# ssrc_source_template 寻源模板表

## 表说明
寻源模板表，定义询价单/招标单的业务规则配置，包括评分方式、资格审查、开标规则等。

## 核心字段（高频使用）

| 字段名 | 数据类型 | 说明 | 关联 |
|--------|----------|------|------|
| template_id | bigint | 主键 | ssrc_rfx_header.template_id |
| tenant_id | bigint | 租户ID | hpfm_tenant.tenant_id |
| template_num | varchar | 模板编号 | — |
| template_name | varchar | 模板名称 | — |
| template_status | varchar | 模板状态：PENDING/待发布、RELEASED/已发布 | — |
| version_number | int | 版本 | — |
| latest_flag | varchar | 模板标志：P/父模板、Y/最新模板、N/历史模板 | — |
| source_category | varchar | 寻源类别：RFQ/询价、RFA/竞价、BID/招投标 | — |
| secondary_source_category | varchar | 次级寻源类别：RFQ/RFA/BID/NEW_BID | — |
| qualification_type | varchar | 资格审查方式：NONE/无需、PRE/资格预审、POST/资格后审、PRE_POST/预审并后审 | — |
| expert_score_type | varchar | 专家评分方式：NONE/无需、ONLINE/线上、OFFLINE/线下 | — |
| pretrial_flag | tinyint | 是否有询价初审 | — |
| release_approve_type | varchar | 发布审批方式：SELF/自审批、WFL/工作流、EXTERNAL/外部审批 | — |
| result_approve_type | varchar | 结果审批方式 | — |
| score_type | varchar | 评分方式：WEIGHT/权重法、SCORE/分值法 | — |
| open_bid_order | varchar | 开标步制：SYNC/同步、TECH_FIRST/先技术后商务、BUSINESS_FIRST/先商务后技术 | — |
| source_method | varchar | 询价方式：INVITE/邀请、OPEN/合作伙伴公开、ALL_OPEN/全平台公开 | — |
| auction_direction | varchar | 竞价方向：FORWARD/正向、REVERSE/反向 | — |
| tax_included_flag | tinyint | 是否含税标志 | — |

## 其他字段

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| bid_rule_type | varchar | 标书规则：NONE/不区分、DIFF/分商务技术 |
| multi_currency_flag | tinyint | 是否允许多币种报价 |
| sealed_quotation_flag | tinyint | 密封报价标志 |
| password_flag | tinyint | 开启开标密码标识 |
| auto_defer_flag | tinyint | 是否启用自动延时 |
| quotation_type | varchar | 报价方式：ONLINE/线上、OFFLINE/线下、ON_OFF/线上线下并行 |
| quotation_scope | varchar | 报价范围：PART_QUOTATION/部分、ALL_QUOTATION/全部 |
| rank_rule | varchar | 排名规则：UNIT_PRICE/按单价、WEIGHT_PRICE/按权重单价 |
| bargain_rule | varchar | 议价规则：NONE/不允许、SCORE/评审阶段、CHECK/核价阶段、ALL/均允许 |
| opener_flag | tinyint | 是否启用开标人 |
| object_version_number | bigint | 行版本号（乐观锁） |
| creation_date | datetime | 创建日期 |
| created_by | bigint | 创建人 |
| last_updated_by | bigint | 最后更新人 |
| last_update_date | datetime | 最后更新日期 |

## 常用查询示例

```sql
-- 查询询价单关联的模板信息
SELECT t.*
FROM ssrc_source_template t
JOIN ssrc_rfx_header h ON t.template_id = h.template_id
WHERE h.tenant_id = 155357
  AND h.rfx_header_id = 5923933;

-- 查询某租户下所有已发布的模板
SELECT template_id, template_num, template_name, source_category, expert_score_type
FROM ssrc_source_template
WHERE tenant_id = 155357
  AND template_status = 'RELEASED'
  AND latest_flag = 'Y';
```
