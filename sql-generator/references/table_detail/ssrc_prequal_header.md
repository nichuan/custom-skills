# ssrc_prequal_header 资格预审头表

## 表说明
资格预审头表，与询价单 `ssrc_rfx_header` 通过 `rfx_header_id` 关联。

## 字段列表

| 字段名 | 数据类型 | 说明 | 关联 |
|--------|----------|------|------|
| prequal_header_id | bigint | 主键 | — |
| tenant_id | bigint | 租户ID | hpfm_tenant.tenant_id |
| rfx_header_id | bigint | 询价单头ID | ssrc_rfx_header.rfx_header_id |
| prequal_end_date | datetime | 资格预审截止时间 | — |
| prequal_location | varchar | 申请提交地点 | — |
| review_method | varchar | 审查方式：QUALIFIED/合格制、LIMITED_QUANTITY/有限数量制 | — |
| qualified_limit | int | 合格上限 | — |
| file_free_flag | tinyint | 预审文件免费标志 | — |
| prequal_file_expense | decimal | 预审文件费 | — |
| prequal_remark | longtext | 预审备注 | — |
| enable_score_flag | tinyint | 启用评分标识 | — |
| prequal_attachment_uuid | varchar | 附件UUID | — |
| prequal_status | varchar | 资格预审状态：NO_APPROVED/未审批、APPROVED/已审批 | — |
| prequal_user_id | bigint | 资格预审人主键Id | — |
| approved_remark | longtext | 审批意见 | — |
| approved_date | datetime | 审批时间 | — |
| prequal_category | varchar | 审查类型：BID/招投标、RFX/询报价 | — |
| attachment_uuid | varchar | 资格预审附件UUID | — |
| manufacturer_type | varchar | 厂商类型 | — |
| message_flag | tinyint | 消息已发送标识：1=已发送，0=未发送 | — |
| object_version_number | bigint | 行版本号（乐观锁） | — |
| creation_date | datetime | 创建日期 | — |
| created_by | bigint | 创建人 | — |
| last_updated_by | bigint | 最后更新人 | — |
| last_update_date | datetime | 最后更新日期 | — |

## 常用查询示例

```sql
-- 查询某询价单的资格预审头信息
SELECT *
FROM ssrc_prequal_header
WHERE tenant_id = 155357
  AND rfx_header_id = 5923933;
```
