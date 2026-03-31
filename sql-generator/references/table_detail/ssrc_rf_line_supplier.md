# ssrc_rf_line_supplier - 征询单供应商行表

## 表说明
征询单供应商行表，存储征询单的供应商信息。是SRM采购寻源系统的核心业务表之一，记录征询单邀请的供应商列表。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| rf_line_supplier_id | bigint(20) | 主键，供应商行ID | PRIMARY |
| rf_header_id | bigint(20) | 征询单头ID | INDEX |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_rf_line_supplier_tenant_id) |
| supplier_tenant_id | bigint(20) | 供应商租户 | INDEX |
| supplier_company_id | bigint(20) | 供应商公司 | INDEX |
| supplier_company_name | varchar(500) | 供应方企业名称 | - |
| supplier_contact_id | bigint(20) | 供应商联系人 | INDEX |
| contact_name | varchar(120) | 联系人姓名 | - |
| contact_mail | varchar(240) | 联系人邮箱 | - |
| international_tel_code | varchar(30) | 供应商联系电话-国际电话区号 | - |
| contact_phone | varchar(60) | 联系人电话 | - |
| price_coefficient | decimal(20,6) | 价格系数 | - |
| confirm_flag | tinyint(1) | 供应商确认标志 | - |
| feedback_status | varchar(30) | 反馈状态SSRC.RFX_FEEDBACK_STATUS(PARTICIPATED/参与&#124;ABANDONED/不参与&#124;NEW/未反馈) | INDEX |
| feedback_remark | longtext | 供应商报价状况备注 | - |
| abandon_remark | longtext | 放弃理由 | - |
| append_flag | tinyint(1) | 添加标识 | - |
| append_remark | longtext | 添加备注 | - |
| project_line_supplier_id | bigint(20) | 立项供应商行ID | INDEX |
| pr_line_supplier_id | bigint(20) | 申请供应商行ID | INDEX |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| supplier_company_num | varchar(60) | 供应商公司编码 | - |
| supplier_id | bigint(20) | 外部供应商Id:sslm_external_supplier.supplier_id | INDEX |
| offline_delete_flag | tinyint(1) | 线下删除标识 | - |

## 核心索引
- PRIMARY: `rf_line_supplier_id`
- INDEX: `idx_ssrc_rf_line_supplier_tenant_id` - (tenant_id)
- INDEX: `ssrc_rf_line_supplier_n2` - (rf_header_id)
- INDEX: `ssrc_rf_line_supplier_n3` - (supplier_tenant_id)
- INDEX: `ssrc_rf_line_supplier_n4` - (supplier_company_id)
- INDEX: `ssrc_rf_line_supplier_n5` - (supplier_contact_id)
- INDEX: `ssrc_rf_line_supplier_n6` - (feedback_status)
- INDEX: `ssrc_rf_line_supplier_n7` - (project_line_supplier_id)
- INDEX: `ssrc_rf_line_supplier_n8` - (pr_line_supplier_id)
- INDEX: `ssrc_rf_line_supplier_n9` - (supplier_id)
- INDEX: `ssrc_rf_line_supplier_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 征询单相关
- 通过 `rf_header_id` 关联征询单头表 `ssrc_rf_header`
- `ssrc_rf_item_sup_assign.rf_line_supplier_id` - 关联物料供应商分配表
- `ssrc_rf_quotation_header.rf_line_supplier_id` - 关联征询单报价头表

## 常见查询场景

### 1. 根据征询单ID查询供应商列表
```sql
SELECT rf_line_supplier_id, supplier_company_name, contact_name, feedback_status
FROM ssrc_rf_line_supplier
WHERE tenant_id = {tenant_id}
  AND rf_header_id = {rf_header_id};
```

### 2. 根据供应商公司ID查询征询单供应商信息
```sql
SELECT rf_line_supplier_id, rf_header_id, supplier_company_name, feedback_status
FROM ssrc_rf_line_supplier
WHERE tenant_id = {tenant_id}
  AND supplier_company_id = {supplier_company_id};
```

### 3. 查询征询单的报价头信息
```sql
SELECT rls.rf_line_supplier_id, rls.supplier_company_name, rqh.quotation_header_id, rqh.quotation_status
FROM ssrc_rf_line_supplier rls
INNER JOIN ssrc_rf_quotation_header rqh ON rls.rf_line_supplier_id = rqh.rf_line_supplier_id
WHERE rls.tenant_id = {tenant_id}
  AND rls.rf_header_id = {rf_header_id};
```

### 4. 查询征询单的物料供应商分配信息
```sql
SELECT rls.rf_line_supplier_id, rls.supplier_company_name, isa.rf_line_item_id, isa.max_limit_price
FROM ssrc_rf_line_supplier rls
INNER JOIN ssrc_rf_item_sup_assign isa ON rls.rf_line_supplier_id = isa.rf_line_supplier_id
WHERE rls.tenant_id = {tenant_id}
  AND rls.rf_header_id = {rf_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **征询单关联**：通过 `rf_header_id` 关联征询单头表
3. **供应商关联**：通过 `supplier_company_id` 关联公司信息表
4. **联系人关联**：通过 `supplier_contact_id` 关联供应商联系人
5. **反馈状态**：支持参与、不参与、未反馈三种状态
6. **外部供应商**：`supplier_id` 用于关联外部供应商系统
7. **立项关联**：通过 `project_line_supplier_id` 关联立项供应商行
