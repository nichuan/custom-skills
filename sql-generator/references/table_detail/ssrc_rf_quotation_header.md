# ssrc_rf_quotation_header - 征询单报价头表

## 表说明
征询单报价头表，存储征询单的报价头信息。是SRM采购寻源系统的核心业务表之一，记录供应商对征询单的报价信息。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| quotation_header_id | bigint(20) | 主键，报价头ID | PRIMARY |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_rf_quotation_header_tenant_id) |
| rf_header_id | bigint(20) | RF单头ID | INDEX |
| quotation_num | varchar(60) | RF报价单号 | UNIQUE (quotation_num, tenant_id) |
| quotation_status | varchar(30) | 报价单状态 | INDEX |
| display_quotation_status | varchar(30) | 报价单展示状态 | - |
| supplier_tenant_id | bigint(20) | 供应商租户ID | INDEX |
| supplier_company_id | bigint(20) | 供应方企业ID | INDEX |
| supplier_company_name | varchar(500) | 供应方企业名称 | - |
| rfi_attachment_uuid | varchar(60) | RFI附件UUID | - |
| business_attachment_uuid | varchar(60) | 商务附件UUID | - |
| tech_attachment_uuid | varchar(60) | 技术附件UUID | - |
| rf_line_supplier_id | bigint(20) | RF供应商行表id，ssrc_rf_line_supplier主键 | INDEX |
| quotation_version | bigint(20) | 版本号 | - |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| supplier_company_num | varchar(60) | 供应商公司编码 | - |
| currency_code | varchar(30) | 币种 | - |
| entry_method | varchar(30) | 录入方式，SSRC.RF_QUOTATION.ENTRY_METHOD(OFFLINE/线下录入&#124;ONLINE/线上录入) | - |
| offline_reply_status | varchar(30) | 线下回复状态，REPLIED/已回复&#124;NOT_REPLIED/未回复 | - |

## 核心索引
- PRIMARY: `quotation_header_id`
- UNIQUE: `ssrc_rf_quotation_header_u2` - (quotation_num, tenant_id)
- INDEX: `idx_ssrc_rf_quotation_header_tenant_id` - (tenant_id)
- INDEX: `ssrc_rf_quotation_header_n2` - (rf_header_id)
- INDEX: `ssrc_rf_quotation_header_n3` - (quotation_status)
- INDEX: `ssrc_rf_quotation_header_n4` - (supplier_tenant_id)
- INDEX: `ssrc_rf_quotation_header_n5` - (supplier_company_id)
- INDEX: `ssrc_rf_quotation_header_n6` - (rf_line_supplier_id)
- INDEX: `ssrc_rf_quotation_header_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 征询单相关
- 通过 `rf_header_id` 关联征询单头表 `ssrc_rf_header`
- 通过 `rf_line_supplier_id` 关联征询单供应商行表 `ssrc_rf_line_supplier`
- `ssrc_rf_quotation_line.quotation_header_id` - 关联征询单报价行表
- `ssrc_rf_quo_header_version.quotation_header_id` - 关联报价头版本表

## 常见查询场景

### 1. 根据征询单ID查询报价头列表
```sql
SELECT quotation_header_id, quotation_num, quotation_status, supplier_company_name
FROM ssrc_rf_quotation_header
WHERE tenant_id = {tenant_id}
  AND rf_header_id = {rf_header_id};
```

### 2. 根据报价单号查询报价头信息
```sql
SELECT quotation_header_id, rf_header_id, quotation_status, supplier_company_name
FROM ssrc_rf_quotation_header
WHERE tenant_id = {tenant_id}
  AND quotation_num = '{quotation_num}';
```

### 3. 查询征询单的报价行信息
```sql
SELECT rqh.quotation_header_id, rqh.quotation_num, rql.quotation_line_id, rql.rf_line_item_id
FROM ssrc_rf_quotation_header rqh
INNER JOIN ssrc_rf_quotation_line rql ON rqh.quotation_header_id = rql.quotation_header_id
WHERE rqh.tenant_id = {tenant_id}
  AND rqh.rf_header_id = {rf_header_id};
```

### 4. 查询征询单的报价头版本信息
```sql
SELECT rqh.quotation_header_id, rqh.quotation_num, rqhv.quotation_version, rqhv.qtn_total_amount
FROM ssrc_rf_quotation_header rqh
INNER JOIN ssrc_rf_quo_header_version rqhv ON rqh.quotation_header_id = rqhv.quotation_header_id
WHERE rqh.tenant_id = {tenant_id}
  AND rqh.rf_header_id = {rf_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **唯一标识**：`(quotation_num, tenant_id)` 组合唯一
3. **征询单关联**：通过 `rf_header_id` 关联征询单头表
4. **供应商关联**：通过 `supplier_company_id` 关联公司信息表
5. **供应商行关联**：通过 `rf_line_supplier_id` 关联征询单供应商行表
6. **录入方式**：支持线上录入和线下录入两种方式
7. **版本管理**：支持报价单的版本管理
