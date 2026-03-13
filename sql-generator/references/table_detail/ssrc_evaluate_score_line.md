# ssrc_evaluate_score_line 评分行表

## 表说明
评分行表，存储所有专家给所有供应商的每个评分要素的打分明细。

## 字段列表

| 字段名 | 数据类型 | 说明 | 关联 |
|--------|----------|------|------|
| evaluate_line_id | bigint | 主键 | — |
| tenant_id | bigint | 租户ID | hpfm_tenant.tenant_id |
| evaluate_score_id | bigint | 评分头id | ssrc_evaluate_score.evaluate_score_id |
| evaluate_indic_id | bigint | 评分要素id | ssrc_evaluate_indic.evaluate_indic_id |
| indic_score | decimal | 评分要素得分 | — |
| remark | varchar | 备注 | — |
| pass_status | varchar | 通过制打分结果：NO_APPROVED/审批不通过、APPROVED/审批通过 | — |
| expert_weight_indic_score | decimal | 专家权重得分（expert_weight * indic_score） | — |
| object_version_number | bigint | 行版本号（乐观锁） | — |
| creation_date | datetime | 创建日期 | — |
| created_by | bigint | 创建人 | — |
| last_updated_by | bigint | 最后更新人 | — |
| last_update_date | datetime | 最后更新日期 | — |

## 常用查询示例

```sql
-- 查询某询价单的所有评分行（需先获取 evaluate_score_id）
SELECT esl.*
FROM ssrc_evaluate_score_line esl
JOIN ssrc_evaluate_score es ON esl.evaluate_score_id = es.evaluate_score_id
WHERE es.tenant_id = 155357
  AND es.source_from = 'RFX'
  AND es.source_header_id = 5923933;

-- 查询某供应商所有要素得分
SELECT ei.indicate_name, esl.indic_score, esl.expert_weight_indic_score
FROM ssrc_evaluate_score_line esl
JOIN ssrc_evaluate_indic ei ON esl.evaluate_indic_id = ei.evaluate_indic_id
WHERE esl.evaluate_score_id IN (
    SELECT evaluate_score_id FROM ssrc_evaluate_score
    WHERE quotation_header_id = ?
      AND tenant_id = 155357
);
```
