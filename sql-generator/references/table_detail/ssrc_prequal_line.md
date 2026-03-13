# ssrc_prequal_line 资格预审行表

## 表说明
资格预审行表，与供应商关联（1对1），存储各供应商的资格预审申请信息。

## 字段列表

| 字段名 | 数据类型 | 说明 | 关联 |
|--------|----------|------|------|
| prequal_line_id | bigint | 主键 | — |
| tenant_id | bigint | 租户ID | hpfm_tenant.tenant_id |
| prequal_header_id | bigint | 资格预审头ID | ssrc_prequal_header.prequal_header_id |
| supplier_tenant_id | bigint | 供应商租户ID | — |
| supplier_company_id | bigint | 供应方企业ID | — |
| application_remark | varchar | 资格预审申请说明 | — |
| current_attachment_uuid | varchar | 当前附件UUID | — |
| valid_attachment_uuid | varchar | 有效附件UUID | — |
| prequal_line_status | varchar | 资格预审行状态：NEW/未提交、SUBMITED/已提交、APPROVED/已通过、REFUSED/未通过 | — |
| line_approved_status | varchar | 审批通过状态：NO_APPROVED/审批不通过、APPROVED/审批通过 | — |
| approved_remark | longtext | 审批意见 | — |
| approved_date | datetime | 审批日期 | — |
| payment_flag | tinyint | 付费标记 | — |
| user_id | bigint | 资审成员用户id | — |
| return_remark | longtext | 退回说明 | — |
| object_version_number | bigint | 行版本号（乐观锁） | — |
| creation_date | datetime | 创建日期 | — |
| created_by | bigint | 创建人 | — |
| last_updated_by | bigint | 最后更新人 | — |
| last_update_date | datetime | 最后更新日期 | — |

## 常用查询示例

```sql
-- 查询某资格预审头下所有供应商的预审行状态
SELECT pl.supplier_company_id, pl.prequal_line_status, pl.line_approved_status
FROM ssrc_prequal_line pl
WHERE pl.tenant_id = 155357
  AND pl.prequal_header_id = ?;  -- 替换为实际的 prequal_header_id

-- 通过询价单ID查询资格预审行
SELECT pl.*
FROM ssrc_prequal_line pl
JOIN ssrc_prequal_header ph ON pl.prequal_header_id = ph.prequal_header_id
WHERE ph.tenant_id = 155357
  AND ph.rfx_header_id = 5923933;
```
