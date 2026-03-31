# hpfm_purchase_organization - 采购组织表

## 表说明
采购组织表，存储系统中所有采购组织的基本信息。是SRM采购寻源系统的基础平台表之一，询价单等业务表通过 pur_organization_id 关联此表。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| purchase_org_id | bigint(20) | 主键，采购组织ID | PRIMARY |
| tenant_id | bigint(20) | 租户ID，hpfm_tenant.tenant_id | INDEX (idx_hpfm_purchase_organization_tenant_id) |
| organization_code | varchar(30) | 采购组织编码 | UNIQUE (organization_code, tenant_id) |
| organization_name | varchar(240) | 采购组织名称 | INDEX |
| source_code | varchar(30) | 数据来源，值集：HPFM.DATA_SOURCE | INDEX |
| enabled_flag | tinyint(1) | 是否启用。1启用，0未启用 | - |
| external_system_code | varchar(30) | 外部来源系统代码 | INDEX |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |

## 核心索引
- PRIMARY: `purchase_org_id`
- UNIQUE: `hpfm_purchase_organization_u2` - (organization_code, tenant_id)
- INDEX: `idx_hpfm_purchase_organization_tenant_id` - (tenant_id)
- INDEX: `hpfm_purchase_organization_n2` - (organization_name)
- INDEX: `hpfm_purchase_organization_n3` - (source_code)
- INDEX: `hpfm_purchase_organization_n4` - (external_system_code)
- INDEX: `hpfm_purchase_organization_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表被多个核心业务表关联：

### 询价单相关
- `ssrc_rfx_header.pur_organization_id` - 关联询价单的采购组织ID

### 其他业务表
- 基本所有表里的 `purOrganizationId` 都会关联此表

## 常见查询场景

### 1. 根据采购组织编码查询采购组织信息
```sql
SELECT purchase_org_id, organization_code, organization_name
FROM hpfm_purchase_organization
WHERE tenant_id = {tenant_id}
  AND organization_code = '{organization_code}';
```

### 2. 查询所有启用的采购组织
```sql
SELECT purchase_org_id, organization_code, organization_name
FROM hpfm_purchase_organization
WHERE tenant_id = {tenant_id}
  AND enabled_flag = 1
ORDER BY organization_code;
```

### 3. 查询询价单的采购组织信息
```sql
SELECT rfx.rfx_num, rfx.rfx_title, po.organization_name, po.organization_code
FROM ssrc_rfx_header rfx
INNER JOIN hpfm_purchase_organization po ON rfx.pur_organization_id = po.purchase_org_id
WHERE rfx.tenant_id = {tenant_id}
  AND rfx.rfx_header_id = {rfx_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **唯一标识**：`(organization_code, tenant_id)` 组合唯一
3. **启用标识**：`enabled_flag = 1` 表示启用状态
4. **外部系统**：`external_system_code` 用于标识外部来源系统
