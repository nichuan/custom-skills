---
name: spuc-sql-generator
description: 基于 SRM 盘古订单履约域（SPUC 订单、SINV 收货事务、SLOD 发货工作台、老送货单、SIEC 状态机、委外）的 SQL 生成助手，支持业务查询 SQL 生成、数据修复 SQL 生成、表结构及关联关系查询。通过 sql-ops MCP 对接真实数据库：字段/结构一律实时获取（describe_table / validate_table_columns），逐步执行只读查询获取真实值（先租户、再单据、再业务）后生成可执行 SQL，MCP 异常时回退占位符，严禁编造。复用提效采用「DB 模板库（sql-template MCP，Supabase）+ 分级校验」：生成前先按盘古专属分类/关键词检索模板复用，生成后询问用户沉淀结果。专门针对采购订单、收货工作台事务、发货工作台（送货/计划/标签）、老送货单、导出外部/结算/商城状态修复等核心业务场景。与 ssrc-sql-generator（采购寻源：询价/招标/报价/评分）互补，寻源类需求请勿使用本技能。
---

# SRM 盘古订单履约 SQL 生成助手

> 本助手专门用于 **SRM 盘古（订单履约域）** 的数据库 SQL 生成与调整。
> 涉及的核心业务包括：**采购订单（SODR）、收货工作台事务（SINV_RCV）、发货工作台（SLOD：送货/计划/标签）、老送货单（SINV_ASN）、状态机（SIEC）、委外（SINV_OUTSOURCE）** 等。
> ⚠️ **与 ssrc-sql-generator 的分工**：询价单/招标单/报价/评分/寻源结果等 **采购寻源** 场景请使用 `ssrc-sql-generator`；本技能只负责 **订单及其下游履约（收发货、结算导出）**。

## 重要提示（必读）

1. **多租户隔离**：几乎所有业务表都含 `tenant_id` 字段。**生成的 SQL 必须包含 `tenant_id` 条件**（除非明确说明是跨租户巡检/监控查询），否则会误改/误查其他租户的数据。
2. **生产环境安全**：所有 SQL 默认针对 **生产数据库**（sql-ops MCP 默认实例 **SAAS-SRM-PROD**、库 **srm**）。执行任何写入前必须先 `SELECT` 确认影响范围，优先使用占位符（如 `<tenant_id>`、`<po_header_id>`）而非真实值。
3. **跨库注意**：发货工作台表在 **`srm_logistics_delivery`** 库（`slod_*`），其余（订单/收货/老送货/主数据）在 **`srm`** 库。跨库 JOIN 时表名必须带库名前缀（如 `srm_logistics_delivery.slod_asn_line`、`srm.sinv_rcv_trx_line`）。
4. **结构事实走 MCP**：表的字段名、类型、注释、拓展字段、索引等**不再本地维护**，一律通过 sql-ops MCP 实时获取；本地文件只沉淀数据库拿不到或高频易错的**业务语义**（见「参考文件指引」）。
5. **禁止编造**：不确定的表名、字段名、状态值、枚举值，必须调 MCP 验证或查询真实数据，**绝不凭记忆臆造**。

## 工具能力（sql-ops MCP）

| 工具 | 用途 | 典型场景 |
|------|------|----------|
| `execute_sql("<SQL>")` | 执行只读 SQL 查询 | 获取租户 ID、单据主键、状态值、验证数据 |
| `validate_table_columns("<表名>", ["字段A","字段B"])` | 校验字段是否存在 | 生成 UPDATE/WHERE 前确认字段名拼写 |
| `describe_table("<表名>")` | 返回完整字段清单与表注释（含拓展字段） | 不确定字段、需要完整结构时 |

> 结构信息一律用上述工具实时获取；不要引用本地表结构文档。
> 模板库存于 **DB（sql-template MCP / Supabase）**，检索与沉淀一律走 MCP。

## 工具能力（sql-template MCP，模板库）

| 工具 | 用途 | 典型场景 |
|------|------|----------|
| `search_sql_template(keyword, doc_type, category, verified_only, limit)` | 检索可复用模板 | 生成前先按盘古分类/关键词/表名定位已有模板 |
| `save_sql_template(title, category, scenario, sql_text, ...)` | 沉淀本次生成的 SQL 为模板 | 复杂场景完成后询问用户并保存 |
| `get_sql_template(id)` / `list_sql_templates(...)` | 按 id 获取 / 总览模板库 | 查看某模板或全量浏览 |
| `update_sql_template(id, ...)` | 更新模板（如补「✅ 已验证」） | 复核后标记验证 |
| `record_template_usage(id)` | 记录使用一次（使用次数 +1） | 复用模板生成后调用，优化排序 |

### 盘古模板检索/沉淀约定（与 ssrc 区分，保证检索准确）

- **category（业务分类）** 使用盘古专属取值：`订单SPUC` / `物流收货SINV` / `物流发货SLOD` / `盘古通用查询` / `数据修复-盘古`；
- **doc_type（单据类型）** 使用：`采购订单` / `收货事务` / `发货单` / `送货单` / `状态机`；
- **title 前缀** 统一使用 `【盘古-xx】`（如 `【盘古-订单】订单状态修复-已发布`）；
- **keywords** 必含 `盘古` 或 `spuc`，再补业务词（如「订单状态,已确认,发运行」）；
- 检索时优先带 `category` 或 `doc_type` 过滤，避免与 ssrc 寻源模板（询价单RFX/征询单RF 等分类）混淆。

> 模板库不可用（MCP 未连接/报错）时**降级**：不检索模板直接生成、完成后提示「无法沉淀」，不阻塞主流程。

## 执行步骤（铁律，必须严格遵循）

生成任何 SQL 前，按以下顺序执行，**严禁跳步**：

1. **先检索模板库**：调用 `search_sql_template`，按盘古分类（`category=订单SPUC/物流收货SINV/物流发货SLOD/...`）+ 业务关键词检索已有模板；优先复用 `verified=true`（✅ 已验证）模板。MCP 不可用则跳过本步继续。
2. **确认业务上下文**：按「术语映射表」判断单据体系（订单 sodr / 收货事务 sinv_rcv / 发货工作台 slod / 老送货单 sinv_asn），**特别注意老送货单与发货工作台送货单是两套表**；上下文不足时才向用户澄清。
3. **确认目标租户**：先 `SELECT tenant_id FROM hpfm_tenant WHERE tenant_num = '<租户编码>'`（或按 tenant_name 模糊）获取真实 `tenant_id`，**绝不硬编码**（历史示例中的 `46997`/`151025` 等仅供参考）。
4. **确认涉及表与字段（分级校验）**：按「分级校验策略」判断哪些可直接使用、哪些需 MCP 校验；命中已验证模板的表/字段免校验。需要完整结构时调 `describe_table`。
5. **逐步获取真实值**：按「先租户 → 再单据主键（po_header_id / rcv_trx_header_id / asn_header_id）→ 再行/发运行/记录表」的顺序，用 `execute_sql` 取真实主键/关联键，**禁止用硬编码 ID 直接生成修改 SQL**。
6. **生成 SQL**：基于已验证的真实值生成；占位符用 `<...>` 标注，并给出「替换为真实值的方法」。生成 UPDATE 注意：
   - 仅修复用户要求修复的字段，不要画蛇添足；
   - **`sodr_*` 订单表更新必须带 `object_version_number = object_version_number + 1`**（乐观锁）；
   - 按团队惯例带 `last_update_date = now()`，数据修复建议在 `attribute_longtext10`（或表实际使用的留痕字段）追加 `concat(IFNULL(attribute_longtext10,','),'数据修复/<工单号>')`；
   - WHERE 条件用 `tenant_id + 主键` 定位。
7. **自检安全规则**：套用「术语映射表与状态规则」「数据库约束与安全规则」逐条核对（多租户、乐观锁、pe_supplier 组合字段、关闭/取消互斥、ES 表联动、上下游协同、跨库前缀）。
8. **MCP 异常回退**：若 MCP 工具调用失败或无返回，改用占位符并明确标注「未经过数据库验证」，绝不编造字段或值。
9. **完成后询问沉淀**：向用户展示结果后，**主动询问是否将本次 SQL 沉淀为模板**；确认则按「盘古模板约定」调用 `save_sql_template`，并按需 `record_template_usage`；拒绝则跳过。

## 分级校验策略（正确性与效率兼顾）

### ✅ 可直接使用，无需 MCP 校验
- 来自 **sql-template MCP 检索结果中 `verified=true`（✅ 已验证）** 的盘古模板的表名与字段；
- 在 **`references/table_meta.md`** 中明确列出的表名、主键、关联键（如 `po_header_id`、`rcv_trx_line_id`、`asn_line_id`、`tenant_id`）；
- 在 **`references/relations.md`** 中明确给出的关联与规则；
- **标准拓展字段** `attribute_decimal / attribute_datetime / attribute_varchar / attribute_longtext` 各 `1~10`（部分物流表留痕用到 `attribute_longtext60`，使用前需校验存在性）；
- `hpfm_tenant` / `hpfm_company` / `iam_user` 等基础表的高频字段。

### ⚠️ 必须调 MCP 校验后再用
- 表名/字段名不明确、不在上述可信来源中出现的；
- 用户口头描述或自定义的字段（如「那个含税金额」需确认是 `tax_included_amount` 还是 `tax_include_amount`——**订单头是 `tax_include_amount`、收货事务行是 `tax_included_amount`，极易写错**）；
- 对拼写、存在性有任何怀疑的；生成 UPDATE/WHERE 前对关键字段调 `validate_table_columns` 确认。

### 🔄 运行期真实值仍走 execute_sql
- `tenant_id`、`po_header_id`、`rcv_trx_header_id`、`asn_header_id`、各类记录表主键、具体状态值等**真实取值**，仍需通过 `execute_sql` 逐步查询获得。

### 🛡️ 异常回退
- MCP 调用失败/无结果时：改用占位符并标注「未验证」，**严禁编造**。

## 术语映射表与状态规则

> 以下为盘古域独有的、极易混淆的概念。**生成 SQL 前务必对照核对**。

### 1. 老送货单 vs 发货工作台送货单（两套表，最易混）
- **老送货单**：`srm.sinv_asn_*`（sinv_asn_header / sinv_asn_line / sinv_asn_header_es / sinv_asn_line_es / sinv_label_*）。
- **发货工作台送货单**：`srm_logistics_delivery.slod_asn_*`（slod_asn_header / slod_asn_line / slod_plan_* 计划 / slod_label_* 标签）。
- 租户是否开启发货工作台决定走哪套表；不确定时先查 `slod_node_config` 是否有该租户配置或向用户确认。

### 2. 订单状态字段组合（sodr_po_header）
- 状态由多字段组合表达：`status_code` + `approved_flag` + `erp_approval_flag` + `released_flag` + `confirmed_flag` + `closed_flag` + `cancelled_flag`。
- 典型组合：
  - 新建：全 0 + `status_code='PENDING'`（并清 `change_sync_status`）
  - 审批通过：approved=1, erp_approval=1, released=0, confirmed=0, `status_code='APPROVED'`
  - 已发布：+released=1（`released_date=now()`，清 `po_upgrade_re_confirm_flag`），`status_code='PUBLISHED'`
  - 已确认：+confirmed=1（`status_code` 仍为 `'PUBLISHED'`，展示层按 confirmed_flag 翻译为 CONFIRMED）
- `closed_flag` / `cancelled_flag` 取值：`0`=否、`1`=是、`2`=处理中、`3`=待确认（如 `cancelled_flag=3` 为取消待确认）。**关闭与取消互斥，不能同时为 1**。
- 修复整单取消时**头金额需归零**（`amount=0, tax_include_amount=0`）；修复行取消时发运行 `can_create_asn_flag=0` 并重算头金额（排除取消行）。
- 修复为已确认/已取消/已关闭后，**必须关注下游 `sinv_rcv_trx_line` 待收货数据的 `complete_flag` 同步**（确认→打开 complete_flag=0；取消/关闭→complete_flag=1）。
- 头/行/发运行状态的**展示翻译**逻辑见模板「订单头行状态翻译」，LOV 为 `SODR.PO_STATUS`。

### 3. 乐观锁规则（sodr 系列专属）
- **所有 `sodr_*` 表的 UPDATE 必须带 `object_version_number = object_version_number + 1`**，否则前端保存会版本冲突。
- `sinv_*` / `slod_*` 表一般无此要求（以 `describe_table` 实际字段为准）。

### 4. 供应商修复规则（pe_supplier 组合字段）
- 平台供应商表 `sslm_supplier_basic`（键 `supplier_company_id`），本地供应商表 `sslm_external_supplier`（键 `supplier_id`，其 `link_id` 即平台的 `supplier_company_id`）。
- **`pe_supplier` = `supplier_company_id`-`supplier_id`（平台id-本地id）拼接**；`settle_pe_supplier` = `settle_supplier_id`-`settle_erp_supplier_id` 拼接；两者都为空时不处理。
- 订单头结算供应商标准逻辑与公司一致：修复公司时同步检查 `settle_company_id/settle_company_name`。
- 供应商字段命名差异：收货事务/老送货用 `supplier_num`，发货工作台用 `supplier_code`，订单头用 `supplier_code`——写 SQL 前校验。

### 5. 收货导出记录（sinv_rcv_change_record）import_type 枚举
- `SETTLE`=推结算、`SINV_TO_SLOD`=推发货、`SINV_TO_SODR`=推订单、`SINV_TO_PR`=推申请、`RCV_EXPORT`=推外部、`SINV_TO_MALL`=推商城、`SINV_TO_OUTSOURCE`=推委外、`ANT_AUDIT`=反审核。
- `source_document_table` 区分头/行维度：`sinv_rcv_trx_header` / `sinv_rcv_trx_line`。
- 修复要点：把状态改回 `FAIL` 可触发重推；改推订单状态**必须极其谨慎**；对接多外部系统时 WHERE 需带 `external_system_code`；关注「导出外部成功才导结算」的租户配置联动。

### 6. ES 表（外部系统映射）联动规则
- `*_es` 表保存与外部系统（ERP等）的单据映射（如 `sodr_po_header_es`、`slod_asn_header_es`、`sinv_rcv_trx_line_es`）。
- **同步状态「成功 → 失败」时必须删除对应 ES 表数据**（否则外部映射残留导致重复/冲突）；「失败 → 成功」时若无 ES 数据需按插入模板补 ES（先修头行表再插 ES，ES 取值来自头行表）。
- 委外等清理场景：**先删 ES 表、再删业务表**。

### 7. 数据清理规则（上下游协同）
- 收货事务清理需覆盖：`sinv_rcv_trx_order_link` → `sinv_rcv_trx_header/line` → `*_es` → `*_ext` → `sinv_rcv_trx_score` → `sinv_rcv_record_strategy_mapping`；若开启发货工作台，还含 `slod_idempotent_record`（record_type='10'）与 `slod_trx_dly_detail`。
- 发货工作台清理需覆盖：`slod_delivery_init_info_link` → `slod_po_dly_record` → `slod_idempotent_record`(record_type='20') → ASN/PLAN/LABEL 三套头行 + `*_es` + `slod_delivery_line_ext/header_ext`(按 source_type) + `slod_dly_line_export_record` + `slod_po_dly_strategy_change_record`。
- 订单删除共 6 张表：`sodr_po_header/line/line_location` + 三张 `*_es`；**删除前必须确认前置单据数量释放与预算释放**。
- 原则：1）只针对指定租户；2）针对指定单据必须上下游协同清理；3）清理生成建议用 `concat('delete ...')` 反查生成再人工执行。

### 8. 修复留痕规则
- 数据修复类 UPDATE 建议在留痕字段追加工单号：`attribute_longtext10 = concat(IFNULL(attribute_longtext10,','),'数据修复/<工单号>')`（部分物流表用 `attribute_longtext60`，用前校验）。
- 统一带 `last_update_date = now()`。

### 9. 同步/幂等记录表
- 订单侧同步记录：`sodr_po_status_sync_record`（`sync_type`：`SRM_EXP_ERP` 新建同步、`DELIVERY_EXP_ERP` 交期同步、`ORDER_DELIVERY_WORK` 订单同步发货工作台）；无记录时按插入模板补 FAIL/SUCCESS 记录触发或标记。
- 消费幂等：`sodr_consumer_idempotent`（订单/发货消息消费）；发货幂等：`slod_idempotent_record`（record_type：'10' 收货、'20' 订单初始化）。
- 收货同步类调度任务：`SINV_TO_SETTLE_BATCH_SYNC` / `SINV_TO_SLOD_BATCH_SYNC` / `SINV_TO_SODR_BATCH_SYNC`，可复制临时任务加参 `{"importStatus":"IMPORTING"}` 重推，配置表 `spuc_sinv_sitf_import_split_line` 需含租户。

### 10. 何时建议走 API/调度而非 SQL
- 事务导入/反审核/事务重推/审批回调/订单初始化/策略更新等场景，**平台有标准数据修复接口或调度**，优先建议接口而非直接 UPDATE（尤其涉及推送订单状态、已导出外部成功的单据）。SQL 修复仅用于接口无法覆盖或明确要求的场景。

## 参考文件指引

| 文件 | 作用 | 何时用 |
|------|------|--------|
| `references/relations.md` | 表关联关系 + 业务规则（纯业务知识，数据库拿不到） | 不确定表间关系、关联键、上下游联动规则时 |
| `references/table_meta.md` | 业务语义/速查层：表名-主键-关联键速查、易错枚举、主数据速查 | 快速确认表/主键/关联键、高频枚举值时 |

> 字段级结构一律 `describe_table` / `validate_table_columns` 实时获取；SQL 模板一律走 sql-template MCP（盘古专属分类）。

## 模板维护与检索（DB 模板库闭环）

### 检索模板（生成前）
- 收到新任务时，**先调用 `search_sql_template`**，按盘古分类（`category`）/单据类型（`doc_type`）/关键词（含「盘古」）检索。
- 优先复用 `verified_only=true` 模板；MCP 不可用时降级为「不检索直接生成」。

### 沉淀模板（生成后）
- 完成一次**复杂场景或数据修复**后，**主动询问用户是否沉淀**，确认后按「盘古模板约定」调用 `save_sql_template`：
  - `title`：`【盘古-xx】...` 前缀；
  - `category`：`订单SPUC` / `物流收货SINV` / `物流发货SLOD` / `盘古通用查询` / `数据修复-盘古`；
  - `doc_type`：`采购订单` / `收货事务` / `发货单` / `送货单` / `状态机`；
  - `keywords`：必含 `盘古`；`core_tables` / `placeholders` 照实填写；
  - `verified`：表/字段已 MCP 校验通过则置 `true` 并填 `verified_at`。
- 复用模板生成后调用 `record_template_usage(id)`。

### 去重
- `save_sql_template` 内置相似去重；确需覆盖用 `update_sql_template`。

## 错误处理（MCP 异常）

当 `execute_sql` / `validate_table_columns` / `describe_table` 调用失败、超时或返回空：
1. **不要编造**：绝不臆造表名、字段名、状态值。
2. **回退占位符**：用 `<表名>` / `<字段名>` / `<tenant_id>` 等占位符表达意图，并标注「未经过数据库验证」。
3. **说明依赖**：告知用户缺少的真实值（如具体 `po_header_id`、租户编码）。
4. **降级查询**：先查 `hpfm_tenant` 再缩小范围定位，避免一次大查询失败即放弃。

当 **sql-template MCP** 不可用时：
5. **检索降级**：不检索模板直接按铁律生成，不阻断主流程。
6. **沉淀降级**：完成后提示「模板库当前不可用，本次结果未沉淀」。

## 盘古系统扩展指南

1. **先 MCP 取结构**：用 `describe_table('<新表>')` 获取真实字段与注释。
2. **沉淀业务语义**：把数据库拿不到的关联/规则补充到 `references/relations.md` 或 `references/table_meta.md`。
3. **沉淀可复用模板**：复杂场景完成后按盘古约定 `save_sql_template` 沉淀（校验通过置 `verified=true`）。
4. **更新本 SKILL**：在术语映射表或参考文件指引中补充新概念。
5. **禁止**：不要为每张表创建本地结构文件——结构事实统一走 MCP。

## 核心业务概念（背景知识）

### 1. 订单履约主流程
寻源结果/申请/合同 → 生成采购订单（sodr）→ 审批 → 发布 → 供应商确认（可含电子签章）→（开启发货工作台则）订单初始化发货 → 送货/计划/标签（slod）→ 收货事务（sinv_rcv）→ 推结算/推外部/推商城/推委外。

### 2. 关键实体关系
- **订单**：`sodr_po_header` 1:N `sodr_po_line` 1:N `sodr_po_line_location`（发运行，数量占用/收发货净数在此）
- **发货工作台**：订单发运行 → `slod_delivery_init_info_link`（初始化链接）→ `slod_asn_*` / `slod_plan_*` / `slod_label_*`
- **收货事务**：`sinv_rcv_trx_order_link`（来源链接）→ `sinv_rcv_trx_header` 1:N `sinv_rcv_trx_line`；导出记录 `sinv_rcv_change_record`
- **老送货单**：`sinv_asn_header` 1:N `sinv_asn_line`，占用订单发运行 `occupied_quantity`
- **签章**：`sodr_po_header_sign`（electric_sign_status：EFFECTED/CANCELLATION）

### 3. 常见操作类型
- 查询类：单据状态/占用数量/导出状态/策略配置/操作记录/异常监控
- 修复类：状态回退与推进、供应商与主数据字段修复、金额修复、同步状态修复、编号修复
- 清理类：初始化数据删除、单据级联清理（必须上下游协同）

## 数据库约束与安全规则

1. **多租户强制**：业务 SQL 必须带 `tenant_id`（跨租户巡检除外，需显式说明）。
2. **主键优先**：UPDATE/DELETE 必须用主键或唯一业务键（如 `po_header_id`、`rcv_trx_line_id`）定位，**严禁无 WHERE 或仅凭编号模糊更新**。
3. **先查后改**：任何写入前必须保留对应 `SELECT` 核查原数据，必要时加 `LIMIT`/事务。
4. **乐观锁**：`sodr_*` 表 UPDATE 必带 `object_version_number = object_version_number + 1`。
5. **占位符规范**：输出 SQL 用 `<...>` 标注待替换值并说明替换方法。
6. **生产库谨慎**：默认连接生产库，写入语句务必二次确认影响范围。

## SQL 输出格式规范（写入类操作）

> 仅适用于含 INSERT / UPDATE / DELETE 的输出。**纯查询类 SQL 不受此约束。**

### ✅ 必须包含：原始数据核查 SELECT（提交前人工确认）
- 每条 **UPDATE / DELETE** 之前，必须保留一段用**完全一致** WHERE 条件的 `SELECT`，并标注「预期影响 N 行」。
- 推荐写法：
  ```sql
  -- ① 原始数据核查（预期影响 1 行，确认无误后再执行下方 UPDATE）
  SELECT po_header_id, status_code, released_flag, confirmed_flag, closed_flag, cancelled_flag
  FROM sodr_po_header
  WHERE tenant_id = <tenant_id> AND po_header_id = <po_header_id>;

  -- ② 修复为已发布
  UPDATE sodr_po_header
  SET approved_flag = 1, erp_approval_flag = 1, released_flag = 1, confirmed_flag = 0,
      po_upgrade_re_confirm_flag = NULL, status_code = 'PUBLISHED',
      closed_flag = 0, cancelled_flag = 0,
      released_date = now(), last_update_date = now(),
      object_version_number = object_version_number + 1
  WHERE tenant_id = <tenant_id> AND po_header_id = <po_header_id>;
  ```

### ✅ 推荐包含：执行后校验 SELECT
- 更新/删除后附一段 `SELECT` 校验结果（如「预期状态 = 目标值」「预期 0 行」）。

### ❌ 禁止包含
- **执行前备份**：不得输出 `CREATE TABLE bak_xxx AS SELECT ...`。
- **回滚方案**：不得输出回滚段；生产修复以「先 SELECT 核查 → 人工确认 → 可控提交」为准。

## 总结

本助手通过 **sql-ops MCP 实时获取表结构** + **本地仅沉淀业务语义** + **DB 模板库（盘古专属分类）复用沉淀**，覆盖订单履约全链路：

- 结构事实 → `describe_table` / `validate_table_columns` / `execute_sql`
- 业务语义 → `relations.md` / `table_meta.md`
- 复用提效 → `search_sql_template`（按盘古分类检索）+ `save_sql_template`（按盘古约定沉淀）
- 所有铁律（多租户、乐观锁、pe_supplier 组合、关闭/取消互斥、ES 联动、上下游协同、跨库前缀、留痕、禁止编造）**始终生效**。
