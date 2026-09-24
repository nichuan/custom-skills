"""寻源 SQL 模板验收样例：关联查询可多条件，UPDATE 只能按租户和主键。"""

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_repair_package.py"
spec = importlib.util.spec_from_file_location("check_repair_package", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def package(sql=None):
    sql = sql or """SELECT quote_id FROM ssrc_rfx_quote
WHERE tenant_id = 39783 AND rfx_header_id = 7233742 AND round_number = 1 AND supplier_id = 88;
SELECT quote_id, invalid_flag, object_version_number, rfx_header_id FROM ssrc_rfx_quote
WHERE tenant_id = 39783 AND quote_id = 901;
UPDATE ssrc_rfx_quote SET invalid_flag = 'N'
WHERE tenant_id = 39783 AND quote_id = 901;
SELECT quote_id, invalid_flag FROM ssrc_rfx_quote
WHERE tenant_id = 39783 AND quote_id = 901;"""
    return {
        "sql": sql,
        "comment": "## 修复 SQL\n\n```sql\n" + sql + "\n```",
        "template_sql": sql,
        "verified_updates": [{
            "table": "ssrc_rfx_quote", "primary_key": "quote_id",
            "tenant_id": "39783", "primary_key_value": "901",
            "set": {"invalid_flag": "'N'"},
        }],
    }


class RepairPackageTest(unittest.TestCase):
    def test_association_query_can_use_extra_conditions(self):
        validator.validate(package())

    def test_update_rejects_association_or_old_value_conditions(self):
        for condition in ("rfx_header_id = 7233742", "round_number = 1",
                          "invalid_flag = 'Y'", "object_version_number = 1"):
            with self.subTest(condition=condition):
                bad = package()
                bad["sql"] = bad["sql"].replace(
                    "WHERE tenant_id = 39783 AND quote_id = 901;\nSELECT quote_id, invalid_flag",
                    f"WHERE tenant_id = 39783 AND quote_id = 901 AND {condition};\nSELECT quote_id, invalid_flag",
                )
                bad["comment"] = "```sql\n" + bad["sql"] + "\n```"
                bad["template_sql"] = bad["sql"]
                with self.assertRaisesRegex(ValueError, "UPDATE WHERE"):
                    validator.validate(bad)

    def test_comment_must_contain_exact_sql(self):
        bad = package()
        bad["comment"] = "## 摘要\n\n将无效标识改为 N。"
        with self.assertRaisesRegex(ValueError, "评论必须包含"):
            validator.validate(bad)

    def test_set_value_must_match_verified_target(self):
        bad = package()
        bad["verified_updates"][0]["set"]["invalid_flag"] = "'Y'"
        with self.assertRaisesRegex(ValueError, "SET 字段或值"):
            validator.validate(bad)


if __name__ == "__main__":
    unittest.main()
