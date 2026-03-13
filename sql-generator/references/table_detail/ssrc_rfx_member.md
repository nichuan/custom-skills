# ssrc_rfx_member 表详细结构

询价单寻源小组成员表

## 表信息
- **表名**: ssrc_rfx_member
- **主键**: rfx_member_id
- **外键**: rfx_header_id（关联 ssrc_rfx_header.rfx_header_id），1:N 关系
- **说明**: 存储询价单的寻源小组成员，包含各角色（询价员、核价员、开标人等）

## 字段详情

| 字段名                 | 数据类型  | 说明                                                                                    |
|-----------------------|-----------|----------------------------------------------------------------------------------------|
| rfx_member_id         | bigint    | 成员行ID（主键）                                                                        |
| rfx_header_id         | bigint    | 询价单头ID                                                                              |
| tenant_id             | bigint    | 租户ID                                                                                  |
| rfx_role              | varchar   | 询价角色（SSRC.RFX_ROLE）：CHECKED_BY/核价员、PRETRIAL_BY/预审审查员、RFX_BY/询价员、OPENED_BY/开标人 |
| user_id               | bigint    | 用户ID                                                                                  |
| password_flag         | tinyint   | 开启开标密码标识                                                                        |
| open_password         | varchar   | 开标密码                                                                                |
| opened_flag           | tinyint   | 已开标标识                                                                              |
| second_opened_flag    | tinyint   | 二阶段已开标标识                                                                        |
| send_flag             | tinyint   | 发送标识                                                                                |
| opener_pending_status | varchar   | 开标人开标状态：NOT_START/未开始、OPEN_PENDING/待开标、OPENED/已开标                    |
| object_version_number | bigint    | 行版本号，用来处理锁                                                                    |
| creation_date         | datetime  | 创建日期                                                                                |
| last_update_date      | datetime  | 最后更新日期                                                                            |

## 常用查询

### 查询询价单寻源小组成员
```sql
SELECT * FROM ssrc_rfx_member
WHERE tenant_id = 155357 AND rfx_header_id = 5923933;
```

### 查询询价单指定角色成员
```sql
-- 查询询价员
SELECT m.rfx_member_id, m.rfx_role, m.user_id, u.login_name, u.real_name
FROM ssrc_rfx_member m
JOIN iam_user u ON m.user_id = u.id
WHERE m.tenant_id = 155357
  AND m.rfx_header_id = 5923933
  AND m.rfx_role = 'RFX_BY';
```

### 查询核价员
```sql
SELECT m.user_id, u.login_name, u.real_name
FROM ssrc_rfx_member m
JOIN iam_user u ON m.user_id = u.id
WHERE m.tenant_id = 155357
  AND m.rfx_header_id = 5923933
  AND m.rfx_role = 'CHECKED_BY';
```
