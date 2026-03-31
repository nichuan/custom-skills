# ssrc_rf_action - 征询单操作记录表

## 表说明
征询单操作记录表，存储征询单（RFI/RFP）的操作历史记录。是SRM采购寻源系统的核心业务表之一，记录征询单的审批、发布等操作轨迹。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| rf_action_id | bigint(20) | 主键，操作记录ID | PRIMARY |
| rf_header_id | bigint(20) | 来源ID，征询单头ID | INDEX |
| tenant_id | bigint(20) | 租户ID | INDEX (idx_ssrc_rf_action_tenant_id) |
| processed_by | bigint(20) | 处理人 | INDEX |
| processed_status | varchar(30) | 处理时单据状态 | - |
| processed_operation | varchar(30) | 对应操作 | - |
| processed_date | datetime | 处理日期 | INDEX |
| processed_remark | varchar(500) | 处理内容 | - |
| process_flag | tinyint(1) | 流程标志 | - |
| process_system_code | varchar(30) | 流程运行系统 SRM/OA/SAP/ERP | - |
| process_inst_id | varchar(60) | 流程Id | INDEX |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| source_node | varchar(30) | 操作节点 | - |
| deliver_from_user_id | bigint(20) | 单据转交从 | INDEX |
| deliver_to_user_id | bigint(20) | 单据转交至 | INDEX |
| expand_param | longtext | 扩展参数 | - |

## 核心索引
- PRIMARY: `rf_action_id`
- INDEX: `idx_ssrc_rf_action_tenant_id` - (tenant_id)
- INDEX: `ssrc_rf_action_n2` - (rf_header_id)
- INDEX: `ssrc_rf_action_n3` - (processed_by)
- INDEX: `ssrc_rf_action_n4` - (processed_date)
- INDEX: `ssrc_rf_action_n5` - (process_inst_id)
- INDEX: `ssrc_rf_action_n6` - (deliver_from_user_id)
- INDEX: `ssrc_rf_action_n7` - (deliver_to_user_id)
- INDEX: `ssrc_rf_action_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 征询单相关
- 通过 `rf_header_id` 关联征询单头表 `ssrc_rf_header`

## 常见查询场景

### 1. 根据征询单ID查询操作记录列表
```sql
SELECT rf_action_id, processed_by, processed_status, processed_operation, processed_date
FROM ssrc_rf_action
WHERE tenant_id = {tenant_id}
  AND rf_header_id = {rf_header_id}
ORDER BY processed_date DESC;
```

### 2. 根据处理人查询操作记录
```sql
SELECT rf_action_id, rf_header_id, processed_status, processed_operation, processed_date
FROM ssrc_rf_action
WHERE tenant_id = {tenant_id}
  AND processed_by = {processed_by}
ORDER BY processed_date DESC;
```

### 3. 查询征询单的审批操作记录
```sql
SELECT rf_action_id, processed_by, processed_status, processed_operation, processed_date, processed_remark
FROM ssrc_rf_action
WHERE tenant_id = {tenant_id}
  AND rf_header_id = {rf_header_id}
  AND processed_operation LIKE '%APPROVE%'
ORDER BY processed_date DESC;
```

### 4. 查询征询单的转交记录
```sql
SELECT rf_action_id, deliver_from_user_id, deliver_to_user_id, processed_date
FROM ssrc_rf_action
WHERE tenant_id = {tenant_id}
  AND rf_header_id = {rf_header_id}
  AND deliver_from_user_id IS NOT NULL
ORDER BY processed_date DESC;
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **征询单关联**：通过 `rf_header_id` 关联征询单头表
3. **操作轨迹**：记录征询单的完整操作历史
4. **流程集成**：支持与外部流程系统（OA/SAP/ERP）集成
5. **单据转交**：支持记录单据在不同处理人之间的转交操作
