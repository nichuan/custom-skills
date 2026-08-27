---
name: archery
description: Archery 数据库查询助手（统一数据访问层）。仅在用户要「查数据库 / 确认实例与库 / 确认环境 / 用 Archery 取数或看表结构」时使用。集中管理：双站点实例别名与真实名映射、每个环境/实例下有哪些库（如 SAAS-SRM-PROD 的 srm / srm_logistics_delivery 等）、什么场景用哪个 site+instance、archery_query/describe/list_columns/list_databases/list_instances/query_tenant 的调用规范与安全降级。各 SQL 技能（ssrc / spuc）只关心「生成什么 SQL」，查询落到哪里、怎么查一律交给本 Skill。只读取数；写 SQL 由各 SQL 技能生成后交用户人工确认执行。
---

# Archery 数据库查询助手（统一数据访问层）

## 职责边界

本 Skill 是**所有数据库实时访问的唯一入口与规范源**。它回答的是：
- 某个环境/业务应该用哪个 `site` + `instance`？真实实例名是什么？
- 某实例下有哪些库？某个表/业务属于哪个库（跨库怎么写）？
- 怎样调用 `archery_query` / `archery_describe_table` / `archery_list_columns` / `archery_list_databases` / `archery_list_instances` / `archery_query_tenant`？
- 查询失败/异常时如何降级？

它**不生成业务 SQL**（交给 `ssrc-sql-generator` / `spuc-sql-generator`），**不做故障根因分析**（交给 `java-troubleshoot`）。本 Skill 只描述"怎么查、往哪查"。

工具的**真实参数 Schema 以 MCP 运行时为唯一事实源**，严禁在本文件猜测/重复定义。

---

## 铁律（踩坑总结，必须严格遵守）

### 铁律 1：实例必须用别名，site 必传

- `site` 只能是 `cn` / `aws`。
- `instance` **必须用别名**（`prod`/`prod-ro`/`aws`/`dev`/`test`），**严禁直传真实实例名**（如 `SAAS-SRM-PROD数据库`）。真实名由别名自动转换。
- `archery_list_instances` 明确警告：**只传 instance 不传 site 会按默认 `site=cn` 解析而报「未关联该实例」**。因此 `aws` 实例务必带 `site="aws"`。

### 铁律 2：环境选择——查询默认 prod，修改必确认

| 用户说 | 传 `site` / `instance` | 真实实例 |
|--------|------------------------|----------|
| 「生产」/ 不提环境 → **仅用于查询** | `cn` / `prod` | `SAAS-SRM-PROD数据库` |
| 「生产只读」/「prod 只读」 | `prod-ro` | `SAAS-SRM-PROD只读数据库` |
| 「测试」/「test」 | `test` | `SAAS-SRM-TEST数据库` |
| 「开发」/「dev」 | `dev` | `SAAS-SRM-DEV数据库` |
| 「aws」/ 海外站点 | `aws` / `aws` | `JP-SaaS-1-Prod-RW-8.0` |

- **查询类**：不提环境可默认 `cn`/`prod`。
- **修改类（数据修复、生产写操作）**：**必须显式确认目标环境 + 目标租户 + 影响范围**，不得因「默认 prod」就直接执行/生成。拿不准先问清。
- 用户只要提到**非生产环境**，必须显式传 `site`+`instance`，否则会误查/误改生产。

### 铁律 3：库名以实测为准，默认 `srm`，跨库显式带库名

- 默认库 `srm`；跨库查询必须显式传 `db_name`。
- 可用库以 `archery_list_databases` 实际返回为准，**严禁猜库名**。
- 拿不准实例/库时先调 `archery_list_instances(site)` / `archery_list_databases(site, instance)`。

### 铁律 4：查询/修改分离，Agent 不直接写库

- `archery_query` 仅执行**只读** SQL（单条基础 SELECT / EXPLAIN SELECT / SHOW CREATE TABLE）。
- 不支持其它 SHOW/DESC、WITH、多语句、注释、函数/子查询、窗口函数、集合运算或任何写入语法。
- 表结构/字段请使用专用 `archery_describe_table` / `archery_list_columns`，不要拿 `archery_query` 跑 DDL。
- 任何 INSERT/UPDATE/DELETE 一律由各 SQL 技能**生成 SQL 后交用户人工确认执行**，Agent 不直接执行写操作。

---

## 实例与库清单（实测，作为事实基础）

### 实例别名映射（来自 `archery_list_instances`，实时为准）

```
cn:
  prod      -> SAAS-SRM-PROD数据库
  prod-ro   -> SAAS-SRM-PROD只读数据库
  dev       -> SAAS-SRM-DEV数据库
  test      -> SAAS-SRM-TEST数据库
aws:
  aws / aws-prod -> JP-SaaS-1-Prod-RW-8.0
default_site = cn, default_db = srm
```

### 各环境有哪些库（以 `archery_list_databases` 实测为准）

**SAAS-SRM-PROD（cn / prod）实测库列表**：

| 库名 | 用途 / 备注 |
|------|------------|
| `srm` | 主业务库（寻源 ssrc_*、履约 spfm_/sodr_、平台 hpfm_、主数据 smdm_、状态机 siec_ 等） |
| `srm_logistics_delivery` | 发货工作台域（`slod_*` 表，如 `slod_asn_header` 送货/计划/标签） |
| `srm_budget` | 预算相关 |
| `srm_data_application` | 数据应用 |
| `srm_open_platform` | 开放平台 |
| `srm_requisition_plan` | 申购计划 |
| `srm_workbench` | 工作台 |
| `scavenger_prod` | 业务库（具体用途以实际为准） |

> 系统/内部库（一般不查）：`mysql` / `information_schema` / `performance_schema` / `sys` / `apolloconfigdb` / `apolloportaldb` / `test`。

**跨库原则**：当参与 JOIN 的表 `db_name` 不同，必须写成跨库查询（带库前缀，如 `srm_logistics_delivery.slod_asn_header`），不可省略库名。

> 其他环境（dev / test / aws）的库清单**不在此硬编码**，用 `archery_list_databases(site, instance)` 实时获取。

---

## 工具调用规范

| 工具 | 用途 | 何时调用 |
|------|------|----------|
| `archery_query(sql, site, instance, db)` | 执行只读 SQL，逐步取租户/主键/状态真实值 | 确认真实数据、验证查询条件 |
| `archery_list_columns(table, site, instance, db)` | 列字段名清单 | 生成 UPDATE/WHERE 前核对字段拼写 |
| `archery_describe_table(table, site, instance, db)` | SHOW CREATE TABLE（结构+注释+索引） | 不确定字段/需完整结构时 |
| `archery_list_instances(site?)` | 列出可用实例与别名映射 | 拿不准实例名时先调 |
| `archery_list_databases(site, instance)` | 列出某实例下所有库 | 确认 `srm` / `srm_logistics_delivery` 等库名 |
| `archery_query_tenant(tenant, site, instance, db)` | 按租户编码/名称反查 `tenant_id` | 生成 SQL 前确认真实租户，禁止硬编码 |

**示例**：
- 查 dev 采购订单：`archery_query(site="cn", instance="dev", db="srm", sql="<SQL>")`
- 查 aws：`archery_query(site="aws", instance="aws", db="srm", sql="<SQL>")`
- 确认发货工作台库：`archery_list_databases(site="cn", instance="prod")` → 见 `srm_logistics_delivery`

---

## 取数顺序（真实值逐步获取）

```
① 确认环境（铁律 2）→ site + instance（aws 必带 site）
② 确认租户：archery_query_tenant → 真实 tenant_id（禁止硬编码）
③ 确认库：库非默认 srm 时显式 db_name；拿不准先 archery_list_databases
④ 确认字段：archery_describe_table / archery_list_columns（生成写 SQL 前必做）
⑤ 查询真实值：archery_query —— 先租户 → 再单据 → 再业务
```

---

## 降级策略（禁止"失败→相同参数→再调"）

| 返回 | 含义 | 处理 |
|------|------|------|
| 401 / 凭据缺失 | 凭据问题 | 提示检查 `.env` 的 `ARCHERY_*` 配置，不让用户贴密码 |
| 「未关联该实例」 | 只传 instance 没传 site | 补 `site`（aws 实例必带 `site="aws"`） |
| 库不存在 / 表不存在 | db/表名错 | 先 `archery_list_databases` 确认真实库；`archery_describe_table` 探测真实表 |
| query 报语法不支持 | 用了 WITH/子查询/多语句/写入 | 改写为基础 SELECT；结构用 describe/list_columns |
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
