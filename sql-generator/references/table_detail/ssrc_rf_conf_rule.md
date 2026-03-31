# ssrc_rf_conf_rule - 征询单配置规则表

## 表说明
征询单配置规则表，存储征询单（RFI/RFP）的配置规则信息。是SRM采购寻源系统的核心业务表之一，定义征询单的报价方式、审批方式等业务规则。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| rf_conf_rule_id | bigint(20) | 主键，配置规则ID | PRIMARY |
| tenant_id | bigint(20) | 租户ID | INDEX (idx_ssrc_rf_conf_rule_tenant_id) |
| source_from | varchar(30) | 来源类型 RFI/RFP | INDEX |
| source_from_id | bigint(20) | 来源id | INDEX |
| quotation_type | varchar(30) | 报价方式SSRC.QUOTATION_TYPE(ONLINE/线上报价 &#124; OFFLINE/线下报价 &#124; ON_OFF/线上线下并行) | - |
| sealed_quotation_flag | tinyint(1) | 密封报价标志 | - |
| release_approve_type | varchar(30) | 发布审批方式SPFM.BUSINESS_APV_METHOD(SELF/自审批&#124;WFL/工作流&#124;EXTERNAL/外部审批) | - |
| result_approve_type | varchar(30) | 结果审批方式SPFM.BUSINESS_APV_METHOD(SELF/自审批&#124;WFL/工作流&#124;EXTERNAL/外部审批) | - |
| clarify_approve_type | varchar(30) | 澄清函审批方式SPFM.BUSINESS_APV_METHOD(SELF/自审批&#124;WFL/工作流&#124;EXTERNAL/外部审批) | - |
| expert_score_type | varchar(30) | 专家评分方式SSRC.EXPERT_SCORE_TYPE(NONE/无需专家评分&#124;ONLINE/线上专家评分&#124;OFFLINE/线下专家评分) | - |
| bid_rule_type | varchar(30) | 标书规则SSRC.BID_RULE_TYPE(NONE/不区分&#124;DIFF/分商务技术) | - |
| open_bid_order | varchar(30) | 开标步制SSRC.OPEN_BID_ORDER(SYNC/同步&#124;TECH_FIRST/先技术后商务&#124;BUSINESS_FIRST/先商务后技术) | - |
| subject_matter_rule | varchar(30) | 标的规则SSRC.SUBJECT_MATTER_RULE(PACK/分标段包&#124;NONE/不区分) | - |
| multi_reply_flag | tinyint(1) | 允许供应商多次回复标识 | - |
| auction_direction | varchar(30) | 竞价方向SSRC.SOURCE_AUCTION_DIRECTION(FORWARD/正向&#124;REVERSE/反向) | - |
| business_weight | decimal(5,2) | 商务组权重 | - |
| technology_weight | decimal(5,2) | 技术组权重 | - |
| min_quoted_supplier | int(11) | 最少报价供应商数 | - |
| start_flag | tinyint(1) | 发布即开始标识 | - |
| quotation_running_duration | decimal(10,2) | 征询运行时间 | - |
| quotation_start_date | datetime | 征询开始时间 | - |
| quotation_end_date | datetime | 征询截止时间 | - |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| score_type | varchar(30) | 评分方式SSRC.TEMPLATE_SCORE_TYPE | - |
| score_template_id | bigint(20) | 评分模板id | INDEX |
| score_template_code | varchar(60) | 参考评分模板 | - |
| line_items_flag | tinyint(1) | 含物料标识 | - |
| min_invite_supplier | int(11) | 最少邀请供应商数量 | - |
| currency_code | varchar(30) | 币种 | - |
| multi_currency_flag | tinyint(1) | 是否允许多币种报价 | - |
| clarify_end_date | datetime | 澄清截止时间 | - |
| reply_type | varchar(30) | 回复类型(值集:SSRC.RF_REPLY_TYPE) | - |

## 核心索引
- PRIMARY: `rf_conf_rule_id`
- INDEX: `idx_ssrc_rf_conf_rule_tenant_id` - (tenant_id)
- INDEX: `ssrc_rf_conf_rule_n2` - (source_from)
- INDEX: `ssrc_rf_conf_rule_n3` - (source_from_id)
- INDEX: `ssrc_rf_conf_rule_n4` - (score_template_id)
- INDEX: `ssrc_rf_conf_rule_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 征询单相关
- 通过 `source_from_id` 关联征询单头表 `ssrc_rf_header`

## 常见查询场景

### 1. 根据征询单ID查询配置规则
```sql
SELECT rf_conf_rule_id, quotation_type, sealed_quotation_flag, release_approve_type, result_approve_type
FROM ssrc_rf_conf_rule
WHERE tenant_id = {tenant_id}
  AND source_from = 'RFI'
  AND source_from_id = {rf_header_id};
```

### 2. 查询征询单的报价方式配置
```sql
SELECT rf_conf_rule_id, quotation_type, multi_reply_flag, min_quoted_supplier
FROM ssrc_rf_conf_rule
WHERE tenant_id = {tenant_id}
  AND source_from_id = {rf_header_id};
```

### 3. 查询征询单的审批方式配置
```sql
SELECT rf_conf_rule_id, release_approve_type, result_approve_type, clarify_approve_type
FROM ssrc_rf_conf_rule
WHERE tenant_id = {tenant_id}
  AND source_from_id = {rf_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **征询单关联**：通过 `source_from_id` 关联征询单头表
3. **报价方式**：支持线上、线下、线上线下并行三种报价方式
4. **审批方式**：支持自审批、工作流、外部审批三种审批方式
5. **专家评分**：支持无需专家评分、线上专家评分、线下专家评分三种方式
6. **权重配置**：支持商务组和技术组的权重配置
