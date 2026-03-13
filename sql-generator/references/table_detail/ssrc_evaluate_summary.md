# ssrc_evaluate_summary 评分汇总表

## 表说明
评分汇总表，供应商维度。与报价单 `ssrc_rfx_quotation_header` 的 `quotation_header_id` 1对1关联，汇总各专家的评分结果。

## 字段列表

| 字段名 | 数据类型 | 说明 | 关联 |
|--------|----------|------|------|
| evaluate_summary_id | bigint | 主键 | — |
| tenant_id | bigint | 租户ID | hpfm_tenant.tenant_id |
| source_header_id | bigint | 招标头id | ssrc_rfx_header.rfx_header_id |
| source_from | varchar | 来源类型：RFX/BID | — |
| round_number | int | 轮次 | — |
| section_flag | tinyint | 标段标识 | — |
| section_id | bigint | 标段ID | ssrc_bid_line_item.bid_line_item_id |
| quotation_header_id | bigint | 报价头id（1对1） | ssrc_rfx_quotation_header.quotation_header_id |
| business_score | decimal | 商务组得分 | — |
| technology_score | decimal | 技术组得分 | — |
| score | decimal | 总分（商务总分*商务权重+技术总分*技术权重） | — |
| invalid_flag | tinyint | 无效投标：0=有效，1=无效 | — |
| invalid_reason | longtext | 无效投标原因 | — |
| candidate_flag | tinyint | 候选标识：0=不推荐，1=推荐 | — |
| candidate_suggestion | varchar | 候选推荐意见 | — |
| score_rank | int | 总分排名 | — |
| summary_status | varchar | 汇总状态：NEW/新建、SUBMITTED/已提交 | — |
| sequence_num | tinyint | 专家组别 | — |
| evaluate_summary_type | varchar | 汇总类型：REVIEW_SCORE/评审评分汇总、SCORE/评分汇总 | — |
| summary_review_result | varchar | 初审评审结果 | — |
| object_version_number | bigint | 行版本号（乐观锁） | — |
| creation_date | datetime | 创建日期 | — |
| created_by | bigint | 创建人 | — |
| last_updated_by | bigint | 最后更新人 | — |
| last_update_date | datetime | 最后更新日期 | — |

## 常用查询示例

```sql
-- 查询某询价单所有供应商评分汇总（含排名）
SELECT qh.supplier_company_name, esm.score, esm.score_rank,
       esm.candidate_flag, esm.invalid_flag
FROM ssrc_evaluate_summary esm
JOIN ssrc_rfx_quotation_header qh ON esm.quotation_header_id = qh.quotation_header_id
WHERE esm.tenant_id = 155357
  AND esm.source_from = 'RFX'
  AND esm.source_header_id = 5923933
ORDER BY esm.score_rank;
```
