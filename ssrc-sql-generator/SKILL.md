---
name: ssrc-sql-generator
description: 基于 SRM 采购寻源系统的 SQL 生成助手，支持快速生成业务查询 SQL、调整现有 SQL、查询表结构及关联关系。通过 sql-ops MCP 对接真实数据库：字段/结构一律实时获取（describe_table / validate_table_columns），逐步执行只读查询获取真实值（先租户、再单据、再业务）后生成可执行 SQL，MCP 异常时回退占位符，严禁编造。采用「本地仅沉淀业务语义、结构事实走 MCP」的分层设计，并通过「模板库 + 分级校验」兼顾正确性与处理效率。专门针对租户的询价单（招标单）、报价单、评分、资格预审、寻源结果、征询单等核心业务场景。
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

## 执行步骤（铁律，必须严格遵循）

生成任何 SQL 前，按以下顺序执行，**严禁跳步**：

1. **澄清租户 source_from**：确认业务单据类型与 `source_from`（见术语映射表第 5 条），避免混淆单据来源与单据类型。
2. **确认目标租户**：先 `SELECT tenant_id FROM hpfm_tenant WHERE tenant_num = '<租户编码>'` 获取真实 `tenant_id`，**绝不硬编码**（历史示例中的 `155357`/`SRM-JDENERGY` 仅供参考）。
3. **确认涉及表与字段（分级校验）**：按下方「分级校验策略」判断哪些表/字段可直接使用、哪些需 MCP 校验。需要完整结构时调 `describe_table`。
4. **逐步获取真实值**：按「先租户 → 再单据（rfx_header_id / rf_header_id）→ 再业务明细」的顺序，用 `execute_sql` 取真实主键/关联键，**禁止用硬编码 ID 直接生成修改 SQL**。
5. **生成 SQL**：基于已验证的真实值生成；占位符用 `<...>` 标注，并在输出中给出「替换为真实值的方法」。
6. **自检安全规则**：套用下方「术语映射表与状态码」「数据库约束与安全规则」逐条核对（多租户、主键、附件删除、状态同步、附件 UUID 必填、人员 ID 指向 iam_user、延时消息、征询单类型、寻源结果删除）。
7. **MCP 异常回退**：若 MCP 工具调用失败或无返回，改用占位符并明确标注「未经过数据库验证」，绝不编造字段或值。

## 分级校验策略（核心：正确性与效率兼顾）

> 目标：**已知可信的来源免校验以提效；不明确或存疑的必校验以保证正确**。

### ✅ 可直接使用，无需 MCP 校验
- 来自 **`references/sql_templates.md` 或 `assets/sql_template_examples/` 中已标注「✅ 已验证」** 的模板/示例的表名与字段；
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
| `references/sql_templates.md` | **模板库（快速维护入口）**：含业务场景说明 + SQL + 状态值附录，顶部有「场景检索速查表」 | 生成常见业务 SQL 时先检索复用；新场景沉淀模板 |
| `assets/sql_template_examples/` | **复杂 / 数据修复场景完整 SQL 示例入口**：按需增长的独立 .sql 文件 | 复杂/特定修复场景，检索或沉淀完整可执行示例 |

> 字段级结构（字段名、类型、注释、索引）一律 `describe_table` / `validate_table_columns` 实时获取，不在此列文件内。

## 模板维护与检索（快速沉淀入口）

> 目标：既保证正确性，又通过复用沉淀提升效率。复杂场景/特定数据修复场景的 SQL 应**沉淀为可检索的模板**，后续同类任务直接复用。

### 何时检索模板
- 收到新任务时，**先查 `references/sql_templates.md` 顶部「场景检索速查表」**，按业务关键词/单据类型定位是否已有可复用模板。
- 若是复杂/修复类、且模板库未覆盖，再查 `assets/sql_template_examples/` 下的完整示例。

### 何时沉淀新模板
- 完成一次**复杂场景或数据修复**后，应把可复用的内容沉淀下来，便于下次快速检索：
  - **通用/中等复杂度** → 写入 `sql_templates.md`（按现有分类，含「业务场景」说明 + 占位符 SQL + 必要状态值）。
  - **完整、特定、可独立执行的修复 SQL** → 新增 `assets/sql_template_examples/<场景>.sql`，文件头注释包含：场景说明、涉及表、关键关联、占位符清单、（是否已验证）。

### 「已验证」标记约定（用于启用「免校验」）
- 模板/示例中的表与字段，若**首次生成时已经 `describe_table`/`validate_table_columns` 校验通过**，在模板/示例内标注 **「✅ 已验证」** 及验证日期。
- 被标记为「已验证」的表/字段，后续生成同类 SQL 时**纳入「分级校验-免校验」范围**，无需重复调 MCP，提升效率。
- 若数据库结构可能已变更（如很久未用、已知有字段调整），重新校验后再使用，或去掉「已验证」标记。

## 错误处理（MCP 异常）

当 `execute_sql` / `validate_table_columns` / `describe_table` 调用失败、超时或返回空：

1. **不要编造**：绝不臆造表名、字段名、状态值。
2. **回退占位符**：用 `<表名>` / `<字段名>` / `<tenant_id>` 等占位符表达意图，并明确标注「未经过数据库验证」。
3. **说明依赖**：告知用户缺少的真实值（如具体 `rfx_header_id`、租户编码），请其补充或确认后再执行。
4. **降级查询**：若指定表查询失败，可先查 `hpfm_tenant`、再缩小范围定位，避免一次大查询失败即放弃。

## SRM 系统扩展指南

当遇到本助手未覆盖的表或业务时：

1. **先 MCP 取结构**：用 `describe_table('<新表>')` 获取真实字段与注释，不要凭空假设。
2. **沉淀业务语义**：把数据库拿不到的关联/规则补充到 `references/relations.md` 或 `references/table_meta.md`（而非创建本地表结构文件）。
3. **沉淀可复用模板**：复杂场景写入 `references/sql_templates.md`，独立修复 SQL 存入 `assets/sql_template_examples/`，并标注「✅ 已验证」。
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
3. **先查后改**：任何写入前先 `SELECT` 确认影响行数，必要时加 `LIMIT`/事务。
4. **占位符规范**：输出给用户的可执行 SQL 用 `<...>` 标注待替换值，并说明替换方法。
5. **生产库谨慎**：默认连接生产库，写入语句务必二次确认影响范围，必要时建议用户在测试库先验证。

## 总结

本助手通过 **sql-ops MCP 实时获取表结构** + **本地仅沉淀业务语义与模板资产**，在精简体积、避免暴露表结构的同时保证准确性：

- 结构事实 → `describe_table` / `validate_table_columns` / `execute_sql`
- 业务语义 → `relations.md` / `table_meta.md`
- 复用提效 → `sql_templates.md`（模板库+检索索引）+ `assets/sql_template_examples/`（复杂场景示例），并依「分级校验策略」对「已验证」内容免校验
- 所有铁律（多租户、主键、状态同步、附件删除、人员 ID 指向 iam_user、延时消息、征询单类型、寻源结果删除、禁止编造）**始终生效**。
