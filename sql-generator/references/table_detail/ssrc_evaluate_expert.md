# ssrc_evaluate_expert 表详细结构

评分专家表

## 表信息
- **表名**: ssrc_evaluate_expert
- **主键**: evaluate_expert_id
- **关联字段**: source_header_id（关联 ssrc_rfx_header.rfx_header_id 或招标单头ID）
- **说明**: 存储询价单/招标单的评分专家信息，一个寻源单可以有多个专家

## 字段详情

| 字段名                  | 数据类型  | 说明                                                                                           |
|------------------------|-----------|-----------------------------------------------------------------------------------------------|
| evaluate_expert_id     | bigint    | 评分专家行ID（主键）                                                                           |
| tenant_id              | bigint    | 租户ID                                                                                         |
| source_header_id       | bigint    | 寻源单头ID（询价单头ID/招标单头ID）                                                            |
| source_from            | varchar   | 来源类型：RFX/询价、BID/招标                                                                   |
| expert_id              | bigint    | 专家ID                                                                                         |
| expert_user_id         | bigint    | 专家子账户ID（关联 iam_user.id）                                                               |
| expert_from            | varchar   | 专家来源：EXPERT_EXTRACT/专家抽取、MANUAL/手工维护                                             |
| leader_flag            | tinyint   | 组长标识                                                                                       |
| evaluate_leader_flag   | tinyint   | 评标负责人标识                                                                                 |
| team                   | varchar   | 专家组别（SSRC.EXPERT_CATEGORY）：BUSINESS/商务组、TECHNOLOGY/技术组、BUSINESS_TECHNOLOGY/商务技术组 |
| sequence_num           | tinyint   | 组别序号                                                                                       |
| expert_status          | varchar   | 专家状态：NEW/新建、SUBMITTED/已提交、APPROVED/审批通过、REFUSED/审批拒绝                       |
| scored_status          | varchar   | 评分状态（SSRC.BID_EVALUATE_STAUTS）：NEW/未评分、SCORED/已评分、RESCORING/重新评分            |
| expert_pending_status  | varchar   | 专家待办状态：NOT_START/未开始、SCORE_PENDING/待评分、SCORED/已评分、RESCORING/重新评分        |
| review_scored_status   | varchar   | 初审评审评分状态：NEW/未评分、SCORED/已评分                                                    |
| start_date             | datetime  | 开始日期                                                                                       |
| end_date               | datetime  | 评分提醒截止时间                                                                               |
| end_date_changed_flag  | tinyint   | 评分提醒截止时间改动标识：0未改动、1改动                                                       |
| attachment_uuid        | varchar   | 专家评分整单头附件UUID                                                                         |
| object_version_number  | bigint    | 行版本号，用来处理锁                                                                           |
| creation_date          | datetime  | 创建日期                                                                                       |
| last_update_date       | datetime  | 最后更新日期                                                                                   |

## 常用查询

### 查询询价单评分专家信息（含用户信息）
```sql
SELECT
    see.evaluate_expert_id,
    iu.login_name,
    iu.real_name,
    see.team,
    see.sequence_num,
    see.expert_user_id,
    see.expert_status,
    see.scored_status
FROM ssrc_evaluate_expert see
JOIN iam_user iu ON see.expert_user_id = iu.id
WHERE see.source_header_id = 5923933
  AND see.source_from = 'RFX'
  AND see.tenant_id = 155357;
```

### 查询已评分的专家
```sql
SELECT * FROM ssrc_evaluate_expert
WHERE tenant_id = 155357
  AND source_header_id = 5923933
  AND source_from = 'RFX'
  AND scored_status = 'SCORED';
```

### 按组别统计专家
```sql
SELECT team, COUNT(*) AS cnt, 
       SUM(CASE WHEN scored_status='SCORED' THEN 1 ELSE 0 END) AS scored_cnt
FROM ssrc_evaluate_expert
WHERE tenant_id = 155357
  AND source_header_id = 5923933
  AND source_from = 'RFX'
GROUP BY team;
```
