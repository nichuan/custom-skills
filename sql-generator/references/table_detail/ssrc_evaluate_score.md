# ssrc_evaluate_score 评分头表

## 表说明
评分头表，供应商维度。与报价单 `ssrc_rfx_quotation_header` 的 `quotation_header_id` 1对1关联。

## 字段列表

| 字段名 | 数据类型 | 说明 | 关联 |
|--------|----------|------|------|
| evaluate_score_id | bigint | 主键 | — |
| tenant_id | bigint | 租户ID | hpfm_tenant.tenant_id |
| source_header_id | bigint | 寻源单头id（询价单/招标单头id） | ssrc_rfx_header.rfx_header_id |
| source_from | varchar | 来源类型：RFX/BID | — |
| round_number | int | 轮次 | — |
| section_flag | tinyint | 标段标识 | — |
| section_id | bigint | 标段ID | ssrc_bid_line_item.bid_line_item_id |
| quotation_header_id | bigint | 报价头id（1对1） | ssrc_rfx_quotation_header.quotation_header_id |
| evaluate_expert_id | bigint | 专家评分行id | ssrc_evaluate_expert.evaluate_expert_id |
| score_status | varchar | 评分状态：NEW/未评分、SCORED/已评分、RESCORING/重新评分 | — |
| suggest_invalid_flag | tinyint | 建议无效：0/空=有效，1=无效 | — |
| sum_indic_score | decimal | 要素评分汇总 | — |
| expert_suggestion | longtext | 评审意见 | — |
| attachment_uuid | varchar | 专家评分附件UUID | — |
| sequence_num | tinyint | 组别序号 | — |
| evaluate_score_type | varchar | 评分类型 | — |
| review_attachment_uuid | varchar | 初步评审附件 | — |
| review_result | varchar | 初步评审结果：通过/不通过 | — |
| review_expert_suggestion | longtext | 初审评审意见 | — |
| expert_weight_sum_indic_score | decimal | 专家打分（含专家权重） | — |
| imported_flag | tinyint | 代录入标识 | — |
| object_version_number | bigint | 行版本号（乐观锁） | — |
| creation_date | datetime | 创建日期 | — |
| created_by | bigint | 创建人 | — |
| last_updated_by | bigint | 最后更新人 | — |
| last_update_date | datetime | 最后更新日期 | — |

## 常用查询示例

```sql
-- 查询某询价单的所有评分头（供应商维度）
SELECT *
FROM ssrc_evaluate_score
WHERE tenant_id = 155357
  AND source_from = 'RFX'
  AND source_header_id = 5923933;

-- 关联报价单查询评分状态
SELECT qh.supplier_company_name, es.score_status, es.sum_indic_score
FROM ssrc_evaluate_score es
JOIN ssrc_rfx_quotation_header qh ON es.quotation_header_id = qh.quotation_header_id
WHERE es.tenant_id = 155357
  AND es.source_from = 'RFX'
  AND es.source_header_id = 5923933;
```
