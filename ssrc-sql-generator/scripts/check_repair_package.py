"""离线检查寻源修复 SQL 在回复、评论和模板中的一致性。

输入 JSON 包含 sql、comment、template_sql、verified_updates。证据值须先经 Archery
核实；本脚本只核对已提供的值和受限的单表 UPDATE 结构，不代替数据库核查。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


IDENT = r"`?[A-Za-z_][A-Za-z_0-9]*`?"
VALUE = r"(?:[0-9]+|<[^<>]+>)"


def _ident(value: str) -> str:
    return value.replace("`", "").lower()


def _statements(sql: str) -> list[str]:
    # 修复包只接受常规 SQL 注释和语句；复杂语法须人工审阅，不能跳过检查。
    cleaned = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    cleaned = re.sub(r"(?m)^\s*--[^\n]*$", "", cleaned)
    return [part.strip() for part in cleaned.split(";") if part.strip()]


def _parse_update(statement: str) -> dict:
    match = re.fullmatch(
        rf"UPDATE\s+({IDENT})\s+SET\s+(.+?)\s+WHERE\s+(.+)",
        statement, re.I | re.S,
    )
    if not match:
        raise ValueError("仅支持可明确检查的单表 UPDATE ... SET ... WHERE ... 语句")
    table, set_clause, where_clause = match.groups()
    conditions = re.split(r"\s+AND\s+", where_clause.strip(), flags=re.I)
    if len(conditions) != 2:
        raise ValueError(f"{table}: UPDATE WHERE 必须恰好有 tenant_id 和主键两个条件")
    parsed_where = {}
    for condition in conditions:
        item = re.fullmatch(rf"\s*({IDENT})\s*=\s*({VALUE})\s*", condition, re.I)
        if not item:
            raise ValueError(f"{table}: UPDATE WHERE 只允许简单等值条件")
        column = _ident(item.group(1))
        if column in parsed_where:
            raise ValueError(f"{table}: UPDATE WHERE 条件重复")
        parsed_where[column] = item.group(2)
    assignments = {}
    for assignment in set_clause.split(","):
        item = re.fullmatch(rf"\s*({IDENT})\s*=\s*(.+?)\s*", assignment, re.S)
        if not item:
            raise ValueError(f"{table}: SET 字段无法确认")
        column = _ident(item.group(1))
        if column in assignments:
            raise ValueError(f"{table}: SET 字段重复")
        assignments[column] = item.group(2).strip()
    return {"table": _ident(table), "where": parsed_where, "set": assignments}


def _has_select(statements: list[str], table: str, tenant: str, pk: str, value: str) -> bool:
    for statement in statements:
        if not re.match(r"^SELECT\b", statement, re.I):
            continue
        if not re.search(rf"\bFROM\s+`?{re.escape(table)}`?\b", statement, re.I):
            continue
        tenant_match = re.search(rf"\btenant_id\s*=\s*{re.escape(tenant)}(?=\s|$|\))", statement, re.I)
        pk_match = re.search(rf"\b{re.escape(pk)}\s*=\s*{re.escape(value)}(?=\s|$|\))", statement, re.I)
        if tenant_match and pk_match:
            return True
    return False


def validate(package: dict) -> None:
    sql = package["sql"].strip()
    comment = package["comment"]
    template_sql = package["template_sql"].strip()
    if not sql or sql != template_sql:
        raise ValueError("最终 SQL 与模板 sql_text 必须逐字一致")
    blocks = re.findall(r"(?ms)^```sql\s*\n(.*?)\n```\s*$", comment)
    if len(blocks) != 1 or blocks[0].strip() != sql:
        raise ValueError("评论必须包含且只包含一份与最终 SQL 一致的完整 sql 代码块")
    statements = _statements(sql)
    updates = [(index, _parse_update(statement)) for index, statement in enumerate(statements)
               if re.match(r"^UPDATE\b", statement, re.I)]
    evidence = package["verified_updates"]
    if not updates or len(updates) != len(evidence):
        raise ValueError("UPDATE 数量与已核实目标行数量不一致")
    for (index, update), row in zip(updates, evidence):
        table = _ident(row["table"])
        pk = _ident(row["primary_key"])
        tenant = str(row["tenant_id"])
        value = str(row["primary_key_value"])
        if update["table"] != table or update["where"] != {"tenant_id": tenant, pk: value}:
            raise ValueError(f"{table}: UPDATE WHERE 与已核实 tenant_id/主键不一致")
        expected_set = {_ident(key): str(val) for key, val in row["set"].items()}
        if update["set"] != expected_set:
            raise ValueError(f"{table}: SET 字段或值与已核实目标不一致")
        if not _has_select(statements[:index], table, tenant, pk, value):
            raise ValueError(f"{table}: UPDATE 前缺少对应 tenant_id/主键的预查 SELECT")
        if not _has_select(statements[index + 1:], table, tenant, pk, value):
            raise ValueError(f"{table}: UPDATE 后缺少对应 tenant_id/主键的核验 SELECT")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="待检查的 JSON 修复包")
    args = parser.parse_args()
    try:
        validate(json.loads(args.package.read_text(encoding="utf-8")))
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"检查未通过: {exc}\n")
    print("检查通过：SQL 正文一致，预查/更新/核验齐全，UPDATE WHERE 和赋值匹配已提供证据。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
