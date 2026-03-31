# ssrc_rf_quotation_line - 征询单报价行表

## 表说明
征询单报价行表，存储征询单的报价行信息。是SRM采购寻源系统的核心业务表之一，记录供应商对征询单物料行的报价明细。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| quotation_line_id | bigint(20) | 主键，报价行ID | PRIMARY |
| quotation_header_id | bigint(20) | 征询报价单头ID | INDEX |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_rf_quotation_line_tenant_id) |
| quotation_line_status | varchar(30) | 报价行状态SSRC.RF_QUOTATION_LINE_STATUS(NEW/新建&#124;SUBMITTED/已报价&#124;BARGAINED/已还价&#124;TAKEN_BACK/收回&#124;ABANDONED/放弃) | INDEX |
| rf_line_item_id | bigint(20) | 征询单物料行ID | INDEX |
| tax_included_flag | tinyint(1) | 含税标识 | - |
| tax_id | bigint(20) | 税率ID | INDEX |
| tax_rate | decimal(5,2) | 税率 | - |
| quoted_date | datetime | 报价时间 | INDEX |
| price_batch_quantity | decimal(20,6) | 价格批量数量 | - |
| valid_quoted_by | bigint(20) | 报价人 | INDEX |
| valid_quotation_quantity | decimal(20,6) | 有效报价数量 | - |
| valid_quotation_price | decimal(20,6) | 有效报价单价 | - |
| valid_net_price | decimal(20,6) | 有效未税单价 | - |
| valid_quotation_remark | longtext | 报价理由 | - |
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
| rf_line_section_id | bigint(20) | 征询标段id | INDEX |
| exchange_rate | decimal(10,6) | 汇率 | - |
| valid_quotation_sec_quantity | decimal(20,6) | 辅助有效报价数量 | - |
| valid_quotation_sec_price | decimal(20,6) | 辅助含税单价 | - |
| valid_net_secondary_price | decimal(20,6) | 辅助未税单价 | - |

## 核心索引
- PRIMARY: `quotation_line_id`
- INDEX: `idx_ssrc_rf_quotation_line_tenant_id` - (tenant_id)
- INDEX: `ssrc_rf_quotation_line_n2` - (quotation_header_id)
- INDEX: `ssrc_rf_quotation_line_n3` - (quotation_line_status)
- INDEX: `ssrc_rf_quotation_line_n4` - (rf_line_item_id)
- INDEX: `ssrc_rf_quotation_line_n5` - (tax_id)
- INDEX: `ssrc_rf_quotation_line_n6` - (quoted_date)
- INDEX: `ssrc_rf_quotation_line_n7` - (valid_quoted_by)
- INDEX: `ssrc_rf_quotation_line_n8` - (rf_line_section_id)
- INDEX: `ssrc_rf_quotation_line_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 征询单报价相关
- 通过 `quotation_header_id` 关联征询单报价头表 `ssrc_rf_quotation_header`
- 通过 `rf_line_item_id` 关联征询单物料行表 `ssrc_rf_line_item`
- `ssrc_rf_quotation_line_version.quotation_line_id` - 关联报价行版本表

## 常见查询场景

### 1. 根据报价头ID查询报价行列表
```sql
SELECT quotation_line_id, rf_line_item_id, quotation_line_status, valid_quotation_price, total_amount
FROM ssrc_rf_quotation_line
WHERE tenant_id = {tenant_id}
  AND quotation_header_id = {quotation_header_id}
ORDER BY quotation_line_id;
```

### 2. 根据物料行ID查询报价行信息
```sql
SELECT quotation_line_id, quotation_header_id, quotation_line_status, valid_quotation_price
FROM ssrc_rf_quotation_line
WHERE tenant_id = {tenant_id}
  AND rf_line_item_id = {rf_line_item_id};
```

### 3. 查询征询单的报价行版本信息
```sql
SELECT rql.quotation_line_id, rql.rf_line_item_id, rqlv.quotation_line_version, rqlv.valid_quotation_price
FROM ssrc_rf_quotation_line rql
INNER JOIN ssrc_rf_quotation_line_version rqlv ON rql.quotation_line_id = rqlv.quotation_line_id
WHERE rql.tenant_id = {tenant_id}
  AND rql.quotation_header_id = {quotation_header_id};
```

### 4. 查询征询单的报价行详情
```sql
SELECT rql.quotation_line_id, rli.item_code, rli.item_name, 
       rql.valid_quotation_price, rql.total_amount, rql.quotation_line_status
FROM ssrc_rf_quotation_line rql
INNER JOIN ssrc_rf_line_item rli ON rql.rf_line_item_id = rli.rf_line_item_id
WHERE rql.tenant_id = {tenant_id}
  AND rql.quotation_header_id = {quotation_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **报价头关联**：通过 `quotation_header_id` 关联征询单报价头表
3. **物料行关联**：通过 `rf_line_item_id` 关联征询单物料行表
4. **状态管理**：支持新建、已报价、已还价、收回、放弃等状态
5. **金额计算**：支持未税金额、税额、总金额的计算
6. **双单位支持**：支持辅助单位和辅助数量
7. **阶梯报价**：支持阶梯报价功能
