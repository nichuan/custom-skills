# SRM SQL Generator Skill

## 概述

本 Skill 是专门为 SRM（Supplier Relationship Management）采购寻源系统设计的 SQL 生成助手。采用 **「本地仅沉淀业务语义、结构事实走 MCP」** 的分层设计：表的字段/结构通过 **sql-ops MCP** 实时获取，本地只保留数据库拿不到或高频易错的业务知识，并通过 **模板库 + 分级校验** 兼顾正确性与处理效率。

> **重要**：本 Skill 同时覆盖询价单（RFX 开头）和新招标单（BID 开头）两种寻源场景，两者共用同一套 `ssrc_rfx_*` 数据库表。区分字段是 `ssrc_rfx_header.secondary_source_category`（新招标单 = `'NEW_BID'`），评标/结果等关联表中两者**共用同一 `source_from = 'RFX'` 上下文**（新招标不再使用 `'BID'`，`'BID'` 仅指几乎不用的老招标），仅前端术语叫法不同（如"待定标"="待核价"、"评标"="评分"等）。

## 核心特性

### 1. 结构事实走 MCP（替代本地表结构文件）
- 表的字段名、类型、注释、拓展字段、索引等**不再本地维护**，一律通过 sql-ops MCP 实时获取：
  - `describe_table('<表名>')` 取完整字段
  - `validate_table_columns('<表名>', ['字段'])` 校验字段存在性
  - `execute_sql('<SQL>')` 取真实值（租户ID、单据主键、状态值等）
- 仓库不再包含 `table_detail/` 这类暴露表结构的大文件，更精简、更安全。

### 2. 业务语义分层（本地只沉淀拿不到的知识）
- `table_meta.md`：表名-主键-关联键速查 + 常见租户 + 易错枚举（数据库拿不到或高频易错）。
- `relations.md`：表关联与业务规则（纯业务知识）。
- 模板库已迁移至 **DB（sql-template MCP / Supabase）**：检索复用与沉淀走 MCP，不再本地维护（详见下方「模板库 + 分级校验」）。

### 3. 模板库 + 分级校验（正确性与效率兼顾）
- 模板库存于 **Supabase（sql-template MCP）**，提供 `search_sql_template`（生成前检索复用）与 `save_sql_template`（生成后沉淀）闭环。
- 模板随使用增长，越用越强；「✅ 已验证」模板（`verified=true`）的表字段免 MCP 校验以提效（详见 `SKILL.md` 分级校验策略）。

### 4. 维护成本低、可持续沉淀
- 新场景完成即沉淀为模板/示例，后续同类任务快速复用。
- 业务规则变化只需更新 `relations.md` / `table_meta.md`，无需维护逐表结构文件。

## 目录结构

```
ssrc-sql-generator/
├── SKILL.md                              # Skill 入口文件（必填）
├── README.md                             # 本文件
├── skill.json                            # Skill 配置文件
├── references/                           # SRM 系统参考文档（仅业务语义层）
│   ├── table_meta.md                     # 业务语义/速查层（表名-主键-关联键、常见租户、易错枚举）
│   ├── relations.md                      # 表关联关系与业务规则
│   └── sql_templates.md                  # SQL 模板库（含场景检索速查表 + 状态值附录）
└── assets/                               # 资源文件目录
    └── sql_template_examples/            # 复杂/数据修复场景完整 SQL 示例（可增长）
        └── rfx_rollback_to_quotation.sql # 示例：询价单回退至报价中（状态同步 + 延时消息）
```

> 表结构由 sql-ops MCP 实时提供，**`references/` 下不再有单表结构文件**。

## 快速开始

### 基本使用

本 Skill 专门处理 SRM 采购寻源系统的 SQL 需求，当用户提出以下需求时自动触发：

1. **询价单/招标单查询**："租户 SRM-AUX 查询询价单"、"查询招标单 BID2026070100001 的投标情况"
2. **报价单/投标单分析**："生成 SRM-AUX 租户近 7 天的报价统计"
3. **关联关系查询**："列出询价单表和报价单表的关联关系"
4. **数据修复**："修复报价单状态不一致的数据"、"将招标单修复为待定标状态"
5. **评分/评标统计**："统计专家评分情况和排名"
6. **寻源结果查询**："查询 XX 询价单的寻源结果"、"查询 XX 招标单的中标结果"

### 工作流程

1. **识别涉及的表**：从用户需求中提取表名，对照 `table_meta.md` 确认表与关联键。
2. **实时获取结构（MCP）**：对不明确的表/字段调 `describe_table` / `validate_table_columns` 确认。
3. **补充关联关系**：参考 `relations.md` 确认关联键与业务规则。
4. **检索复用模板**：先查 `sql_templates.md` 顶部「场景检索速查表」，复杂修复查 `assets/sql_template_examples/`。
5. **分级校验**：按 `SKILL.md` 分级校验策略，已验证内容免校验、不明确必校验。
6. **逐步取真实值并执行**：用 `execute_sql` 先租户→再单据→再业务明细，确认影响范围后生成 SQL。

## 核心文件说明

### SKILL.md
Skill 入口文件，定义：
- Skill 基本信息（name、description）
- 执行步骤（铁律）+ **分级校验策略**（正确性与效率兼顾）
- 术语映射表与状态码（易混淆概念）
- 参考文件指引 + **模板维护与检索**章节
- 错误处理（MCP 异常回退）、扩展指南

### references/table_meta.md
业务语义 / 速查层（**非**字段结构）：
- 表名（按业务模块分类）、主键、关联键
- 常见参考租户、易错枚举（team / rfx_role / source_from 等）
- 拓展字段特例（如 `iam_user` 的 `attribute1~15`）

### references/relations.md
表之间的关联关系与业务规则：
- 关联类型（1:1、1:N）
- 关联键与 SQL 关联示例
- 状态同步、人员 ID 指向、延时消息等业务规则

### references/sql_templates.md
模板库：
- 顶部 **场景检索速查表**：按业务关键词/单据类型快速定位模板编号
- 通用基础、询价单/招标单、征询单三类模板 + 数据修复模板
- 附录：常用状态值参考
- 「✅ 已验证」标记约定（用于启用免校验）

### assets/sql_template_examples/[场景名].sql
复杂 / 特定数据修复场景的**完整可执行 SQL 示例**入口：
- 文件头注释含：场景说明、涉及表、关键关联、占位符清单、已验证标记
- 命名规范：`<场景>.sql`（如 `rfx_rollback_to_quotation.sql`）
- 随业务增长持续沉淀，是可检索复用的正式资产

## 扩展指南

### 新增业务知识（关联/规则）
1. 在 `relations.md` 或 `table_meta.md` 中补充，无需创建逐表结构文件。
2. 结构信息一律用 MCP 获取，不要本地维护表字段。

### 新增 SQL 模板
1. 通用/中等复杂度 → 写入 `sql_templates.md`（含业务场景说明 + 占位符 SQL）。
2. 复杂/特定修复 → 新增 `assets/sql_template_examples/<场景>.sql`。

### 标记「已验证」
首次生成并经 `describe_table` / `validate_table_columns` 校验通过后，在模板/示例内标注「✅ 已验证」+ 日期，后续同类任务即可免校验提效。若结构可能已变更，重新校验或去掉标记。

## 使用示例

### 示例1：查询租户 SRM-AUX 的询价单

**用户请求**："生成查询租户 SRM-AUX 询价单的 SQL，统计最近 7 天的数据"

**Skill 处理**：
1. 从 `table_meta.md` 识别涉及表：`hpfm_tenant`、`ssrc_rfx_header`
2. 用 MCP `execute_sql` 取 `tenant_id`：`SELECT tenant_id FROM hpfm_tenant WHERE tenant_num='SRM-AUX'`
3. 从 `relations.md` 确认关联：`hpfm_tenant.tenant_id` ↔ `ssrc_rfx_header.tenant_id`
4. 从 `sql_templates.md` 匹配时间过滤模板
5. 生成 SQL：

```sql
SELECT
    t.tenant_num,
    r.rfx_num,
    r.rfx_status,
    r.rfx_title,
    r.quotation_start_date,
    r.quotation_end_date,
    r.create_time
FROM hpfm_tenant t
INNER JOIN ssrc_rfx_header r ON t.tenant_id = r.tenant_id
WHERE t.tenant_num = 'SRM-AUX'
  AND r.create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY r.create_time DESC;
```

### 示例2：报价单与询价单关联分析

**用户请求**："查询 SRM-AUX 租户询价单对应的报价情况"

**Skill 处理**：
1. 从 `table_meta.md` 识别涉及表：`ssrc_rfx_header`、`ssrc_rfx_quotation_header`、`ssrc_rfx_line_supplier`
2. 用 `describe_table` 确认字段（如有不明确）
3. 从 `relations.md` 确认关联键
4. 生成关联查询 SQL

### 示例3：查询 SRM 表关联关系

**用户请求**："列出询价单表和报价单表的关联关系"

**Skill 处理**：
1. 从 `relations.md` 查找 `ssrc_rfx_header` 和 `ssrc_rfx_quotation_header` 的关联
2. 输出业务关联关系（见上）

## 最佳实践

### SQL 生成规则
- 必须先确认表关联键的正确性（参考 `relations.md`）
- 使用明确的表别名避免字段歧义
- 时间范围过滤优先使用 `sql_templates.md` 中的模板
- 聚合统计时明确 GROUP BY 字段和聚合函数
- 生成的 SQL 必须包含关键注释说明
- ⚠️ 新招标单（BID）查询与询价单完全共用：评标/结果表 `source_from` 仍为 `'RFX'`（不要写成 `'BID'`），单据类型区分用 `ssrc_rfx_header.secondary_source_category = 'NEW_BID'`
- ⚠️ **写入类 SQL 输出规范**（详见 `SKILL.md`「SQL 输出格式规范」）：每条 UPDATE/DELETE 之前必须保留一段用一致 WHERE 条件的「原始数据核查 SELECT」，供提交前人工确认；**禁止输出**「执行前备份」(`CREATE TABLE bak_...`) 与「回滚方案」段。

### 结构获取规则（替代原"上下文加载规则"）
- 结构事实统一走 MCP：`describe_table` / `validate_table_columns` / `execute_sql`
- 不维护本地单表结构文件，避免上下文臃肿与表信息暴露
- 字段名/表名不明确时必校验，已验证模板中的内容可免校验

### 准确性保障
- 生成 SQL 前必须验证：
  - 表名拼写（对照 `table_meta.md` 或 `describe_table`）
  - 关联键（对照 `relations.md`）
  - 字段存在性（`validate_table_columns` 或 `describe_table`）
  - ⚠️ **source_from 是否正确**：评标/结果表中 `'RFX'` 同时覆盖询价单与新招标（新招标不再用 `'BID'`），`'BID'` 仅指几乎不用的老招标；征询单用 `'RFI'`/`'RFP'`。另：`ssrc_rfx_header.source_from` 是单据来源，区分单据类型用 `secondary_source_category`
- 对于复杂逻辑，建议分步生成并验证

## 维护建议

### 定期更新
- 定期检查 `table_meta.md` / `relations.md` 中的业务规则是否仍准确
- 模板/示例随业务演进补充「✅ 已验证」状态

### 优化建议
- 若某类 SQL 频繁出错，补充模板到 `sql_templates.md` 或 `assets/sql_template_examples/`
- 若用户常问某些关联，补充到 `relations.md`
- 保持本地文件精简：结构事实一律走 MCP

## 版本历史

### v1.6.0
- **SQL 输出格式规范（写入类操作）**：新增专章，明确 UPDATE/DELETE 类输出的格式要求
  - ✅ 每条 UPDATE/DELETE 之前必须保留用一致 WHERE 条件的「原始数据核查 SELECT」，便于提交前人工跑查询确认数据正确
  - ✅ 推荐保留「执行后校验 SELECT」
  - ❌ 禁止输出「执行前备份」(`CREATE TABLE bak_...`) 与「回滚方案」段，生产修复以「先核查→人工确认→事务可控提交」为准
  - 同步更新「数据库约束与安全规则」第 3 条与 README 最佳实践

### v1.5.0
- **精简**：删除 `references/table_detail/` 全部 41 个本地表结构文件，不再在仓库中暴露表结构与字段信息
- **结构事实走 MCP**：表字段/类型/注释/拓展字段/索引统一通过 sql-ops MCP（`describe_table` / `validate_table_columns` / `execute_sql`）实时获取
- **业务语义分层**：将数据库拿不到或高频易错的知识沉淀到 `table_meta.md`（含常见租户、易错枚举、拓展字段特例）
- **分级校验策略**：已验证模板/示例、table_meta/relations 明确列出的表字段免 MCP 校验提效；表名/字段名不明确时必校验
- **模板维护入口**：`sql_templates.md` 顶部新增「场景检索速查表」；正式确立 `assets/sql_template_examples/` 为复杂/数据修复场景完整 SQL 示例入口（含「✅ 已验证」标记约定），新增首个示例 `rfx_rollback_to_quotation.sql`
- **清理死链**：移除 `columns_202603131733.md`、本地 `table_detail/` 等失效引用
- 同步更新 SKILL.md / README.md / skill.json

### v1.4.0
- 接入 sql-ops MCP（execute_sql / validate_table_columns / describe_table）
- 强化逐步取值、异常回退占位符等规则

### v1.3 (2026-07-09)
- 修正招标单（BID）与询价单（RFX）的区分规则：区分字段为 `ssrc_rfx_header.secondary_source_category`（新招标 = `'NEW_BID'`），而非 `source_from`
- 修正评标/结果表上下文：`source_from = 'RFX'` 同时覆盖询价单与新招标
- 明确 `ssrc_rfx_header.source_from` 是单据来源字段，并非单据类型区分字段

### v1.2 (2026-07-09)
- 新增招标单（BID）与询价单（RFX）共用表体系规则及完整术语映射表

### v1.1 (2026-03-22)
- 优化 SQL 模板格式，统一占位符规范
- 移除不存在的示例文件引用

### v1.0 (2026-03-13)
- 初始版本

## 许可证

本 Skill 采用 MIT 许可证。
