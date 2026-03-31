# 核心表元数据

本文件仅维护表的**极简元数据**，用于快速匹配表名和确认基本信息。如需详细字段信息，请查看 `table_detail/[表名].md`。

## 元数据格式
- **表名**: 主键、核心字段1、核心字段2、关联键(外键)

---

## 核心表列表

### 基础平台
- **hpfm_tenant**: tenant_id(主键)、tenant_num(租户编码)、tenant_name(租户名)、enabled_flag
- **hpfm_company**: company_id(主键)、tenant_id(关联hpfm_tenant)、company_num(公司编码)、company_name(公司名称)、unified_social_code(统一社会信用码)、duns_code(邓白氏编码)

### 询价单
- **ssrc_rfx_header**: rfx_header_id(主键)、tenant_id(关联hpfm_tenant)、rfx_num(单号)、rfx_status、rfx_title、quotation_start_date、quotation_end_date
- **ssrc_rfx_header_expand**: rfx_header_expand_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、rfx_real_status
- **ssrc_rfx_line_item**: rfx_line_item_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、item_code、item_name、rfx_quantity
- **ssrc_rfx_line_supplier**: rfx_line_supplier_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、supplier_company_id、supplier_company_name、feedback_status
- **ssrc_rfx_item_sup_assign**: item_sup_assign_id(主键)、rfx_header_id(关联ssrc_rfx_header)、rfx_line_supplier_id(关联ssrc_rfx_line_supplier)、tenant_id、rfx_line_item_id、invite_flag
- **ssrc_rfx_member**: rfx_member_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、rfx_role、user_id

### 报价单
- **ssrc_rfx_quotation_header**: quotation_header_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、supplier_company_id、quotation_status、qtn_total_amount
- **ssrc_rfx_quotation_line**: quotation_line_id(主键)、quotation_header_id(关联ssrc_rfx_quotation_header)、tenant_id、rfx_line_item_id、valid_quotation_price、total_amount

### 评分
- **ssrc_evaluate_expert**: evaluate_expert_id(主键)、source_header_id(关联rfx_header_id)、tenant_id、source_from、expert_user_id、team、scored_status
- **ssrc_evaluate_indic**: evaluate_indic_id(主键)、source_header_id(关联rfx_header_id)、tenant_id、source_from、indicate_name、weight、max_score
- **ssrc_evaluate_score**: evaluate_score_id(主键)、source_header_id(关联rfx_header_id)、quotation_header_id、tenant_id、evaluate_expert_id、sum_indic_score
- **ssrc_evaluate_score_line**: evaluate_line_id(主键)、evaluate_score_id(关联ssrc_evaluate_score)、tenant_id、evaluate_indic_id、indic_score
- **ssrc_evaluate_summary**: evaluate_summary_id(主键)、source_header_id(关联rfx_header_id)、quotation_header_id、tenant_id、score、score_rank

### 资格预审
- **ssrc_prequal_header**: prequal_header_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、prequal_status、prequal_end_date
- **ssrc_prequal_line**: prequal_line_id(主键)、prequal_header_id(关联ssrc_prequal_header)、tenant_id、supplier_company_id、prequal_line_status

### 寻源结果
- **ssrc_source_result**: result_id(主键)、source_header_id(关联rfx_header_id)、tenant_id、source_from、supplier_company_id、item_code、unit_price

### 寻源模板
- **ssrc_source_template**: template_id(主键)、tenant_id、template_num、template_name、template_status、source_category

### 征询单
- **ssrc_rf_header**: rf_header_id(主键)、tenant_id(关联hpfm_tenant)、rf_num(单号)、display_rf_status(显示状态)、current_node(当前节点)、rf_title(标题)
- **ssrc_rf_conf_rule**: rf_conf_rule_id(主键)、rf_header_id(关联ssrc_rf_header)、tenant_id、quotation_end_date(报价截止时间)、quotation_running_duration(报价时长)

---

## 维护说明

### 添加新表
1. 按照上述格式添加表元数据
2. 确保标注主键和外键关联
3. 仅列出**高频使用的3-5个核心字段**
4. 在 `table_detail/` 中创建对应的详细结构文件

### 表命名规范
- **hpfm_** 前缀：平台基础数据表
- **ssrc_rfx_** 前缀：询价单相关表
- **ssrc_rf_** 前缀：征询单相关表
- **ssrc_evaluate_** 前缀：评分相关表
- **ssrc_prequal_** 前缀：资格预审相关表
- **ssrc_source_** 前缀：寻源相关表
