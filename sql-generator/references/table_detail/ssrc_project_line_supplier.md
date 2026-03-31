# ssrc_project_line_supplier - 寻源立项供应商行表

## 表说明
寻源立项供应商行表，存储寻源立项单的供应商信息。是SRM采购寻源系统的核心业务表之一，记录寻源立项邀请的供应商列表。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| project_line_supplier_id | bigint(20) | 主键，供应商行ID | PRIMARY |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_project_line_supplier_tenant_id) |
| source_project_id | bigint(20) | 寻源立项id | INDEX |
| supplier_tenant_id | bigint(20) | 供应商租户ID | INDEX |
| supplier_company_id | bigint(20) | 供应商公司ID | INDEX |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| supplier_category_code | longtext | 供应商分类编码 | - |
| supplier_category_description | longtext | 供应商分类描述 | - |
| supplier_contact_id | bigint(20) | 供应商联系人ID | INDEX |
| contact_name | varchar(120) | 联系人姓名 | - |
| contact_mail | varchar(240) | 联系人邮箱 | - |
| international_tel_code | varchar(30) | 供应商联系电话-国际电话区号 | - |
| contact_mobilephone | varchar(60) | 联系人手机号 | - |
| supplier_id | bigint(20) | 外部供应商Id:sslm_external_supplier.supplier_id | INDEX |

## 核心索引
- PRIMARY: `project_line_supplier_id`
- INDEX: `idx_ssrc_project_line_supplier_tenant_id` - (tenant_id)
- INDEX: `ssrc_project_line_supplier_n2` - (source_project_id)
- INDEX: `ssrc_project_line_supplier_n3` - (supplier_tenant_id)
- INDEX: `ssrc_project_line_supplier_n4` - (supplier_company_id)
- INDEX: `ssrc_project_line_supplier_n5` - (supplier_contact_id)
- INDEX: `ssrc_project_line_supplier_n6` - (supplier_id)
- INDEX: `ssrc_project_line_supplier_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 询价单相关
- `ssrc_rfx_line_supplier.project_line_supplier_id` - 关联询价单供应商行的立项供应商行ID

### 其他业务表
- 通过 `source_project_id` 关联寻源立项头表
- 通过 `supplier_company_id` 关联公司信息表
- 通过 `supplier_contact_id` 关联供应商联系人

## 常见查询场景

### 1. 根据寻源立项ID查询供应商列表
```sql
SELECT project_line_supplier_id, supplier_company_id, supplier_company_name, contact_name
FROM ssrc_project_line_supplier
WHERE tenant_id = {tenant_id}
  AND source_project_id = {source_project_id};
```

### 2. 根据供应商公司ID查询立项供应商信息
```sql
SELECT project_line_supplier_id, source_project_id, supplier_company_name
FROM ssrc_project_line_supplier
WHERE tenant_id = {tenant_id}
  AND supplier_company_id = {supplier_company_id};
```

### 3. 查询询价单关联的立项供应商信息
```sql
SELECT rls.rfx_line_supplier_id, rls.supplier_company_name, pls.contact_name, pls.contact_mail
FROM ssrc_rfx_line_supplier rls
INNER JOIN ssrc_project_line_supplier pls ON rls.project_line_supplier_id = pls.project_line_supplier_id
WHERE rls.tenant_id = {tenant_id}
  AND rls.rfx_header_id = {rfx_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **寻源立项关联**：通过 `source_project_id` 关联寻源立项头表
3. **供应商关联**：通过 `supplier_company_id` 关联公司信息表
4. **联系人关联**：通过 `supplier_contact_id` 关联供应商联系人
5. **外部供应商**：`supplier_id` 用于关联外部供应商系统
