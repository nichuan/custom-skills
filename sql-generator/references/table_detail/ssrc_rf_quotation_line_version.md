# ssrc_rf_quotation_line_version - 征询单报价行版本表

## 表说明
征询单报价行版本表，存储征询单报价行的版本历史信息。是SRM采购寻源系统的核心业务表之一，记录报价行的版本变更历史。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| quotation_line_version_id | bigint(20) | 主键，报价行版本ID | PRIMARY |
| quotation_line_id | bigint(20) | 报价行ID | INDEX |
| quotation_header_id | bigint(20) | 征询报价单头ID | INDEX |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_rf_quotation_line_version_tenant_id) |
| quotation_line_status | varchar(30) | 报价单行状态SSRC.RF_QUOTATION_LINE_STATUS(NEW/新建&#124;SUBMITTED/已报价&#124;BARGAINED/已还价&#124;TAKEN_BACK/收回&#124;ABANDONED/放弃) | INDEX |
| rf_line_item_id | bigint(20) | 征询单物料行ID | INDEX |
| tax_included_flag | tinyint(1) | 含税标识 | - |
| tax_id | bigint(20) | 税率ID | INDEX |
| tax_rate | decimal(5,2) | 税率 | - |
| quoted_date | datetime | 报价时间 | INDEX |
| price_batch_quantity | decimal(20,6) | 价格批量数量 | - |
| valid_quoted_by | bigint(20) | 有效报价人 | INDEX |
| valid_quotation_quantity | decimal(20,6) | 有效报价数量 | - |
| valid_quotation_price | decimal(20,6) | 有效报价单价 | - |
| valid_net_price | decimal(20,6) | 有效未税单价 | - |
| valid_quotation_remark | longtext | 有效报价理由 | - |
| benchmark_price_type | varchar(30) | 基准价(值集:SFIN.BENCHMARK_PRICE) | - |
| net_amount | decimal(20,6) | 未税金额 | - |
| tax_amount | decimal(20,6) | 税额 | - |
| total_amount | decimal(20,6) | 总金额 | - |
| attachment_uuid | varchar(60) | 附件UUID | - |
| abandoned_flag | tinyint(1) | 放弃标识 | - |
| ladder_inquiry_flag | tinyint(1) | 阶梯报价标志 | - |
| quotation_line_version | bigint(20) | 报价行版本号 | - |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| quotation_header_version_id | bigint(20) | 报价头版本id | INDEX |
| rf_line_section_id | bigint(20) | 征询标段id | INDEX |
| currency_code | varchar(30) | 币种 | - |
| exchange_rate | decimal(10,6) | 汇率 | - |
| local_ln_quotation_price | decimal(20,6) | 本币报价单价 | - |
| local_ln_net_price | decimal(20,6) | 本币未税单价 | - |
| local_ln_total_amount | decimal(20,6) | 本币总金额 | - |
| local_ln_net_amount | decimal(20,6) | 本币未税金额 | - |
| local_ln_tax_amount | decimal(20,6) | 本币税额 | - |
| suggested_ln_total_amount | decimal(20,6) | 选用总金额 | - |
| suggested_ln_net_amount | decimal(20,6) | 选用未税金额 | - |
| suggested_ln_tax_amount | decimal(20,6) | 选用税额 | - |
| local_suggested_ln_total_amount | decimal(20,6) | 本币选用总金额 | - |
| local_suggested_ln_net_amount | decimal(20,6) | 本币选用未税金额 | - |
| local_suggested_ln_tax_amount | decimal(20,6) | 本币选用税额 | - |
| valid_quotation_sec_quantity | decimal(20,6) | 辅助有效报价数量 | - |
| valid_quotation_sec_price | decimal(20,6) | 辅助含税单价 | - |
| valid_net_secondary_price | decimal(20,6) | 辅助未税单价 | - |
| local_ln_quotation_sec_price | decimal(20,6) | 本币辅助含税单价 | - |
| local_ln_net_sec_price | decimal(20,6) | 本币辅助未税单价 | - |

## 核心索引
- PRIMARY: `quotation_line_version_id`
- INDEX: `idx_ssrc_rf_quotation_line_version_tenant_id` - (tenant_id)
- INDEX: `ssrc_rf_quotation_line_version_n2` - (quotation_line_id)
- INDEX: `ssrc_rf_quotation_line_version_n3` - (quotation_header_id)
- INDEX: `ssrc_rf_quotation_line_version_n4` - (quotation_line_status)
- INDEX: `ssrc_rf_quotation_line_version_n5` - (rf_line_item_id)
- INDEX: `ssrc_rf_quotation_line_version_n6` - (tax_id)
- INDEX: `ssrc_rf_quotation_line_version_n7` - (quoted_date)
- INDEX: `ssrc_rf_quotation_line_version_n8` - (valid_quoted_by)
- INDEX: `ssrc_rf_quotation_line_version_n9` - (quotation_header_version_id)
- INDEX: `ssrc_rf_quotation_line_version_n10` - (rf_line_section_id)
- INDEX: `ssrc_rf_quotation_line_version_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 征询单报价相关
- 通过 `quotation_line_id` 关联征询单报价行表 `ssrc_rf_quotation_line`
- 通过 `quotation_header_id` 关联征询单报价头表 `ssrc_rf_quotation_header`
- 通过 `quotation_header_version_id` 关联报价头版本表 `ssrc_rf_quo_header_version`

## 常见查询场景

### 1. 根据报价行ID查询版本历史
```sql
SELECT quotation_line_version_id, quotation_line_version, quotation_line_status, valid_quotation_price, creation_date
FROM ssrc_rf_quotation_line_version
WHERE tenant_id = {tenant_id}
  AND quotation_line_id = {quotation_line_id}
ORDER BY quotation_line_version DESC;
```

### 2. 查询报价行的最新版本
```sql
SELECT quotation_line_version_id, quotation_line_version, quotation_line_status, valid_quotation_price
FROM ssrc_rf_quotation_line_version
WHERE tenant_id = {tenant_id}
  AND quotation_line_id = {quotation_line_id}
ORDER BY quotation_line_version DESC
LIMIT 1;
```

### 3. 查询报价头版本下的所有报价行版本
```sql
SELECT rqlv.quotation_line_version_id, rqlv.rf_line_item_id, rqlv.quotation_line_status, rqlv.valid_quotation_price
FROM ssrc_rf_quotation_line_version rqlv
WHERE rqlv.tenant_id = {tenant_id}
  AND rqlv.quotation_header_version_id = {quotation_header_version_id}
ORDER BY rqlv.rf_line_item_id;
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **报价行关联**：通过 `quotation_line_id` 关联征询单报价行表
3. **报价头关联**：通过 `quotation_header_id` 关联征询单报价头表
4. **版本管理**：记录报价行的版本变更历史
5. **金额记录**：记录每个版本的报价金额和选用金额
6. **双单位支持**：支持辅助单位和辅助数量
7. **本币金额**：支持本币金额的计算和记录
