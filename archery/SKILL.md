---
name: archery
description: 只读访问 Archery，负责选择 site/instance/db、查询真实数据与表结构并安全降级。数据修复只生成写 SQL交用户确认，不直接写库。
---

# Archery 数据库查询助手（统一数据访问层）

## 跨流程协作（按需）

跨技能/跨 agent 交接或恢复任务时读取[协作协议](../zhenyun-ops/references/collaboration-contract.md)（未安装时改用 `get_workflow_guide(topic="handoff")`）：复用已验证的环境/租户/证据、可变数据执行前重核、只问真正阻塞的未知、已授权同范围动作不重复确认——完整协作规则以该协议为准。

## 职责边界

本 Skill 是**所有数据库实时访问的唯一入口与规范源**。它回答的是：
- 某个环境/业务应该用哪个 `site` + `instance`？真实实例名是什么？
- 某实例下有哪些库？某个表/业务属于哪个库（跨库怎么写）？
- 怎样调用 `archery_query` / `archery_describe_table` / `archery_list_columns` / `archery_list_databases` / `archery_list_instances` / `archery_query_tenant`？
- 查询失败/异常时如何降级？

它**不生成业务 SQL**（交给 `ssrc-sql-generator` / `spuc-sql-generator`），**不做故障根因分析**（交给 `java-troubleshoot`）。本 Skill 只描述"怎么查、往哪查"。

工具的**真实参数 Schema 以 MCP 运行时为唯一事实源**，严禁在本文件猜测/重复定义。

## 执行效率

- 用户已经明确环境、库和表时直接查询，不先调用 `list_instances`、`list_databases` 或目录发现工具；这些工具只用于真实不确定或返回路由错误时。
- 同一目标环境已由 DDL、list_columns 或成功查询证明的表/字段不重复 describe。模板和表目录只提供候选，不能证明当前结构。多个独立结构检查可并行。
- 能用一条有界、索引友好的 JOIN 同时确认租户、单据和状态时，不拆成多次查询；只有后续 SQL 必须依赖前一步返回值时才串行。
- 相同 `site/instance/db`、`tenant_id`、表结构和已验证结果在本次任务内复用。

---

## 铁律（踩坑总结，必须严格遵守）

### 铁律 1：按目标站点选择实例

- `site` 支持 `cn` / `aws`，工具默认 `cn`；`instance` 省略时使用该站点配置的默认实例（当前 `cn` 默认生产）。只有目标是 AWS 或国内 dev/test/prod-ro 时才需要显式指定站点和实例。
- 显式指定 `instance` 时使用 `archery_list_instances` 返回的别名（`prod`/`prod-ro`/`dev`/`test`/`aws`），不要自行拼真实实例名。真实实例名由 MCP 配置映射。
- AWS 查询必须传 `site="aws", instance="aws"`；只传 `instance="aws"` 会沿用默认 `site="cn"` 并报站点不匹配。

### 铁律 2：环境选择——查询默认 prod，修改必确认

| 用户说 | 传 `site` / `instance` | 真实实例 |
|--------|------------------------|----------|
| 「生产」/ 不提环境 → **仅用于查询** | `cn` / `prod` | `SAAS-SRM-PROD数据库` |
| 「生产只读」/「prod 只读」 | `prod-ro` | `SAAS-SRM-PROD只读数据库` |
| 「测试」/「test」 | `test` | `SAAS-SRM-TEST数据库` |
| 「开发」/「dev」 | `dev` | `SAAS-SRM-DEV数据库` |
| 「aws」/ 海外站点 | `aws` / `aws` | `JP-SaaS-1-Prod-RW-8.0` |

- **查询类**：不提环境可默认 `cn`/`prod`。
- **修改类（数据修复、生产写操作）**：**必须明确目标环境 + 目标租户 + 影响范围（用户或前序已明确则复用，不重复询问）**，不得因「默认 prod」就直接执行/生成。拿不准先问清。
- 用户只要提到**非默认环境**（AWS、dev、test 或 prod-ro），必须显式传 `site`+`instance`，否则会落到默认 cn 生产。

### 铁律 3：库名以实测为准，默认 `srm`，跨库显式带库名

- 默认库 `srm`；跨库查询必须显式传 `db_name`。
- 库名来自用户、可信目录或既有映射时可直接使用；来源不明时以 `archery_list_databases` 实际返回为准，**严禁猜库名**。
- 拿不准实例时调 `archery_list_instances()` 查看全部站点，或传 `site="cn"|"aws"` 只看目标站点；拿不准库时调 `archery_list_databases(site, instance)`。

### 铁律 4：查询/修改分离，Agent 不直接写库

- `archery_query` 仅执行**只读** SQL（单条 SELECT / EXPLAIN SELECT / SHOW CREATE TABLE），SELECT 可使用 `CASE WHEN ... THEN ... ELSE ... END` 表达式和 `IN (...)` / `NOT IN (...)` 值列表。
- 不支持其它 SHOW/DESC、WITH、多语句、注释、子查询、窗口函数、集合运算或任何写入语法；括号只允许白名单无副作用函数及 `IN` 值列表。
- 当前函数白名单仅为 `COUNT`、`SUM`、`AVG`、`MIN`、`MAX`、`IFNULL`、`NULLIF`、`CONCAT`、`CONCAT_WS`、`CAST`；白名单外函数、任意分组括号和嵌套子查询一律拒绝。需要影响行数时优先使用有界 `COUNT(*)`，仍须关注查询条件与数据库权限。
- 表结构/字段请使用专用 `archery_describe_table` / `archery_list_columns`，不要拿 `archery_query` 跑 DDL。
- 任何 INSERT/UPDATE/DELETE 一律由各 SQL 技能**生成 SQL 后交用户人工确认执行**，Agent 不直接执行写操作。

---

## 环境与库参考

常用别名为 `cn/prod`、`cn/prod-ro`、`cn/dev`、`cn/test` 与 `aws/aws`，默认库为 `srm`。只有用户询问完整映射、库清单，或当前任务无法确定路由时，才阅读 [references/environment-routing.md](references/environment-routing.md)；实时结果仍以 `archery_list_instances` / `archery_list_databases` 为准。

跨库 JOIN 必须显式写库名前缀；例如 `slod_*` 位于 `srm_logistics_delivery`。

---

## 工具调用规范

| 工具 | 用途 | 何时调用 |
|------|------|----------|
| `archery_query(sql, site, instance, db)` | 执行只读 SQL，逐步取租户/主键/状态真实值 | 确认真实数据、验证查询条件 |
| `archery_list_columns(table, site, instance, db)` | 列字段名清单 | 生成 UPDATE/WHERE 前核对字段拼写 |
| `archery_describe_table(table, site, instance, db)` | SHOW CREATE TABLE（结构+注释+索引） | 不确定字段/需完整结构时 |
| `archery_list_instances(site?)` | `site` 留空返回全部，传 `cn`/`aws` 只返回该站点 | 拿不准实例名时先调 |
| `archery_list_databases(site, instance)` | 列出某实例下所有库 | 确认 `srm` / `srm_logistics_delivery` 等库名 |
| `archery_query_tenant(tenant, site, instance, db)` | 按租户编码/名称反查 `tenant_id` | 生成 SQL 前确认真实租户，禁止硬编码 |

**示例**：
- 查 dev 采购订单：`archery_query(site="cn", instance="dev", db="srm", sql="<SQL>")`
- 查 aws：`archery_query(site="aws", instance="aws", db="srm", sql="<SQL>")`
- 确认发货工作台库：`archery_list_databases(site="cn", instance="prod")` → 见 `srm_logistics_delivery`

---

## 取数依赖

```
① 确认环境（铁律 2）→ site + instance（aws 必带 site）
② 只补齐未知事实：未知租户才 query_tenant，未知库才 list_databases，未知字段才 describe/list_columns
③ 查询真实值：优先用一条有界 SELECT/JOIN 同时返回租户、单据与业务状态；确有数据依赖时再拆步
④ 生成写 SQL 前，租户过滤、目标主键、字段存在性和当前值必须已有真实证据
```

---

## 降级策略（禁止"失败→相同参数→再调"）

| 返回 | 含义 | 处理 |
|------|------|------|
| 401 / 凭据缺失 | 凭据问题 | 提示检查 `.env` 的 `ARCHERY_*` 配置，不让用户贴密码 |
| 「未关联该实例」 | 只传 instance 没传 site | 补 `site`（aws 实例必带 `site="aws"`） |
| 库不存在 / 表不存在 | db/表名错 | 先 `archery_list_databases` 确认真实库；`archery_describe_table` 探测真实表 |
| query 报语法不支持 | 核对是否用了 WITH/子查询/多语句/写入；CASE 表达式和 IN 值列表受支持，若单独使用时仍被拒绝，说明当前 MCP runtime 可能未更新 | 合法只读语法可直接查询；结构用 describe/list_columns |
| 空结果 | 条件/环境错 | 核对租户、环境、表名；先用 `hpfm_tenant` 缩小范围 |

> **MCP 异常降级**：Archery 任一不可用，不阻塞主流程——跳过对应步骤、用占位符标注真实值缺失、完成后提示能力缺失，**不得假装执行通过**。

---

## 输出规范

- 报告查询时标注 `site/instance/db` 三元组与真实实例名（如 `cn/prod/srm` → SAAS-SRM-PROD数据库）。
- 涉及跨库，明确标注 `db_name` 来源。
- 多租户场景必须显示 `tenant_id` 来源（来自 `archery_query_tenant`，非硬编码）。

---

## 安全检查

- 凭据只由 MCP 从环境变量读取；输出不得展示密码 / Token / AccessKey，必要时写为 `****`。
- 只读取数；不执行写入；写 SQL 生成后交用户人工确认。
