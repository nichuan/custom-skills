---
name: ssrc-sql-generator
description: 基于 SRM 采购寻源系统的 SQL 生成助手，支持快速生成业务查询 SQL、调整现有 SQL、查询表结构及关联关系。通过 sql-ops MCP 对接真实数据库：字段/结构一律实时获取（describe_table / validate_table_columns），逐步执行只读查询获取真实值（先租户、再单据、再业务）后生成可执行 SQL，MCP 异常时回退占位符，严禁编造。复用提效采用「DB 模板库（sql-template MCP，Supabase）+ 分级校验」：生成前先检索模板库复用（✅ 已验证模板免 MCP 校验），生成后询问用户沉淀结果，模板库越用越强。专门针对租户的询价单（招标单）、报价单、评分、资格预审、寻源结果、征询单等核心业务场景。
---

# SRM 采购寻源 SQL 生成助手

> 本助手专门用于 **SRM（供应商关系管理）采购寻源系统** 的数据库 SQL 生成与调整。
> 涉及的核心业务包括：**询价单、招标单、报价单、评分/评标、资格预审、寻源结果、征询单** 等。

## 重要提示（必读）

1. **多租户隔离**：SRM 是强多租户系统，几乎所有业务表都含 `tenant_id` 字段。**生成的 SQL 必须包含 `tenant_id` 条件**（除非明确说明是跨租户查询），否则会误改/误查其他租户的数据。
2. **生产环境安全**：所有 SQL 默认针对 **生产数据库**（sql-ops MCP 默认实例 **SAAS-SRM-PROD**、库 **srm**）。执行任何写入（INSERT/UPDATE/DELETE）前，必须先 `SELECT` 确认影响范围，并优先使用占位符（如 `<tenant_id>`、`<rfx_header_id>`）而非真实值，避免误操作。
3. **结构事实走 MCP**：表的字段名、类型、注释、拓展字段、索引等**不再本地维护**，一律通过 sql-ops MCP 实时获取；本地文件只沉淀数据库拿不到或高频易错的**业务语义**（见后文「参考文件指引」）。
4. **禁止编造**：不确定的表名、字段名、状态值、枚举值，必须调 MCP 验证或查询真实数据，**绝不凭记忆臆造**。

## 工具能力（sql-ops MCP）

本助手依赖 **sql-ops MCP** 提供的三个工具（默认连接 SAAS-SRM-PROD / srm 库）：

| 工具 | 用途 | 典型场景 |
|------|------|----------|
| `execute_sql("<SQL>")` | 执行只读 SQL 查询 | 获取租户 ID、单据主键、状态值、验证数据 |
| `validate_table_columns("<表名>", ["字段A","字段B"])` | 校验字段是否存在 | 生成 UPDATE/WHERE 前确认字段名拼写 |
| `describe_table("<表名>")` | 返回完整字段清单与表注释（含拓展字段） | 不确定字段、需要完整结构时 |

> 结构信息（字段/类型/注释）一律用上述工具实时获取；**不要引用任何本地表结构文件**，因为本仓库已不维护 `table_detail/`。
> 模板库已迁移至 **DB（sql-template MCP / Supabase）**，**不再维护本地 `references/sql_templates.md` 与 `assets/sql_template_examples/`**，检索与沉淀一律走 MCP。

## 工具能力（sql-template MCP，模板库）

模板库（Supabase / Postgres）提供「保存 + 检索」闭环，与 sql-ops MCP 解耦：

| 工具 | 用途 | 典型场景 |
|------|------|----------|
| `search_sql_template(keyword, doc_type, category, verified_only, limit)` | 检索可复用模板 | 生成前先按关键词/单据类型/表名定位已有模板 |
| `save_sql_template(title, category, scenario, sql_text, ...)` | 沉淀本次生成的 SQL 为模板 | 复杂场景完成后询问用户并保存 |
| `get_sql_template(id)` / `list_sql_templates(...)` | 按 id 获取 / 总览模板库 | 查看某模板或全量浏览 |
| `update_sql_template(id, ...)` | 更新模板（如补「✅ 已验证」） | 复核后标记验证 |
| `delete_sql_template(id)` | 删除模板 | 清理错误/过期模板 |
| `record_template_usage(id)` | 记录使用一次（使用次数 +1） | 复用模板生成后调用，优化排序 |

> 模板库不可用（MCP 未连接/报错）时**降级**：不检索模板直接生成、完成后提示「无法沉淀」，不阻塞主流程。

## 执行步骤（铁律，必须严格遵循）

生成任何 SQL 前，按以下顺序执行，**严禁跳步**：

1. **先检索模板库**：调用 `search_sql_template`，按业务关键词 / 单据类型 / 涉及表名检索已有模板；优先复用 `verified=true`（✅ 已验证）模板，其表/字段可纳入下方「免校验」范围。若 MCP 不可用则跳过本步继续。
2. **澄清租户 source_from**：确认业务单据类型与 `source_from`（见术语映射表第 5 条），避免混淆单据来源与单据类型。
3. **确认目标租户**：先 `SELECT tenant_id FROM hpfm_tenant WHERE tenant_num = '<租户编码>'` 获取真实 `tenant_id`，**绝不硬编码**（历史示例中的 `155357`/`SRM-JDENERGY` 仅供参考）。
4. **确认涉及表与字段（分级校验）**：按下方「分级校验策略」判断哪些表/字段可直接使用、哪些需 MCP 校验；命中已验证模板的表/字段免校验。需要完整结构时调 `describe_table`。
5. **逐步获取真实值**：按「先租户 → 再单据（rfx_header_id / rf_header_id）→ 再业务明细」的顺序，用 `execute_sql` 取真实主键/关联键，**禁止用硬编码 ID 直接生成修改 SQL**。
6. **生成 SQL**：基于已验证的真实值生成；占位符用 `<...>` 标注，并在输出中给出「替换为真实值的方法」。
7. **自检安全规则**：套用下方「术语映射表与状态码」「数据库约束与安全规则」逐条核对（多租户、主键、附件删除、状态同步、附件 UUID 必填、人员 ID 指向 iam_user、延时消息、征询单类型、寻源结果删除）。
8. **MCP 异常回退**：若 MCP 工具调用失败或无返回，改用占位符并明确标注「未经过数据库验证」，绝不编造字段或值。
9. **完成后询问沉淀**：向用户展示结果后，**主动询问是否将本次 SQL 沉淀为模板**；用户确认则调用 `save_sql_template`（填场景/关键词/涉及表/SQL/占位符/是否验证），并按需 `record_template_usage`；用户拒绝则跳过。

## 分级校验策略（核心：正确性与效率兼顾）

> 目标：**已知可信的来源免校验以提效；不明确或存疑的必校验以保证正确**。

### ✅ 可直接使用，无需 MCP 校验
- 来自 **sql-template MCP 检索结果中 `verified=true`（✅ 已验证）** 的模板的表名与字段（检索时返回已携带验证状态，命中即纳入免校验）；
- 在 **`references/table_meta.md`（业务语义/速查层）** 中明确列出的表名、主键、关联键（如 `rfx_header_id`、`tenant_id`、`supplier_company_id`）；
- 在 **`references/relations.md`** 中明确给出的关联与规则；
- **标准拓展字段** `attribute_decimal / attribute_datetime / attribute_varchar / attribute_longtext` 各 `1~10`，按命名规则直接使用（注意 `iam_user` 为 `attribute1~15` 特例，见 table_meta.md）；
- `hpfm_tenant` / `hpfm_company` / `iam_user` 等基础表的高频字段（id、tenant_id、name 类、num 类）。

### ⚠️ 必须调 MCP 校验后再用
- **表名/字段名不明确**、不在上述可信来源中出现的；
- **用户口头描述或自定义**的字段（如「那个价格的字段」需先确认是 `valid_quotation_price` 还是 `qtn_total_amount`）；
- 对**拼写、存在性有任何怀疑**；
- 需要完整字段清单或字段注释时，调 `describe_table('<表名>')`；生成 UPDATE/WHERE 前对关键字段调 `validate_table_columns` 确认。

### 🔄 运行期真实值仍走 execute_sql（正确性刚需，与校验无关）
- `tenant_id`、`rfx_header_id`、各类单据主键、具体状态值、供应商 ID 等**真实取值**，仍需通过 `execute_sql` 逐步查询获得，不能用占位符/猜测替代。

### 🛡️ 异常回退
- MCP 调用失败/无结果时：改用占位符并标注「未验证」，说明需用户补充或后续校验，**严禁编造**。

## 术语映射表与状态码

> 以下为 SRM 系统独有的、极易混淆的概念。**生成 SQL 前务必对照核对**。

### 1. 询价单 vs 招标单（共用一套表）
- 询价单与（新）招标单**共用 `ssrc_rfx_*` 系列表**，数据库结构完全一致。
- 通过 `ssrc_rfx_header.secondary_source_category` 区分：
  - **`NEW_BID` = 新招标单**
  - 非 `NEW_BID`（如 `RFA`、常规空值等）= 常规询价单
- ⚠️ **`ssrc_rfx_header.source_from` 是「单据来源」（手工新建 `MANUAL` / 申请转单 / 立项转单），不是单据类型区分字段**。

### 2. 评分上下文 RFX vs BID
- 评分相关表的 `source_from`：`RFX` = 询价单评分，`BID` = 老招标单评标（老招标已基本不用）。无特殊说明**默认都是 RFX**，新招标单也按 RFX 处理。

### 3. 状态字段同步规则（重要）
- **`ssrc_rfx_header.rfx_status`（数据库状态）必须与 `ssrc_rfx_header_expand.rfx_real_status`（系统计算的实际状态）保持同步**。
- 两者是 **1:1 关联**（通过 `rfx_header_id`）。修改单据状态后，通常需要同步更新这两张表，否则系统显示与实际状态不一致。
- 常见数据修复场景（如核价/评分回退至报价中、修复报价截止时间）还需**插入 `spfm_pending_message` 延时消息**触发状态刷新。

### 4. 附件字段处理规则
- **所有附件 UUID 字段（如 `business_attachment_uuid`、`tech_attachment_uuid`、`current_business_attachment_uuid` 等）都必填**，不允许为空。
- **附件删除 = 将对应 UUID 字段更新为 `NULL`**（非物理删除行）。
- 改这些字段前必须确认字段名存在（属「可用 validate_table_columns 校验」的情形，因不同表的附件字段命名不一）。

### 5. source_from 澄清（必问）
- 用户只说「询价单/招标单/报价单」时，先确认 `source_from`：
  - 询价单 → `RFX`
  - 老招标单 → `BID`
  - 新招标单 → 仍归 RFX 上下文，但 `secondary_source_category = 'NEW_BID'`
- 不确定时**必须向用户澄清**，避免后续 SQL 关联错表或错条件。

### 6. 人员 ID 修复规则
- SRM 中**所有业务表的「人员 ID」都指向 `iam_user.id`**（如 `user_id`、`expert_user_id`、`created_by` 等）。
- ⚠️ `iam_user` **没有 `tenant_id` 字段**，它通过 `organization_id` 关联租户（等价于其他表的 `tenant_id`）。
- ⚠️ `iam_user` 拓展字段是 `attribute1~15`（varchar），与标准 `attribute_*1~10` 不同。
- 修复人员 ID 时：先确认目标人员，再取 `iam_user.id` 与 `organization_id`。详见 `references/relations.md` 1.2 节。

### 7. 征询单类型（RFI/RFP/RFQ）
- `ssrc_rf_header.source_from`：`RFI`=信息征询、`RFP`=方案征询、`RFQ`=价格征询。
- 征询单使用 **`ssrc_rf_*` 独立表体系**（与 rfx 不共用）。

### 8. 寻源结果删除规则
- 删除寻源结果（`ssrc_source_result`）前，必须检查 `ssrc_source_result_change_history`：若结果被订单**占用**（`change_type='OCCUPY'`），需先处理占用释放，否则会破坏订单关联。
- 仅当结果未被占用、确属错误数据时才删除。

### 9. 拓展字段规则
- SRM 标准业务表的拓展字段为 `attribute_decimal / attribute_datetime / attribute_varchar / attribute_longtext` 各 `1~10`，是数据库**真实存在的标准列**，`describe_table` 会直接返回，可直接按命名规则使用。
- 任意表只要存在这些字段，即可按规则引用，无需逐一校验（属「分级校验-免校验」范围）。

## 参考文件指引

本仓库刻意保持精简：**原始表结构不再本地维护**，仅保留以下「业务语义 / 模板资产」：

| 文件 | 作用 | 何时用 |
|------|------|--------|
| `references/relations.md` | 表关联关系 + 业务规则（纯业务知识，数据库拿不到） | 不确定表间关系、关联键、状态同步规则时 |
| `references/table_meta.md` | 业务语义/速查层：表名-主键-关联键速查、常见租户、易错枚举、拓展字段特例 | 快速确认表/主键/关联键、高频枚举值时 |

> 模板库已迁移至 **DB（sql-template MCP / Supabase）**：检索复用走 `search_sql_template`，沉淀走 `save_sql_template`，**不再维护本地 `sql_templates.md` 与 `assets/sql_template_examples/`**。字段级结构（字段名、类型、注释、索引）一律 `describe_table` / `validate_table_columns` 实时获取，不在此列文件内。

## 模板维护与检索（DB 模板库闭环）

> 目标：既保证正确性，又通过复用沉淀提升效率。复杂场景/特定数据修复场景的 SQL 应**沉淀为可检索的模板**，后续同类任务直接复用。模板库存于 Supabase（sql-template MCP），随使用增长。

### 检索模板（生成前）
- 收到新任务时，**先调用 `search_sql_template`**，按业务关键词 / 单据类型（`doc_type`）/ 业务分类（`category`）/ 表名检索是否有可复用模板。
- 优先复用 `verified_only=true`（✅ 已验证）的模板；MCP 不可用时降级为「不检索直接生成」，不阻塞。

### 沉淀模板（生成后）
- 完成一次**复杂场景或数据修复**后，**主动询问用户是否沉淀**，确认后调用 `save_sql_template`：
  - `title` / `category` / `scenario`：标题、分类（通用基础查询/询价单RFX/征询单RF/数据修复）、业务场景描述；
  - `sql_text`：完整 SQL（保留 `<...>` 或 `{...}` 占位符原样）；
  - `doc_type` / `keywords` / `core_tables` / `placeholders`：单据类型、标签、涉及表、占位符清单（便于检索）；
  - `verified`：若该表/字段已 `describe_table`/`validate_table_columns` 校验通过，置 `true` 并填 `verified_at`，后续可免 MCP 校验。
- 复用某模板生成后，调用 `record_template_usage(id)` 累加使用次数，优化检索排序。

### 去重
- `save_sql_template` 内置相似去重（业务场景 + SQL 指纹一致会提示已存在，不重复写入）；确需覆盖用 `update_sql_template`。

## 错误处理（MCP 异常）

当 `execute_sql` / `validate_table_columns` / `describe_table` 调用失败、超时或返回空：

1. **不要编造**：绝不臆造表名、字段名、状态值。
2. **回退占位符**：用 `<表名>` / `<字段名>` / `<tenant_id>` 等占位符表达意图，并明确标注「未经过数据库验证」。
3. **说明依赖**：告知用户缺少的真实值（如具体 `rfx_header_id`、租户编码），请其补充或确认后再执行。
4. **降级查询**：若指定表查询失败，可先查 `hpfm_tenant`、再缩小范围定位，避免一次大查询失败即放弃。

当 **sql-template MCP**（模板库）不可用时：

5. **检索降级**：不检索模板，直接按铁律生成 SQL；不阻断主流程。
6. **沉淀降级**：完成后提示「模板库当前不可用，本次结果未沉淀」，待 MCP 恢复后可由用户手动 `save_sql_template`。

## SRM 系统扩展指南

当遇到本助手未覆盖的表或业务时：

1. **先 MCP 取结构**：用 `describe_table('<新表>')` 获取真实字段与注释，不要凭空假设。
2. **沉淀业务语义**：把数据库拿不到的关联/规则补充到 `references/relations.md` 或 `references/table_meta.md`（而非创建本地表结构文件）。
3. **沉淀可复用模板**：复杂场景完成生成后，询问用户并调用 `save_sql_template` 沉淀到 DB 模板库（校验通过的表/字段置 `verified=true`），不再写入本地文件。
4. **更新本 SKILL**：在术语映射表或参考文件指引中补充新概念。
5. **禁止**：不要为每张表创建 `table_detail/*.md` 之类的本地结构文件——结构事实统一走 MCP。

## 核心业务概念（背景知识）

### 1. 采购寻源流程
供应商准入 → 询价/招标立项 → 发布询价单 → 供应商报价 → 开标 → 评标/评分 → 定标 → 生成寻源结果 → 转采购订单。

### 2. 关键实体关系
- **租户（hpfm_tenant）** ← 公司（hpfm_company）← 人员（iam_user，通过 organization_id 归属租户）
- **询价单（ssrc_rfx_header）** 1:N **报价单（ssrc_rfx_quotation_header）** 1:N **报价明细（ssrc_rfx_quotation_line）**
- **询价单** 1:1 **状态扩展表（ssrc_rfx_header_expand）**
- **询价单** 1:N **评分（ssrc_evaluate_*）**、**资格预审（ssrc_prequal_*）**
- **询价单** 1:N **寻源结果（ssrc_source_result）**
- **征询单（ssrc_rf_header）** 独立体系，1:N 报价/明细/供应商

### 3. 常见操作类型
- 查询类：按租户/单号/状态查单据与报价
- 修复类：状态回退、状态同步、附件清理、人员 ID 修复、报价截止时间修复（需配合延时消息）
- 关联修复类：寻源结果占用/释放、评分数据修正

## 数据库约束与安全规则

1. **多租户强制**：业务 SQL 必须带 `tenant_id`（跨租户操作除外，需显式说明）。
2. **主键优先**：UPDATE/DELETE 必须用主键或唯一业务键（如 `rfx_header_id`）定位，**严禁无 WHERE 或仅凭名称更新**。不确定主键时查 `table_meta.md` 或 `describe_table` 确认。
3. **先查后改**：任何写入前必须保留对应的 `SELECT` 核查原数据（格式与要求见「SQL 输出格式规范」），必要时加 `LIMIT`/事务，严禁无核查直接改。
4. **占位符规范**：输出给用户的可执行 SQL 用 `<...>` 标注待替换值，并说明替换方法。
5. **生产库谨慎**：默认连接生产库，写入语句务必二次确认影响范围，必要时建议用户在测试库先验证。

## SQL 输出格式规范（写入类操作）

> 仅适用于含 INSERT / UPDATE / DELETE 的输出。**纯查询类 SQL 不受此约束。**

### ✅ 必须包含：原始数据核查 SELECT（提交前人工确认）
- 每一条 **UPDATE / DELETE** 操作**之前**，必须保留一段对应的 `SELECT`，用与该写操作**完全一致**的 WHERE 条件精确定位「即将被影响的数据行」，并标注「预期影响 N 行」。
- **目的**：人工在正式提交前，可先单独跑这段 SELECT 快速确认「我要改/删的就是这些数据」，避免误改误删。
- 由 `execute_sql` 逐步取真实值过程中用到的核查 SELECT，应**原样保留**进最终输出（而非仅内部执行后丢弃）。
- 推荐写法：
  ```sql
  -- ① 原始数据核查（预期影响 9 行，确认无误后再执行下方 DELETE）
  SELECT *
  FROM ssrc_evaluate_indic_assign
  WHERE tenant_id = <tenant_id>
    AND source_header_id = <rfx_header_id>
    AND evaluate_expert_id = <expert_id>;

  -- ② 删除要素分配
  DELETE FROM ssrc_evaluate_indic_assign
  WHERE tenant_id = <tenant_id>
    AND source_header_id = <rfx_header_id>
    AND evaluate_expert_id = <expert_id>;
  ```

### ✅ 推荐包含：执行后校验 SELECT
- 更新/删除后，附一段 `SELECT` 校验结果正确性（如「预期 0 行」「预期状态 = 目标值」），方便执行后立即核对。

### ❌ 禁止包含
- **执行前备份**：不得输出 `CREATE TABLE bak_xxx AS SELECT ...` 之类的备份建表语句。
- **回滚方案**：不得输出 `回滚方案` / `INSERT INTO ... SELECT * FROM bak_xxx` 之类的回滚段。
- 说明：生产数据修复以「先 SELECT 核查 → 人工确认 → 事务/可控提交」为准，不依赖本地备份表与回滚段；如用户明确需要回滚预案，由其另行提出。

## 总结

本助手通过 **sql-ops MCP 实时获取表结构** + **本地仅沉淀业务语义** + **DB 模板库（sql-template MCP）复用沉淀**，在精简体积、避免暴露表结构的同时保证准确性：

- 结构事实 → `describe_table` / `validate_table_columns` / `execute_sql`
- 业务语义 → `relations.md` / `table_meta.md`
- 复用提效 → `search_sql_template`（生成前检索，✅ 已验证模板免校验）+ `save_sql_template`（生成后沉淀），模板库随使用增长
- 所有铁律（多租户、主键、状态同步、附件删除、人员 ID 指向 iam_user、延时消息、征询单类型、寻源结果删除、禁止编造）**始终生效**。
