# hpfm_purchase_agent - 采购员表

## 表说明
采购员表，存储系统中所有采购员的基本信息。是SRM采购寻源系统的基础平台表之一，询价单等业务表通过 pur_agent_id 关联此表。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| purchase_agent_id | bigint(20) | 表ID，主键，供其他表做外键 | PRIMARY |
| tenant_id | bigint(20) | 租户ID，hpfm_tenant.tenant_id | INDEX (idx_hpfm_purchase_agent_tenant_id) |
| purchase_org_id | bigint(20) | 采购组织ID，hpfm_purchase_organization.purchase_org_id | INDEX |
| purchase_agent_code | varchar(30) | 平台编码 | UNIQUE (purchase_agent_code, tenant_id) |
| purchase_agent_name | varchar(240) | 采购员名称 | INDEX |
| contact_info | varchar(500) | 联系方式 | - |
| source_code | varchar(30) | 数据来源 值集：HPFM.DATA_SOURCE | INDEX |
| enabled_flag | tinyint(1) | 是否启用。1启用，0未启用 | - |
| external_system_code | varchar(30) | 外部来源系统代码 | INDEX |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |

## 核心索引
- PRIMARY: `purchase_agent_id`
- UNIQUE: `hpfm_purchase_agent_u2` - (purchase_agent_code, tenant_id)
- INDEX: `idx_hpfm_purchase_agent_tenant_id` - (tenant_id)
- INDEX: `hpfm_purchase_agent_n2` - (purchase_org_id)
- INDEX: `hpfm_purchase_agent_n3` - (purchase_agent_name)
- INDEX: `hpfm_purchase_agent_n4` - (source_code)
- INDEX: `hpfm_purchase_agent_n5` - (external_system_code)
- INDEX: `hpfm_purchase_agent_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表被多个核心业务表关联：

### 询价单相关
- `ssrc_rfx_header.pur_agent_id` - 关联询价单的采购员ID

### 其他业务表
- 基本所有表里的 `purAgentId` 都会关联此表

## 常见查询场景

### 1. 根据采购员编码查询采购员信息
```sql
SELECT purchase_agent_id, purchase_agent_code, purchase_agent_name, contact_info
FROM hpfm_purchase_agent
WHERE tenant_id = {tenant_id}
  AND purchase_agent_code = '{purchase_agent_code}';
```

### 2. 根据采购组织查询采购员列表
```sql
SELECT purchase_agent_id, purchase_agent_code, purchase_agent_name
FROM hpfm_purchase_agent
WHERE tenant_id = {tenant_id}
  AND purchase_org_id = {purchase_org_id}
  AND enabled_flag = 1;
```

### 3. 查询询价单的采购员信息
```sql
SELECT rfx.rfx_num, rfx.rfx_title, pa.purchase_agent_name, pa.contact_info
FROM ssrc_rfx_header rfx
INNER JOIN hpfm_purchase_agent pa ON rfx.pur_agent_id = pa.purchase_agent_id
WHERE rfx.tenant_id = {tenant_id}
  AND rfx.rfx_header_id = {rfx_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **唯一标识**：`(purchase_agent_code, tenant_id)` 组合唯一
3. **采购组织关联**：通过 `purchase_org_id` 关联采购组织表
4. **启用标识**：`enabled_flag = 1` 表示启用状态
5. **外部系统**：`external_system_code` 用于标识外部来源系统
