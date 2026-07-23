# 核心表元数据

本文件是 **业务语义 / 速查层**：仅沉淀数据库拿不到、或高频复用容易写错的业务语义（主键、关联、状态/枚举速查、常见租户）。
**表的原始结构（字段名、类型、注释、拓展字段、索引）一律通过 sql-ops MCP 实时获取**（详见 `SKILL.md`）：

- `describe_table('<表名>')` —— 返回完整字段清单与表注释
- `validate_table_columns('<表名>', ['字段A','字段B'])` —— 校验字段是否存在

## 元数据格式
- **表名**: 主键、核心字段1、核心字段2、关联键(外键)

---

## 核心表列表

### 基础平台
- **hpfm_tenant**: tenant_id(主键)、tenant_num(租户编码)、tenant_name(租户名)、enabled_flag
- **hpfm_company**: company_id(主键)、tenant_id(关联hpfm_tenant)、company_num(公司编码)、company_name(公司名称)、unified_social_code(统一社会信用码)、duns_code(邓白氏编码)
- **iam_user**: id(主键，**所有业务表中的人员ID都指向此id**)、organization_id(**租户ID，等价其他表的tenant_id，本表无tenant_id字段**)、login_name(用户名,全局唯一)、tenant_login_name(租户内用户名,与organization_id组合唯一)、real_name(真实姓名)、email、phone、user_type(用户类型P/C)

### 询价单 / 招标单（共用表体系）

> **重要**: 招标单/新招标单（BID开头）与询价单（RFX开头）共用以下 `ssrc_rfx_*` 系列表。两者通过 `ssrc_rfx_header.secondary_source_category` 字段区分：**新招标单 = `'NEW_BID'`**，常规询价单为该字段的非 `NEW_BID` 取值（如存在竞价等其它类型可见 `RFA` 等取值）。数据库结构完全一致，仅业务术语不同。⚠️ `ssrc_rfx_header.source_from` 是**单据来源**（手工新建/申请转单/立项转单），并非单据类型区分字段。
- **ssrc_rfx_header**: rfx_header_id(主键)、tenant_id(关联hpfm_tenant)、rfx_num(单号)、rfx_status、rfx_title、secondary_source_category(次级寻源类别，**新招标单='NEW_BID'**)、quotation_start_date、quotation_end_date
- **ssrc_rfx_header_expand**: rfx_header_expand_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、rfx_real_status
- **ssrc_rfx_line_item**: rfx_line_item_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、item_code、item_name、rfx_quantity
- **ssrc_rfx_line_supplier**: rfx_line_supplier_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、supplier_company_id、supplier_company_name、feedback_status
- **ssrc_rfx_item_sup_assign**: item_sup_assign_id(主键)、rfx_header_id(关联ssrc_rfx_header)、rfx_line_supplier_id(关联ssrc_rfx_line_supplier)、tenant_id、rfx_line_item_id、invite_flag
- **ssrc_rfx_member**: rfx_member_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、rfx_role、user_id

### 报价单 / 投标单（共用表体系）
- **ssrc_rfx_quotation_header**: quotation_header_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、supplier_company_id、quotation_status、qtn_total_amount
- **ssrc_rfx_quotation_line**: quotation_line_id(主键)、quotation_header_id(关联ssrc_rfx_quotation_header)、tenant_id、rfx_line_item_id、valid_quotation_price、total_amount

### 评分 / 评标

> **注意**: 评分表通过 `source_from` 区分上下文字段：`'RFX'` = 询价单评分，`'BID'` = 老招标单评标，老招标几乎已经不用了，没有特殊说明都是RFX，新招标也是RFX。
- **ssrc_evaluate_expert**: evaluate_expert_id(主键)、source_header_id(关联rfx_header_id)、tenant_id、source_from、expert_user_id、team、scored_status
- **ssrc_evaluate_indic**: evaluate_indic_id(主键)、source_header_id(关联rfx_header_id)、tenant_id、source_from、indicate_name、weight、max_score
- **ssrc_evaluate_score**: evaluate_score_id(主键)、source_header_id(关联rfx_header_id)、quotation_header_id、tenant_id、evaluate_expert_id、sum_indic_score
- **ssrc_evaluate_score_line**: evaluate_line_id(主键)、evaluate_score_id(关联ssrc_evaluate_score)、tenant_id、evaluate_indic_id、indic_score
- **ssrc_evaluate_summary**: evaluate_summary_id(主键)、source_header_id(关联rfx_header_id)、quotation_header_id、tenant_id、score、score_rank

### 资格预审
- **ssrc_prequal_header**: prequal_header_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、prequal_status、prequal_end_date
- **ssrc_prequal_line**: prequal_line_id(主键)、prequal_header_id(关联ssrc_prequal_header)、tenant_id、supplier_company_id、prequal_line_status

### 寻源结果

> **注意**: `source_from` 区分：`'RFX'` = 询价场景，`'BID'` = 老招标场景。
- **ssrc_source_result**: result_id(主键)、source_header_id(关联rfx_header_id)、tenant_id、source_from、supplier_company_id、item_code、unit_price、receipts_status、occupation_quantity、source_result_execute_status、result_execution_strategy
- **ssrc_source_result_change_history**: history_id(主键)、source_result_id(关联ssrc_source_result)、tenant_id、change_type、order_num、occupation_quantity

### 寻源模板
- **ssrc_source_template**: template_id(主键)、tenant_id、template_num、template_name、template_status、source_category

### 延时消息
- **spfm_pending_message**: pending_message_id(主键)、tenant_id、biz_id、biz_type、server_name、execute_type、execute_time、executed_flag、expand_param、adaptor_code

### 征询单
- **ssrc_rf_header**: rf_header_id(主键)、tenant_id(关联hpfm_tenant)、rf_num(单号)、display_rf_status(显示状态)、current_node(当前节点)、rf_title(标题)
- **ssrc_rf_conf_rule**: rf_conf_rule_id(主键)、rf_header_id(关联ssrc_rf_header)、tenant_id、quotation_end_date(报价截止时间)、quotation_running_duration(报价时长)
- **ssrc_rf_quotation_header**: quotation_header_id(主键)、rf_header_id(关联ssrc_rf_header)、tenant_id、supplier_company_id、quotation_status、display_quotation_status
- **ssrc_rf_line_item**: rf_line_item_id(主键)、rf_header_id(关联ssrc_rf_header)、tenant_id、item_code、item_name、demand_quantity、uom_id
- **ssrc_rf_line_supplier**: rf_line_supplier_id(主键)、rf_header_id(关联ssrc_rf_header)、tenant_id、supplier_company_id、supplier_company_name、feedback_status
- **ssrc_rf_item_sup_assign**: rf_item_sup_assign_id(主键)、rf_line_item_id(关联ssrc_rf_line_item)、rf_line_supplier_id(关联ssrc_rf_line_supplier)、tenant_id

---

## 维护说明

### 添加新表
1. 按照上述格式添加表元数据
2. 确保标注主键和外键关联
3. 仅列出**高频使用的3-5个核心字段**
4. 关联、状态语义等数据库拿不到的业务知识沉淀在此文件（而非 `table_detail/`）
5. 复杂/数据修复场景的**完整 SQL 示例**沉淀到 `assets/sql_template_examples/`（见 `SKILL.md` 模板维护章节）

### 表命名规范
- **hpfm_** 前缀：平台基础数据表
- **ssrc_rfx_** 前缀：询价单相关表
- **ssrc_rf_** 前缀：征询单相关表
- **ssrc_evaluate_** 前缀：评分相关表
- **ssrc_prequal_** 前缀：资格预审相关表
- **ssrc_source_** 前缀：寻源相关表
- **spfm_** 前缀：平台消息/待办相关表（如 spfm_pending_message 延时消息表）

---

## 常用参考租户（使用前务必先查真实值）

> SRM 多租户，绝大多数 SQL 都要带 `tenant_id`。历史示例中常见业务租户：
> - `tenant_num = 'SRM-JDENERGY'` 历史上对应 `tenant_id = 155357`（**仅供参考，绝不硬编码**）
>
> ✅ 正确做法：先用 `SELECT tenant_id, tenant_num FROM hpfm_tenant WHERE tenant_num = '目标租户'` 获取真实 `tenant_id` 后再代入。

## 易错枚举速查（数据库注释通常含值集，以下为高频易错项）

- **team（评标专家/指标分组）**：`BUSINESS`(商务) / `TECHNOLOGY`(技术) / `BUSINESS_TECHNOLOGY`(商务+技术)
- **rfx_role（ssrc_rfx_member 成员角色）**：`RFX_BY`(寻源负责人) / `CHECKED_BY`(审批人) / `PRETRIAL_BY`(预审人) / `OPENED_BY`(开标人)
- **ssrc_rf_header.source_from（征询单来源）**：`RFI`(信息征询) / `RFP`(方案征询) / `RFQ`(价格征询)
- 其余状态枚举（rfx_status / quotation_status / feedback_status / 寻源结果状态等）见 `references/sql_templates.md` 附录「常用状态值参考」。

## 拓展字段补充（iam_user 特例）

- 标准 SRM 业务表拓展字段为 `attribute_decimal/datetime/varchar/longtext` 各 `1~10`（见 `SKILL.md` 拓展字段规则）。
- **`iam_user` 例外**：其拓展字段为 `attribute1 ~ attribute15`（均为 `varchar(150)`），处理 iam_user 时以 `describe_table` 实际返回为准，不要套用 1~10 规则。
