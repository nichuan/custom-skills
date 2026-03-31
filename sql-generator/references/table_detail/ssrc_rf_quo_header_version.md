# ssrc_rf_quo_header_version - 征询单报价头版本表

## 表说明
征询单报价头版本表，存储征询单报价头的版本历史信息。是SRM采购寻源系统的核心业务表之一，记录报价单的版本变更历史。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| quotation_header_version_id | bigint(20) | 主键，报价头版本ID | PRIMARY |
| quotation_header_id | bigint(20) | 供应商回复头ID | INDEX |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_rf_quo_header_version_tenant_id) |
| rfi_attachment_uuid | varchar(60) | RFI附件UUID | - |
| business_attachment_uuid | varchar(60) | 商务附件UUID | - |
| tech_attachment_uuid | varchar(60) | 技术附件UUID | - |
| quotation_version | bigint(20) | 版本号 | - |
| suggested_flag | tinyint(1) | 选用标志 | - |
| suggested_remark | varchar(500) | 选用备注 | - |
| suggested_attachment_uuid | varchar(60) | 确定供应商附件UUID | - |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| currency_code | varchar(30) | 币种 | - |
| exchange_rate | decimal(10,6) | 汇率 | - |
| qtn_total_amount | decimal(20,6) | 报价总金额 | - |
| qtn_tax_amount | decimal(20,6) | 报价总税额 | - |
| qtn_net_amount | decimal(20,6) | 报价总未税金额 | - |
| suggested_qtn_total_amount | decimal(20,6) | 选用报价总金额 | - |
| suggested_qtn_net_amount | decimal(20,6) | 选用报价总未税金额 | - |
| suggested_qtn_tax_amount | decimal(20,6) | 选用报价总税额 | - |
| local_suggested_qtn_total_amount | decimal(20,6) | 本币选用报价总金额 | - |
| local_suggested_qtn_net_amount | decimal(20,6) | 本币选用报价总未税金额 | - |
| local_suggested_qtn_tax_amount | decimal(20,6) | 本币选用报价总税额 | - |
| entry_method | varchar(30) | 录入方式，SSRC.RF_QUOTATION.ENTRY_METHOD(OFFLINE/线下录入&#124;ONLINE/线上录入) | - |
| offline_reply_status | varchar(30) | 线下回复状态，REPLIED/已回复&#124;NOT_REPLIED/未回复 | - |

## 核心索引
- PRIMARY: `quotation_header_version_id`
- INDEX: `idx_ssrc_rf_quo_header_version_tenant_id` - (tenant_id)
- INDEX: `ssrc_rf_quo_header_version_n2` - (quotation_header_id)
- INDEX: `ssrc_rf_quo_header_version_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 征询单报价相关
- 通过 `quotation_header_id` 关联征询单报价头表 `ssrc_rf_quotation_header`

## 常见查询场景

### 1. 根据报价头ID查询版本历史
```sql
SELECT quotation_header_version_id, quotation_version, suggested_flag, qtn_total_amount, creation_date
FROM ssrc_rf_quo_header_version
WHERE tenant_id = {tenant_id}
  AND quotation_header_id = {quotation_header_id}
ORDER BY quotation_version DESC;
```

### 2. 查询报价头的最新版本
```sql
SELECT quotation_header_version_id, quotation_version, suggested_flag, qtn_total_amount
FROM ssrc_rf_quo_header_version
WHERE tenant_id = {tenant_id}
  AND quotation_header_id = {quotation_header_id}
ORDER BY quotation_version DESC
LIMIT 1;
```

### 3. 查询报价头的选用版本
```sql
SELECT quotation_header_version_id, quotation_version, suggested_remark, qtn_total_amount
FROM ssrc_rf_quo_header_version
WHERE tenant_id = {tenant_id}
  AND quotation_header_id = {quotation_header_id}
  AND suggested_flag = 1;
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **报价头关联**：通过 `quotation_header_id` 关联征询单报价头表
3. **版本管理**：记录报价单的版本变更历史
4. **选用标志**：`suggested_flag = 1` 表示该版本被选用
5. **金额记录**：记录每个版本的报价金额和选用金额
6. **录入方式**：支持线上录入和线下录入两种方式
