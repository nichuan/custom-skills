# ssrc_evaluate_indic 表详细结构

评分要素表

## 表信息
- **表名**: ssrc_evaluate_indic
- **主键**: evaluate_indic_id
- **关联字段**: source_header_id（关联 ssrc_rfx_header.rfx_header_id）
- **说明**: 存储询价单/招标单的评分要素配置，定义了评什么、怎么评、多少分

## 字段详情

| 字段名                | 数据类型  | 说明                                                                                         |
|----------------------|-----------|----------------------------------------------------------------------------------------------|
| evaluate_indic_id    | bigint    | 评分要素ID（主键）                                                                           |
| tenant_id            | bigint    | 租户ID                                                                                       |
| source_header_id     | bigint    | 寻源单头ID                                                                                   |
| source_from          | varchar   | 来源类型：RFX/询价、BID/招标                                                                 |
| indicate_id          | bigint    | 要素ID                                                                                       |
| indicate_code        | varchar   | 要素code                                                                                     |
| indicate_name        | varchar   | 要素名称                                                                                     |
| indicate_type        | varchar   | 要素类型                                                                                     |
| indicate_remark      | varchar   | 要素备注                                                                                     |
| template_id          | bigint    | 评分模板ID（关联 ssrc_score_tmpl）                                                          |
| tmpl_assign_id       | bigint    | 评分要素分配ID（关联 ssrc_score_tmpl_assign）                                               |
| weight               | decimal   | 要素权重                                                                                     |
| business_weight      | decimal   | 商务组权重                                                                                   |
| technology_weight    | decimal   | 技术组权重                                                                                   |
| qualifie_score       | decimal   | 合格分值                                                                                     |
| min_score            | decimal   | 最低分                                                                                       |
| max_score            | decimal   | 最高分                                                                                       |
| indic_status         | varchar   | 要素状态：NEW/新建、SUBMITTED/已提交、APPROVED/审批通过、REFUSED/审批拒绝                    |
| team                 | varchar   | 所属组别：BUSINESS/商务组、TECHNOLOGY/技术组、BUSINESS_TECHNOLOGY/商务技术组                 |
| sequence_num         | tinyint   | 序号                                                                                         |
| calculate_type       | varchar   | 计算方式（SSRC_CALCULATE_TYPE）                                                             |
| score_type           | varchar   | 评分类型（SSRC_SCORE_TYPE）                                                                 |
| pass_flag            | tinyint   | 必输通过标识                                                                                 |
| detail_enabled_flag  | tinyint   | 是否启用评分要素细项                                                                         |
| object_version_number| bigint    | 行版本号，用来处理锁                                                                         |
| creation_date        | datetime  | 创建日期                                                                                     |
| last_update_date     | datetime  | 最后更新日期                                                                                 |

## 常用查询

### 查询询价单的评分要素
```sql
SELECT * FROM ssrc_evaluate_indic
WHERE tenant_id = 155357
  AND source_from = 'RFX'
  AND source_header_id = 5923933
ORDER BY sequence_num;
```

### 按组别查询评分要素
```sql
SELECT team, indicate_code, indicate_name, weight, min_score, max_score
FROM ssrc_evaluate_indic
WHERE tenant_id = 155357
  AND source_from = 'RFX'
  AND source_header_id = 5923933
ORDER BY team, sequence_num;
```
