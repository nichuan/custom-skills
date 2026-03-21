# SQL 通用模板

本文件提供 SRM 采购寻源系统的常用 SQL 模板，按业务场景分类。所有模板使用占位符 `{...}` 表示需要替换的参数。

## 占位符说明

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{tenant_num}` | 租户编码 | SRM-AUX |
| `{tenant_id}` | 租户ID（需先通过租户编码查询） | 155357 |
| `{rfx_num}` | 询价单单号 | RFX2026022600014 |
| `{rfx_header_id}` | 询价单头ID | 5923933 |
| `{start_date}` | 开始日期 | 2026-03-01 |
| `{end_date}` | 结束日期 | 2026-03-22 |
| `{status}` | 状态值 | IN_QUOTATION |
| `{expert_id}` | 专家ID | 520399 |
| `{indic_id}` | 评分要素ID | 647869 |
| `{score}` | 分数值 | 4.00 |

---

## 基础查询模板

### 1. 查询租户ID

所有业务查询的前置步骤，通过租户编码获取租户ID。

```sql
SELECT tenant_id, tenant_name
FROM hpfm_tenant
WHERE tenant_num = '{tenant_num}';
```

### 2. 按单号查询询价单

```sql
SELECT *
FROM ssrc_rfx_header
WHERE tenant_id = {tenant_id}
  AND rfx_num = '{rfx_num}';
```

### 3. 按状态查询询价单列表

```sql
SELECT rfx_header_id, rfx_num, rfx_title, rfx_status, quotation_start_date, quotation_end_date
FROM ssrc_rfx_header
WHERE tenant_id = {tenant_id}
  AND rfx_status = '{status}'
ORDER BY creation_date DESC;
```

### 4. 按时间范围查询询价单

```sql
SELECT rfx_header_id, rfx_num, rfx_title, rfx_status, creation_date
FROM ssrc_rfx_header
WHERE tenant_id = {tenant_id}
  AND creation_date BETWEEN '{start_date}' AND '{end_date}'
ORDER BY creation_date DESC;
```

---

## 报价单查询模板

### 5. 查询询价单下的所有报价单

```sql
SELECT qh.quotation_header_id, qh.supplier_company_name, qh.quotation_status,
       qh.qtn_total_amount, qh.creation_date
FROM ssrc_rfx_quotation_header qh
WHERE qh.tenant_id = {tenant_id}
  AND qh.rfx_header_id = {rfx_header_id}
ORDER BY qh.qtn_total_amount ASC;
```

### 6. 询价单与报价单关联查询

```sql
SELECT h.rfx_num, h.rfx_title, h.rfx_status,
       qh.supplier_company_name, qh.quotation_status, qh.qtn_total_amount
FROM ssrc_rfx_header h
INNER JOIN ssrc_rfx_quotation_header qh ON h.rfx_header_id = qh.rfx_header_id
WHERE h.tenant_id = {tenant_id}
  AND h.rfx_header_id = {rfx_header_id};
```

---

## 评分查询模板

### 7. 查询询价单的评分专家

```sql
SELECT see.evaluate_expert_id, see.expert_user_id, see.team, see.scored_status
FROM ssrc_evaluate_expert see
WHERE see.tenant_id = {tenant_id}
  AND see.source_header_id = {rfx_header_id}
  AND see.source_from = 'RFX';
```

### 8. 查询评分要素

```sql
SELECT sei.evaluate_indic_id, sei.indicate_name, sei.weight,
       sei.min_score, sei.max_score
FROM ssrc_evaluate_indic sei
WHERE sei.tenant_id = {tenant_id}
  AND sei.source_header_id = {rfx_header_id}
  AND sei.source_from = 'RFX';
```

### 9. 查询评分汇总（按供应商排名）

```sql
SELECT ses.evaluate_summary_id, qh.supplier_company_name,
       ses.score, ses.score_rank, ses.invalid_flag
FROM ssrc_evaluate_summary ses
INNER JOIN ssrc_rfx_quotation_header qh ON ses.quotation_header_id = qh.quotation_header_id
WHERE ses.tenant_id = {tenant_id}
  AND ses.source_header_id = {rfx_header_id}
  AND ses.source_from = 'RFX'
ORDER BY ses.score_rank ASC;
```

---

## 聚合统计模板

### 10. 统计各状态询价单数量

```sql
SELECT rfx_status, COUNT(*) AS cnt
FROM ssrc_rfx_header
WHERE tenant_id = {tenant_id}
GROUP BY rfx_status;
```

### 11. 统计供应商反馈状态

```sql
SELECT feedback_status, COUNT(*) AS cnt
FROM ssrc_rfx_line_supplier
WHERE tenant_id = {tenant_id}
  AND rfx_header_id = {rfx_header_id}
GROUP BY feedback_status;
```

---

## 数据修复模板

> **重要**: 所有 UPDATE/DELETE 操作必须使用 `tenant_id` + 主键作为 WHERE 条件，确保操作范围可控。

### 12. 修复询价单字段

```sql
-- 步骤1: 查询确认数据
SELECT rfx_header_id, rfx_num, {field_name}
FROM ssrc_rfx_header
WHERE tenant_id = {tenant_id}
  AND rfx_num = '{rfx_num}';

-- 步骤2: 执行修复
UPDATE ssrc_rfx_header
SET {field_name} = '{new_value}'
WHERE tenant_id = {tenant_id}
  AND rfx_header_id = {rfx_header_id};
```

### 13. 修复评分要素最高分

```sql
-- 步骤1: 查询要素信息
SELECT h.rfx_header_id, h.rfx_num,
       i.evaluate_indic_id, i.indicate_name, i.weight,
       i.min_score, i.max_score
FROM ssrc_rfx_header h
LEFT JOIN ssrc_evaluate_indic i
  ON i.tenant_id = h.tenant_id
  AND h.rfx_header_id = i.source_header_id
  AND i.source_from = 'RFX'
WHERE h.tenant_id = {tenant_id}
  AND h.rfx_num = '{rfx_num}';

-- 步骤2: 修复要素最高分
UPDATE ssrc_evaluate_indic
SET max_score = {score}
WHERE evaluate_indic_id = {indic_id}
  AND tenant_id = {tenant_id};
```

### 14. 删除专家及其分配要素

```sql
-- 步骤1: 查询专家信息
SELECT see.evaluate_expert_id, see.expert_user_id, see.team, see.scored_status
FROM ssrc_evaluate_expert see
WHERE see.source_header_id = {rfx_header_id}
  AND see.source_from = 'RFX'
  AND see.tenant_id = {tenant_id};

-- 步骤2: 查询该专家的要素分配
SELECT *
FROM ssrc_evaluate_indic_assign
WHERE tenant_id = {tenant_id}
  AND source_header_id = {rfx_header_id}
  AND evaluate_expert_id = {expert_id};

-- 步骤3: 删除专家的分配要素
DELETE FROM ssrc_evaluate_indic_assign
WHERE tenant_id = {tenant_id}
  AND indic_assgin_id IN ({indic_assign_ids});

-- 步骤4: 删除专家
DELETE FROM ssrc_evaluate_expert
WHERE tenant_id = {tenant_id}
  AND evaluate_expert_id = {expert_id};
```

### 15. 重置评分状态（退回评分中）

```sql
-- 步骤1: 查询单据信息
SELECT rfx_header_id, rfx_num, rfx_status
FROM ssrc_rfx_header
WHERE tenant_id = {tenant_id}
  AND rfx_num = '{rfx_num}';

-- 步骤2: 修复单据状态为评分中
UPDATE ssrc_rfx_header
SET rfx_status = 'SCORING'
WHERE rfx_header_id = {rfx_header_id}
  AND tenant_id = {tenant_id};

-- 步骤3: 修复专家状态为未评分
UPDATE ssrc_evaluate_expert
SET scored_status = 'NEW'
WHERE tenant_id = {tenant_id}
  AND evaluate_expert_id IN ({expert_ids});
```

### 16. 释放寻源结果占用

```sql
-- 步骤1: 查询当前寻源结果
SELECT result_id, receipts_status, occupation_quantity,
       source_result_execute_status, result_execution_strategy
FROM ssrc_source_result
WHERE tenant_id = {tenant_id}
  AND source_num = '{rfx_num}';

-- 步骤2: 查询占用历史
SELECT history_id
FROM ssrc_source_result_change_history
WHERE tenant_id = {tenant_id}
  AND source_result_id = {result_id};

-- 步骤3: 删除占用历史
DELETE FROM ssrc_source_result_change_history
WHERE history_id = {history_id};

-- 步骤4: 释放寻源结果
UPDATE ssrc_source_result
SET receipts_status = NULL,
    occupation_quantity = 0,
    source_result_execute_status = 'UNEXECUTED',
    result_execution_strategy = 'BLANK'
WHERE result_id = {result_id}
  AND tenant_id = {tenant_id};
```
