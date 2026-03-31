# ssrc_rf_template - 征询单模板表

## 表说明
征询单模板表，存储征询单（RFI/RFP）的模板信息。是SRM采购寻源系统的核心业务表之一，用于快速创建征询单。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| template_id | bigint(20) | 主键，模板ID | PRIMARY |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_rf_template_tenant_id) |
| template_num | varchar(60) | 模板编号 | UNIQUE (template_num, tenant_id) |
| template_name | varchar(240) | 模板名称 | INDEX |
| template_status | varchar(30) | 模板状态SSRC.SOURCE_TEMPLATE_STATUS(PENDING/待发布&#124;RELEASED/已发布) | INDEX |
| version_number | int(11) | 版本 | - |
| latest_flag | varchar(10) | 模板标志(P/父模板&#124;Y/最新模板&#124;N/历史模板) | - |
| source_category | varchar(30) | 寻源类别(RFI/信息征询书&#124;RFP/方案征询书) | INDEX |
| source_method | varchar(30) | 询价方式SSRC.SOURCE_METHOD(INVITE/邀请&#124;OPEN/合作伙伴公开&#124;ALL_OPEN/全平台公开) | - |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| source_template_id | bigint(20) | 关联的寻源模板id | INDEX |
| system_version | tinyint(4) | 老的寻源模版定义菜单是1,新的寻源模版工作台是2 | - |
| release_date | datetime | 寻源模板发布时间 | INDEX |
| last_template_status | varchar(30) | 上一次状态SSRC.SOURCE_TEMPLATE_STATUS：（PENDING/待发布&#124;RELEASED/已发布） | - |
| source_nodes | varchar(500) | 节点信息 | - |

## 核心索引
- PRIMARY: `template_id`
- UNIQUE: `ssrc_rf_template_u2` - (template_num, tenant_id)
- INDEX: `idx_ssrc_rf_template_tenant_id` - (tenant_id)
- INDEX: `ssrc_rf_template_n2` - (template_name)
- INDEX: `ssrc_rf_template_n3` - (template_status)
- INDEX: `ssrc_rf_template_n4` - (source_category)
- INDEX: `ssrc_rf_template_n5` - (source_template_id)
- INDEX: `ssrc_rf_template_n6` - (release_date)
- INDEX: `ssrc_rf_template_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 征询单相关
- `ssrc_rf_header.template_id` - 关联征询单头表

## 常见查询场景

### 1. 根据模板编号查询模板信息
```sql
SELECT template_id, template_num, template_name, template_status, source_category
FROM ssrc_rf_template
WHERE tenant_id = {tenant_id}
  AND template_num = '{template_num}';
```

### 2. 查询所有已发布的征询单模板
```sql
SELECT template_id, template_num, template_name, source_category, source_method
FROM ssrc_rf_template
WHERE tenant_id = {tenant_id}
  AND template_status = 'RELEASED'
  AND latest_flag = 'Y'
ORDER BY template_name;
```

### 3. 根据寻源类别查询模板列表
```sql
SELECT template_id, template_num, template_name, source_method
FROM ssrc_rf_template
WHERE tenant_id = {tenant_id}
  AND source_category = '{source_category}'
  AND template_status = 'RELEASED'
  AND latest_flag = 'Y'
ORDER BY template_name;
```

### 4. 查询征询单使用的模板信息
```sql
SELECT rf.rf_num, rf.rf_title, rft.template_num, rft.template_name
FROM ssrc_rf_header rf
INNER JOIN ssrc_rf_template rft ON rf.template_id = rft.template_id
WHERE rf.tenant_id = {tenant_id}
  AND rf.rf_header_id = {rf_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **唯一标识**：`(template_num, tenant_id)` 组合唯一
3. **版本管理**：支持模板的版本管理，`latest_flag` 标识最新版本
4. **状态管理**：支持待发布、已发布等状态
5. **寻源类别**：支持RFI（信息征询书）和RFP（方案征询书）
6. **询价方式**：支持邀请、合作伙伴公开、全平台公开三种方式
7. **寻源模板关联**：支持关联寻源模板
