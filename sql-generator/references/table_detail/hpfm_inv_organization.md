# hpfm_inv_organization - 库存组织表

## 表说明
库存组织表，存储系统中所有库存组织的基本信息。是SRM采购寻源系统的基础平台表之一，询价单、报价单等业务表通过 inv_organization_id 关联此表。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| organization_id | bigint(20) | 表ID，主键，供其他表做外键 | PRIMARY |
| organization_code | varchar(30) | 组织编码 | UNIQUE (organization_code, tenant_id) |
| organization_name | varchar(240) | 组织名称 | INDEX |
| ou_id | bigint(20) | 业务实体ID，hpfm_operation_unit.ou_id | INDEX |
| tenant_id | bigint(20) | 租户ID，hpfm_tenant.tenant_id | INDEX (idx_hpfm_inv_organization_tenant_id) |
| enabled_flag | tinyint(1) | 是否启用。1启用，0未启用 | - |
| source_code | varchar(30) | 数据来源 值集：HPFM.DATA_SOURCE | INDEX |
| external_system_code | varchar(30) | 外部来源系统代码 | INDEX |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| postal_code | varchar(30) | 邮编 | - |
| recipient_user_id | bigint(20) | 收货人 | - |
| recipient_phone | varchar(60) | 收货人电话 | - |
| international_tel_code | varchar(30) | 国际电话区号 | - |

## 核心索引
- PRIMARY: `organization_id`
- UNIQUE: `hpfm_inv_organization_u2` - (organization_code, tenant_id)
- INDEX: `idx_hpfm_inv_organization_tenant_id` - (tenant_id)
- INDEX: `hpfm_inv_organization_n2` - (ou_id)
- INDEX: `hpfm_inv_organization_n3` - (organization_name)
- INDEX: `hpfm_inv_organization_n4` - (source_code)
- INDEX: `hpfm_inv_organization_n5` - (external_system_code)
- INDEX: `hpfm_inv_organization_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表被多个核心业务表关联：

### 询价单相关
- `ssrc_rfx_line_item.inv_organization_id` - 关联询价单物料行的库存组织ID

### 报价单相关
- `ssrc_rfx_quotation_line.inv_organization_id` - 关联报价单行的库存组织ID

### 其他业务表
- 基本所有表里的 `invOrganizationId` 都会关联此表

## 常见查询场景

### 1. 根据组织编码查询库存组织信息
```sql
SELECT organization_id, organization_code, organization_name, ou_id
FROM hpfm_inv_organization
WHERE tenant_id = {tenant_id}
  AND organization_code = '{organization_code}';
```

### 2. 根据业务实体查询库存组织列表
```sql
SELECT organization_id, organization_code, organization_name
FROM hpfm_inv_organization
WHERE tenant_id = {tenant_id}
  AND ou_id = {ou_id}
  AND enabled_flag = 1;
```

### 3. 查询询价单物料行的库存组织信息
```sql
SELECT rli.rfx_line_item_id, rli.item_code, io.organization_name
FROM ssrc_rfx_line_item rli
INNER JOIN hpfm_inv_organization io ON rli.inv_organization_id = io.organization_id
WHERE rli.tenant_id = {tenant_id}
  AND rli.rfx_header_id = {rfx_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **唯一标识**：`(organization_code, tenant_id)` 组合唯一
3. **业务实体关联**：通过 `ou_id` 关联业务实体表
4. **启用标识**：`enabled_flag = 1` 表示启用状态
5. **外部系统**：`external_system_code` 用于标识外部来源系统
