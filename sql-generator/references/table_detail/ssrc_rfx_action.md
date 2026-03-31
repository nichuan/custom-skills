# ssrc_rfx_action - 询价单操作记录表

## 表说明
询价单操作记录表，存储询价单的操作历史记录。是SRM采购寻源系统的核心业务表之一，记录询价单的审批、发布、核价等操作轨迹。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| rfx_action_id | bigint(20) | 主键，操作记录ID | PRIMARY |
| rfx_header_id | bigint(20) | 发票头ID | INDEX |
| tenant_id | bigint(20) | 租户ID | INDEX (idx_ssrc_rfx_action_tenant_id) |
| process_user_id | bigint(20) | 处理人 | INDEX |
| process_status | varchar(30) | 询价单状态SSRC.RFX_STATUS | - |
| process_date | datetime | 处理日期 | INDEX |
| process_remark | longtext | 处理消息 | - |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| process_operation | varchar(30) | 询价单操作SSRC.RFX_OPERATION | - |
| deliver_from_user_id | bigint(20) | 单据转交从 | INDEX |
| deliver_to_user_id | bigint(20) | 单据转交至 | INDEX |
| process_type | varchar(30) | 流程名称SSRC.RFX_PROCESS_TYPE | - |
| process_system_code | varchar(30) | 流程运行系统SRM/OA/SAP/ERP | - |
| source_node | varchar(30) | 操作节点 | - |
| expand_param | longtext | 扩展参数 | - |
| process_attachment_uuid | varchar(60) | 处理附件信息 | - |
| process_external_remark | longtext | 处理外部理由 | - |

## 核心索引
- PRIMARY: `rfx_action_id`
- INDEX: `idx_ssrc_rfx_action_tenant_id` - (tenant_id)
- INDEX: `ssrc_rfx_action_n2` - (rfx_header_id)
- INDEX: `ssrc_rfx_action_n3` - (process_user_id)
- INDEX: `ssrc_rfx_action_n4` - (process_date)
- INDEX: `ssrc_rfx_action_n5` - (deliver_from_user_id)
- INDEX: `ssrc_rfx_action_n6` - (deliver_to_user_id)
- INDEX: `ssrc_rfx_action_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 询价单相关
- 通过 `rfx_header_id` 关联询价单头表 `ssrc_rfx_header`

## 常见查询场景

### 1. 根据询价单ID查询操作记录列表
```sql
SELECT rfx_action_id, process_user_id, process_status, process_operation, process_date
FROM ssrc_rfx_action
WHERE tenant_id = {tenant_id}
  AND rfx_header_id = {rfx_header_id}
ORDER BY process_date DESC;
```

### 2. 根据处理人查询操作记录
```sql
SELECT rfx_action_id, rfx_header_id, process_status, process_operation, process_date
FROM ssrc_rfx_action
WHERE tenant_id = {tenant_id}
  AND process_user_id = {process_user_id}
ORDER BY process_date DESC;
```

### 3. 查询询价单的审批操作记录
```sql
SELECT rfx_action_id, process_user_id, process_status, process_operation, process_date, process_remark
FROM ssrc_rfx_action
WHERE tenant_id = {tenant_id}
  AND rfx_header_id = {rfx_header_id}
  AND process_operation LIKE '%APPROVE%'
ORDER BY process_date DESC;
```

### 4. 查询询价单的转交记录
```sql
SELECT rfx_action_id, deliver_from_user_id, deliver_to_user_id, process_date
FROM ssrc_rfx_action
WHERE tenant_id = {tenant_id}
  AND rfx_header_id = {rfx_header_id}
  AND deliver_from_user_id IS NOT NULL
ORDER BY process_date DESC;
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **询价单关联**：通过 `rfx_header_id` 关联询价单头表
3. **操作轨迹**：记录询价单的完整操作历史
4. **流程集成**：支持与外部流程系统（OA/SAP/ERP）集成
5. **单据转交**：支持记录单据在不同处理人之间的转交操作
6. **附件支持**：支持处理附件信息的记录
