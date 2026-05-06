# spfm_pending_message 延时消息表

## 表基本信息

| 属性 | 说明 |
|------|------|
| 表名 | spfm_pending_message |
| 说明 | 延时消息表，用于在指定时间点执行异步任务 |
| 主键 | pending_message_id |

## 字段结构

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| pending_message_id | bigint | 消息ID | 主键 |
| tenant_id | bigint | 租户ID | |
| biz_id | bigint | 业务ID | 如询价单的 rfx_header_id |
| biz_type | varchar(50) | 业务类型 | 如 'RFX' 表示询价单 |
| server_name | varchar(100) | 服务名称 | 如 'srm-source' |
| execute_type | varchar(100) | 执行类型 | 如 'QUOTATION_END_REFRESH_RFX_STATUS' |
| execute_time | datetime | 执行时间 | 延时消息的执行时间点 |
| executed_flag | varchar(1) | 执行标志 | '0' 未执行，'1' 已执行 |
| expand_param | text | 扩展参数 | JSON格式的扩展参数 |
| adaptor_code | varchar(100) | 适配器编码 | 可为空 |
| object_version_number | bigint | 对象版本号 | 用于乐观锁 |
| creation_date | datetime | 创建时间 | |
| created_by | bigint | 创建人ID | |
| last_update_date | datetime | 最后更新时间 | |
| last_updated_by | bigint | 最后更新人ID | |

## 业务场景

### 询价单报价截止时间刷新

当询价单状态回退至"报价中"(IN_QUOTATION)时，需要插入一条延时消息，确保在报价截止时间到达后系统能自动刷新询价单状态。

**使用场景**:
- 核价回退至报价中
- 评分回退至报价中
- 修复询价单报价截止时间

**插入规则**:

```sql
INSERT INTO spfm_pending_message (tenant_id, biz_id, biz_type, server_name, execute_type, execute_time,
                                  executed_flag, expand_param, object_version_number, creation_date,
                                  created_by, last_updated_by, last_update_date, adaptor_code)
VALUES ({tenant_id}, {rfx_header_id}, 'RFX', 'srm-source', 'QUOTATION_END_REFRESH_RFX_STATUS', '{new_end_date}', '0',
        null, '1', now(), {user_id}, {user_id}, now(), null);
```

**字段值说明**:

| 字段 | 值 | 说明 |
|------|-----|------|
| biz_id | {rfx_header_id} | 询价单头ID |
| biz_type | 'RFX' | 固定值，表示询价单业务 |
| server_name | 'srm-source' | 固定值，表示SRM寻源服务 |
| execute_type | 'QUOTATION_END_REFRESH_RFX_STATUS' | 固定值，报价截止刷新 |
| execute_time | {new_end_date} | 新的报价截止时间 |
| executed_flag | '0' | 未执行 |
| expand_param | null | 无扩展参数 |
| object_version_number | '1' | 固定版本号 |
| adaptor_code | null | 无适配器 |

## 关联关系

| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| ssrc_rfx_header | rfx_header_id | spfm_pending_message | biz_id | 询价单与延时消息，通过 biz_type='RFX' 区分 |
