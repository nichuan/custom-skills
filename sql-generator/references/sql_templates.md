# SQL 通用模板

本文件提供 SRM 采购寻源系统的常用 SQL 模板，按业务场景分类。所有模板使用占位符 `{...}` 表示需要替换的参数。

---

## 占位符说明

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{tenant_num}` | 租户编码 | SRM-AUX |
| `{tenant_id}` | 租户ID（需先通过租户编码查询） | 155357 |
| `{company_num}` | 公司编码 | C0001 |
| `{company_id}` | 公司ID | 12345 |
| `{rfx_num}` | 询价单单号 | RFX2026022600014 |
| `{rfx_header_id}` | 询价单头ID | 5923933 |
| `{rfx_header_expand_id}` | 询价单扩展表ID | 5923933 |
| `{rf_num}` | 征询单单号 | RF2026010100001 |
| `{rf_header_id}` | 征询单头ID | 31285 |
| `{rf_conf_rule_id}` | 征询单配置规则ID | 31285 |
| `{start_date}` | 开始日期 | 2026-03-01 |
| `{end_date}` | 结束日期 | 2026-03-22 |
| `{new_end_date}` | 新的报价截止时间 | 2025-09-10 18:00:00 |
| `{duration_seconds}` | 报价时长（秒） | 79287 |
| `{status}` | 状态值 | IN_QUOTATION |
| `{expert_id}` | 专家ID | 520399 |
| `{expert_ids}` | 专家ID列表（多个用逗号分隔） | 492160,492158,492159 |
| `{indic_id}` | 评分要素ID | 647869 |
| `{indic_assign_ids}` | 要素分配ID列表（多个用逗号分隔） | 1001,1002,1003 |
| `{score}` | 分数值 | 4.00 |
| `{field_name}` | 字段名称 | rfx_title |
| `{new_value}` | 新的字段值 | 新的询价单标题 |
| `{social_code}` | 统一社会信用码 | 91110000MA001EXAMPLE |
| `{duns_code}` | 邓白氏编码 | 123456789 |
| `{evaluate_line_ids}` | 评分行ID列表（多个用逗号分隔） | 2001,2002,2003 |
| `{evaluate_score_ids}` | 评分头ID列表（多个用逗号分隔） | 3001,3002,3003 |
| `{quotation_header_id_1}` | 报价单头ID（单个） | 4001 |
| `{quotation_header_id_2}` | 报价单头ID（多个中的第一个） | 4002 |
| `{quotation_header_id_3}` | 报价单头ID（多个中的第二个） | 4003 |
| `{quotation_header_id_4}` | 报价单头ID（多个中的第三个） | 4004 |
| `{result_id}` | 寻源结果ID | 8001 |
| `{history_id}` | 寻源结果变更历史ID | 8002 |

---

## 一、通用基础查询模板

> 以下模板适用于所有业务场景的基础数据查询。

### 1.1 查询租户ID

**业务场景**: 所有业务查询的前置步骤，通过租户编码获取租户ID。

```sql
SELECT tenant_id,
       tenant_name
FROM   hpfm_tenant
WHERE  tenant_num = '{tenant_num}';
```

### 1.2 查询公司信息

**业务场景**: 根据公司编码查询公司基本信息，用于验证公司是否存在或获取公司详情。

```sql
SELECT company_id,
       company_num,
       company_name,
       company_type,
       unified_social_code,
       duns_code,
       enabled_flag
FROM   hpfm_company
WHERE  tenant_id = {tenant_id}
  AND  company_num = '{company_num}';
```

---

## 二、询价单（RFX）SQL模板

> 以下模板适用于询价单相关的查询、统计和数据修复操作。

### 2.1 询价单基础查询

#### 2.1.1 按单号查询询价单

**业务场景**: 根据询价单单号查询单据详情，用于查看单据状态或进行数据核对。

```sql
SELECT *
FROM   ssrc_rfx_header
WHERE  tenant_id = {tenant_id}
  AND  rfx_num = '{rfx_num}';
```

#### 2.1.2 按状态查询询价单列表

**业务场景**: 查询指定状态的询价单列表，常用于批量处理或状态监控。

```sql
SELECT rfx_header_id,
       rfx_num,
       rfx_title,
       rfx_status,
       quotation_start_date,
       quotation_end_date
FROM   ssrc_rfx_header
WHERE  tenant_id = {tenant_id}
  AND  rfx_status = '{status}'
ORDER BY creation_date DESC;
```

#### 2.1.3 按时间范围查询询价单

**业务场景**: 查询指定时间范围内创建的询价单，用于报表统计或历史数据查询。

```sql
SELECT rfx_header_id,
       rfx_num,
       rfx_title,
       rfx_status,
       creation_date
FROM   ssrc_rfx_header
WHERE  tenant_id = {tenant_id}
  AND  creation_date BETWEEN '{start_date}' AND '{end_date}'
ORDER BY creation_date DESC;
```

### 2.2 询价单公司信息查询

#### 2.2.1 查询询价单的采购方公司信息

**业务场景**: 关联查询询价单和采购方公司信息，用于确认采购主体。

```sql
SELECT h.rfx_num,
       h.rfx_title,
       h.rfx_status,
       hc.company_name,
       hc.company_num,
       hc.company_type,
       hc.unified_social_code
FROM   ssrc_rfx_header h
       INNER JOIN hpfm_company hc ON h.company_id = hc.company_id
WHERE  h.tenant_id = {tenant_id}
  AND  h.rfx_header_id = {rfx_header_id};
```

#### 2.2.2 查询询价单的供应商公司信息

**业务场景**: 关联查询询价单、供应商行和公司信息，用于获取参与报价的供应商列表。

```sql
SELECT h.rfx_num,
       qls.supplier_company_name,
       hc.company_num,
       hc.company_name,
       hc.company_type,
       hc.duns_code
FROM   ssrc_rfx_header h
       INNER JOIN ssrc_rfx_line_supplier qls ON h.rfx_header_id = qls.rfx_header_id
       INNER JOIN hpfm_company hc ON qls.supplier_company_id = hc.company_id
WHERE  h.tenant_id = {tenant_id}
  AND  h.rfx_header_id = {rfx_header_id};
```

### 2.3 报价单查询

#### 2.3.1 查询询价单下的所有报价单

**业务场景**: 查询指定询价单下的所有供应商报价单，用于比价分析。

```sql
SELECT qh.quotation_header_id,
       qh.supplier_company_name,
       qh.quotation_status,
       qh.qtn_total_amount,
       qh.creation_date
FROM   ssrc_rfx_quotation_header qh
WHERE  qh.tenant_id = {tenant_id}
  AND  qh.rfx_header_id = {rfx_header_id}
ORDER BY qh.qtn_total_amount ASC;
```

#### 2.3.2 查询报价单的供应商公司信息

**业务场景**: 关联查询报价单和供应商公司信息，用于获取报价供应商的详细资料。

```sql
SELECT qh.quotation_header_id,
       qh.quotation_status,
       qh.qtn_total_amount,
       hc.company_name,
       hc.company_num,
       hc.company_type,
       hc.unified_social_code
FROM   ssrc_rfx_quotation_header qh
       INNER JOIN hpfm_company hc ON qh.supplier_company_id = hc.company_id
WHERE  qh.tenant_id = {tenant_id}
  AND  qh.rfx_header_id = {rfx_header_id};
```

#### 2.3.3 询价单与报价单关联查询（含供应商公司信息）

**业务场景**: 一次性查询询价单及其所有报价单的完整信息，用于综合分析。

```sql
SELECT h.rfx_num,
       h.rfx_title,
       h.rfx_status,
       qh.quotation_header_id,
       qh.quotation_status,
       qh.qtn_total_amount,
       hc.company_name,
       hc.company_num
FROM   ssrc_rfx_header h
       INNER JOIN ssrc_rfx_quotation_header qh ON h.rfx_header_id = qh.rfx_header_id
       INNER JOIN hpfm_company hc ON qh.supplier_company_id = hc.company_id
WHERE  h.tenant_id = {tenant_id}
  AND  h.rfx_header_id = {rfx_header_id};
```

### 2.4 询价单评分查询

#### 2.4.1 查询询价单的评分专家

**业务场景**: 查询参与询价单评分的专家列表，用于了解评分团队组成。

```sql
SELECT see.evaluate_expert_id,
       see.expert_user_id,
       see.team,
       see.scored_status
FROM   ssrc_evaluate_expert see
WHERE  see.tenant_id = {tenant_id}
  AND  see.source_header_id = {rfx_header_id}
  AND  see.source_from = 'RFX';
```

#### 2.4.2 查询评分要素

**业务场景**: 查询询价单的评分要素及权重，用于了解评分标准。

```sql
SELECT sei.evaluate_indic_id,
       sei.indicate_name,
       sei.weight,
       sei.min_score,
       sei.max_score
FROM   ssrc_evaluate_indic sei
WHERE  sei.tenant_id = {tenant_id}
  AND  sei.source_header_id = {rfx_header_id}
  AND  sei.source_from = 'RFX';
```

#### 2.4.3 查询评分汇总（按供应商排名）

**业务场景**: 查询各供应商的评分汇总及排名，用于确定中标供应商。

```sql
SELECT ses.evaluate_summary_id,
       qh.supplier_company_name,
       ses.score,
       ses.score_rank,
       ses.invalid_flag
FROM   ssrc_evaluate_summary ses
       INNER JOIN ssrc_rfx_quotation_header qh ON ses.quotation_header_id = qh.quotation_header_id
WHERE  ses.tenant_id = {tenant_id}
  AND  ses.source_header_id = {rfx_header_id}
  AND  ses.source_from = 'RFX'
ORDER BY ses.score_rank ASC;
```

### 2.5 询价单聚合统计

#### 2.5.1 统计各状态询价单数量

**业务场景**: 统计各状态下的询价单数量，用于业务监控和报表展示。

```sql
SELECT rfx_status,
       COUNT(*) AS cnt
FROM   ssrc_rfx_header
WHERE  tenant_id = {tenant_id}
GROUP BY rfx_status;
```

### 2.6 询价单数据修复

> **重要**: 所有 UPDATE/DELETE 操作必须使用 `tenant_id` + 主键作为 WHERE 条件，确保操作范围可控。

#### 2.6.1 修复询价单字段

**业务场景**: 修复询价单的指定字段值，如标题、描述等文本信息。

```sql
-- 步骤1: 查询确认数据
SELECT rfx_header_id,
       rfx_num,
       {field_name}
FROM   ssrc_rfx_header
WHERE  tenant_id = {tenant_id}
  AND  rfx_num = '{rfx_num}';

-- 步骤2: 执行修复
UPDATE ssrc_rfx_header
SET    {field_name} = '{new_value}'
WHERE  tenant_id = {tenant_id}
  AND  rfx_header_id = {rfx_header_id};
```

#### 2.6.2 修复询价单状态

**业务场景**: 修复询价单状态时，需同时更新主表和扩展表的状态字段。

**涉及表**: `ssrc_rfx_header`（询价单头表）、`ssrc_rfx_header_expand`（询价单扩展表）

```sql
-- 步骤1: 查询租户ID
SELECT tenant_id
FROM   hpfm_tenant
WHERE  tenant_num = '{tenant_num}';

-- 步骤2: 联合查询询价单主表和扩展表信息（一次性获取两个表的主键）
SELECT srh.rfx_header_id,
       srh.rfx_num,
       srh.rfx_status,
       srh.rfx_title,
       srhe.rfx_header_expand_id,
       srhe.rfx_real_status
FROM   ssrc_rfx_header srh
       INNER JOIN ssrc_rfx_header_expand srhe ON srh.rfx_header_id = srhe.rfx_header_id
WHERE  srh.tenant_id = {tenant_id}
  AND  srh.rfx_num = '{rfx_num}';

-- 步骤3: 更新询价单主表状态
UPDATE ssrc_rfx_header
SET    rfx_status = '{status}'
WHERE  rfx_header_id = {rfx_header_id}
  AND  tenant_id = {tenant_id};

-- 步骤4: 同步更新扩展表状态（必须同步执行）
UPDATE ssrc_rfx_header_expand
SET    rfx_real_status = '{status}'
WHERE  rfx_header_expand_id = {rfx_header_expand_id}
  AND  tenant_id = {tenant_id};
```

**状态值说明**:
- `IN_QUOTATION` - 报价中
- `SCORING` - 评分中
- `CHECK_APPROVING` - 核价审批中
- `FINISHED` - 已完成

#### 2.6.3 修复评分要素最高分

**业务场景**: 修复评分要素的最高分限制，用于调整评分规则。

```sql
-- 步骤1: 查询要素信息
SELECT h.rfx_header_id,
       h.rfx_num,
       i.evaluate_indic_id,
       i.indicate_name,
       i.weight,
       i.min_score,
       i.max_score
FROM   ssrc_rfx_header h
       LEFT JOIN ssrc_evaluate_indic i
         ON i.tenant_id = h.tenant_id
        AND h.rfx_header_id = i.source_header_id
        AND i.source_from = 'RFX'
WHERE  h.tenant_id = {tenant_id}
  AND  h.rfx_num = '{rfx_num}';

-- 步骤2: 修复要素最高分
UPDATE ssrc_evaluate_indic
SET    max_score = {score}
WHERE  evaluate_indic_id = {indic_id}
  AND  tenant_id = {tenant_id};
```

#### 2.6.4 删除专家及其分配要素

**业务场景**: 删除评分专家及其相关的要素分配，用于调整评分团队。

```sql
-- 步骤1: 查询专家信息
SELECT see.evaluate_expert_id,
       see.expert_user_id,
       see.team,
       see.scored_status
FROM   ssrc_evaluate_expert see
WHERE  see.source_header_id = {rfx_header_id}
  AND  see.source_from = 'RFX'
  AND  see.tenant_id = {tenant_id};

-- 步骤2: 查询该专家的要素分配
SELECT *
FROM   ssrc_evaluate_indic_assign
WHERE  tenant_id = {tenant_id}
  AND  source_header_id = {rfx_header_id}
  AND  evaluate_expert_id = {expert_id};

-- 步骤3: 删除专家的分配要素
DELETE FROM ssrc_evaluate_indic_assign
WHERE  tenant_id = {tenant_id}
  AND  indic_assgin_id IN ({indic_assign_ids});

-- 步骤4: 删除专家
DELETE FROM ssrc_evaluate_expert
WHERE  tenant_id = {tenant_id}
  AND  evaluate_expert_id = {expert_id};
```

#### 2.6.5 删除寻源结果

**业务场景**: 普通删除/清除寻源结果，用于取消或重置寻源结果。此场景仅操作 `ssrc_source_result` 表，不涉及 `ssrc_source_result_change_history`。

**涉及表**: `ssrc_source_result`（寻源结果表）

```sql
-- 步骤1: 查询当前寻源结果
SELECT result_id,
       source_from,
       source_num,
       supplier_company_name,
       item_code,
       item_name,
       result_status
FROM   ssrc_source_result
WHERE  tenant_id = {tenant_id}
AND soruce_from = 'RFX'
AND  source_header_id = '{source_header_id}';

-- 步骤2: 删除寻源结果
DELETE FROM ssrc_source_result
WHERE  result_id = {result_id}
  AND  tenant_id = {tenant_id};
```

#### 2.6.7 释放被订单错误占用的寻源结果

**业务场景**: 当寻源结果被订单错误占用（如订单错误引用了寻源结果），需要同时清理占用历史记录。**此场景才需要操作 `ssrc_source_result_change_history` 表**，普通删除寻源结果不需要。

**涉及表**: `ssrc_source_result`（寻源结果表）、`ssrc_source_result_change_history`（寻源结果变更历史表）

```sql
-- 步骤1: 查询当前寻源结果
SELECT result_id,
       receipts_status,
       occupation_quantity,
       source_result_execute_status,
       result_execution_strategy
FROM   ssrc_source_result
WHERE  tenant_id = {tenant_id}
  AND  source_num = '{rfx_num}';

-- 步骤2: 查询占用历史
SELECT history_id
FROM   ssrc_source_result_change_history
WHERE  tenant_id = {tenant_id}
  AND  source_result_id = {result_id};

-- 步骤3: 删除占用历史（仅在被订单错误占用时执行此步骤）
DELETE FROM ssrc_source_result_change_history
WHERE  history_id = {history_id};

-- 步骤4: 释放寻源结果
UPDATE ssrc_source_result
SET    receipts_status = NULL,
       occupation_quantity = 0,
       source_result_execute_status = 'UNEXECUTED',
       result_execution_strategy = 'BLANK'
WHERE  result_id = {result_id}
  AND  tenant_id = {tenant_id};
```

#### 2.6.6 询价单回退至报价中（延时消息）

**业务场景**: 当询价单状态回退至"报价中"(IN_QUOTATION)时（如核价回退、评分回退、修复报价截止时间等），必须执行3条SQL：修复主表状态、修复扩展表状态、插入延时消息。

**涉及表**: `ssrc_rfx_header`（询价单头表）、`ssrc_rfx_header_expand`（询价单扩展表）、`spfm_pending_message`（延时消息表）

```sql
-- 步骤1: 查询租户ID
SELECT tenant_id
FROM   hpfm_tenant
WHERE  tenant_num = '{tenant_num}';

-- 步骤2: 联合查询询价单主表和扩展表信息
SELECT srh.rfx_header_id,
       srh.rfx_num,
       srh.rfx_status,
       srh.quotation_end_date,
       srh.created_by,
       srhe.rfx_header_expand_id,
       srhe.rfx_real_status
FROM   ssrc_rfx_header srh
       INNER JOIN ssrc_rfx_header_expand srhe ON srh.rfx_header_id = srhe.rfx_header_id
WHERE  srh.tenant_id = {tenant_id}
  AND  srh.rfx_num = '{rfx_num}';

-- 步骤3: 更新询价单主表状态和报价截止时间
UPDATE ssrc_rfx_header
SET    rfx_status = 'IN_QUOTATION',
       quotation_end_date = '{new_end_date}',
       latest_quotation_end_date = '{new_end_date}'
WHERE  rfx_header_id = {rfx_header_id}
  AND  tenant_id = {tenant_id};

-- 步骤4: 同步更新扩展表状态
UPDATE ssrc_rfx_header_expand
SET    rfx_real_status = 'IN_QUOTATION'
WHERE  rfx_header_expand_id = {rfx_header_expand_id}
  AND  tenant_id = {tenant_id};

-- 步骤5: 插入延时消息（必须执行，用于报价截止时间到达后自动刷新状态）
INSERT INTO spfm_pending_message (tenant_id, biz_id, biz_type, server_name, execute_type, execute_time,
                                  executed_flag, expand_param, object_version_number, creation_date,
                                  created_by, last_updated_by, last_update_date, adaptor_code)
VALUES ({tenant_id}, {rfx_header_id}, 'RFX', 'srm-source', 'QUOTATION_END_REFRESH_RFX_STATUS', '{new_end_date}', '0',
        null, '1', now(), {user_id}, {user_id}, now(), null);
```

**占位符说明**:
- `{user_id}`: 操作人用户ID（可通过询价单的 created_by 字段获取）

**延时消息字段说明**:
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

#### 2.6.8 修复供应商物料分配

**业务场景**: 修复询价单中供应商的物料分配情况，将未邀请的物料设置为已邀请状态。

**涉及表**: `ssrc_rfx_header`（询价单头表）、`ssrc_rfx_line_supplier`（供应商行表）、`ssrc_rfx_item_sup_assign`（物料供应商分配表）

```sql
-- 步骤1: 查询询价单信息
SELECT rfx_header_id,
       rfx_num,
       rfx_title,
       rfx_status
FROM   ssrc_rfx_header
WHERE  tenant_id = {tenant_id}
  AND  rfx_num = '{rfx_num}';

-- 步骤2: 查询供应商行信息
SELECT rfx_line_supplier_id,
       supplier_company_id,
       supplier_company_name,
       feedback_status
FROM   ssrc_rfx_line_supplier
WHERE  tenant_id = {tenant_id}
  AND  rfx_header_id = {rfx_header_id}
  AND  supplier_company_id = {supplier_company_id};

-- 步骤3: 查询该供应商的物料分配情况
SELECT item_sup_assign_id,
       rfx_line_item_id,
       invite_flag
FROM   ssrc_rfx_item_sup_assign
WHERE  tenant_id = {tenant_id}
  AND  rfx_header_id = {rfx_header_id}
  AND  rfx_line_supplier_id = {rfx_line_supplier_id};

-- 步骤4: 更新物料分配状态为已邀请
UPDATE ssrc_rfx_item_sup_assign
SET    invite_flag = 1
WHERE  tenant_id = {tenant_id}
  AND  item_sup_assign_id IN ({item_sup_assign_ids});
```

**说明**:
- `invite_flag = 1` 表示已邀请
- `invite_flag = 0` 表示未邀请
- 需要先查询出需要更新的`item_sup_assign_id`列表

---

## 三、征询单（RF）SQL模板

> 以下模板适用于征询单相关的查询和数据修复操作。

### 3.1 征询单基础查询

#### 3.1.1 按单号查询征询单

**业务场景**: 根据征询单单号查询单据详情，用于查看单据状态或进行数据核对。

```sql
SELECT rf_header_id,
       rf_num,
       rf_title,
       display_rf_status,
       current_node,
       creation_date
FROM   ssrc_rf_header
WHERE  tenant_id = {tenant_id}
  AND  rf_num = '{rf_num}';
```

#### 3.1.2 按状态查询征询单列表

**业务场景**: 查询指定状态的征询单列表，常用于批量处理或状态监控。

```sql
SELECT rf_header_id,
       rf_num,
       rf_title,
       display_rf_status,
       current_node,
       creation_date
FROM   ssrc_rf_header
WHERE  tenant_id = {tenant_id}
  AND  display_rf_status = '{status}'
ORDER BY creation_date DESC;
```

#### 3.1.3 按时间范围查询征询单

**业务场景**: 查询指定时间范围内创建的征询单，用于报表统计或历史数据查询。

```sql
SELECT rf_header_id,
       rf_num,
       rf_title,
       display_rf_status,
       current_node,
       creation_date
FROM   ssrc_rf_header
WHERE  tenant_id = {tenant_id}
  AND  creation_date BETWEEN '{start_date}' AND '{end_date}'
ORDER BY creation_date DESC;
```

### 3.2 征询单报价查询

#### 3.2.1 查询征询单下的所有报价单

**业务场景**: 查询指定征询单下的所有供应商报价单，用于比价分析。

```sql
SELECT quotation_header_id,
       supplier_company_name,
       display_quotation_status,
       qtn_total_amount,
       creation_date
FROM   ssrc_rf_quotation_header
WHERE  tenant_id = {tenant_id}
  AND  rf_header_id = {rf_header_id}
ORDER BY qtn_total_amount ASC;
```

#### 3.2.2 查询征询单配置规则

**业务场景**: 查询征询单的配置规则，了解报价时间、评分方式等配置信息。

```sql
SELECT rf_conf_rule_id,
       rf_header_id,
       quotation_start_date,
       quotation_end_date,
       quotation_running_duration,
       score_method
FROM   ssrc_rf_conf_rule
WHERE  tenant_id = {tenant_id}
  AND  rf_header_id = {rf_header_id};
```

### 3.3 征询单数据修复

> **重要**: 所有 UPDATE/DELETE 操作必须使用 `tenant_id` + 主键作为 WHERE 条件，确保操作范围可控。

#### 3.3.1 修复征询单状态为评分中

**业务场景**: 修复征询单状态为"评分中"，比如已经到了确定供应商的状态，用户希望整单重新评分。

**涉及表**: `ssrc_rf_header`（征询单头表）、`ssrc_evaluate_expert`（专家表）、`ssrc_evaluate_score`（评分头表）、`ssrc_evaluate_score_line`（评分行表）

**征询单类型说明**:
- RFI开头（如RFI2025112000002）：信息征询，`source_from = 'RFI'`
- RFP开头（如RFP2025112000002）：方案征询，`source_from = 'RFP'`

```sql
-- 步骤1: 查询租户ID
SELECT tenant_id
FROM   hpfm_tenant
WHERE  tenant_num = '{tenant_num}';

-- 步骤2: 查询征询单信息
SELECT rf_header_id,
       rf_num,
       display_rf_status,
       current_node,
       rf_title
FROM   ssrc_rf_header
WHERE  tenant_id = {tenant_id}
  AND  rf_num = '{rf_num}';

-- 步骤3: 判断征询单类型并设置source_from
-- RFI开头：source_from = 'RFI'（信息征询）
-- RFP开头：source_from = 'RFP'（方案征询）
-- 示例：RFI2025112000002 -> source_from = 'RFI'

-- 步骤4: 查询征询专家表
SELECT *
FROM   ssrc_rf_expert
WHERE  rf_header_id = {rf_header_id};

-- 步骤5: 查询真实专家表
SELECT evaluate_expert_id,
       expert_user_id,
       team,
       scored_status
FROM   ssrc_evaluate_expert
WHERE  source_header_id = {rf_header_id}
  AND  source_from = '{source_from}'
  AND  tenant_id = {tenant_id};

-- 步骤6: 查询评分头表
SELECT evaluate_score_id,
       quotation_header_id,
       evaluate_expert_id,
       score_status,
       sum_indic_score
FROM   ssrc_evaluate_score
WHERE  tenant_id = {tenant_id}
  AND  source_header_id = {rf_header_id}
  AND  source_from = '{source_from}';

-- 步骤7: 查询评分行表
SELECT evaluate_line_id,
       evaluate_score_id,
       evaluate_indic_id,
       indic_score
FROM   ssrc_evaluate_score_line
WHERE  evaluate_score_id IN (
    SELECT evaluate_score_id
    FROM   ssrc_evaluate_score
    WHERE  tenant_id = {tenant_id}
      AND  source_header_id = {rf_header_id}
      AND  source_from = '{source_from}'
);

-- 步骤8: 修复单据状态为评分中
UPDATE ssrc_rf_header
SET    display_rf_status = 'SCORING'
WHERE  rf_header_id = {rf_header_id}
  AND  tenant_id = {tenant_id};

-- 步骤9: 修复专家状态为未评分
UPDATE ssrc_evaluate_expert
SET    scored_status = 'NEW'
WHERE  tenant_id = {tenant_id}
  AND  evaluate_expert_id IN ({expert_ids});

-- 步骤10: 删除已存在的评分行
DELETE FROM ssrc_evaluate_score_line
WHERE  tenant_id = {tenant_id}
  AND  evaluate_line_id IN ({evaluate_line_ids});

-- 步骤11: 删除已存在的评分头
DELETE FROM ssrc_evaluate_score
WHERE  tenant_id = {tenant_id}
  AND  evaluate_score_id IN ({evaluate_score_ids});
```

#### 3.3.2 修复征询单（延长报价时间）

**业务场景**: 将已过期的征询单状态恢复为"报价中"，并延长报价截止时间。

**涉及表**: `ssrc_rf_header`（征询单头表）、`ssrc_rf_conf_rule`（征询单配置规则表）、`ssrc_rf_quotation_header`（征询单报价头表）

```sql
-- 步骤1: 查询租户ID
SELECT tenant_id
FROM   hpfm_tenant
WHERE  tenant_num = '{tenant_num}';

-- 步骤2: 查询征询单信息
SELECT rf_header_id,
       rf_num,
       display_rf_status,
       current_node,
       rf_title
FROM   ssrc_rf_header
WHERE  tenant_id = {tenant_id}
  AND  rf_num = '{rf_num}';

-- 步骤3: 查询该征询单下的所有供应商报价单
SELECT quotation_header_id,
       supplier_company_name,
       display_quotation_status
FROM   ssrc_rf_quotation_header
WHERE  tenant_id = {tenant_id}
  AND  rf_header_id = {rf_header_id};

-- 步骤4: 更新征询单状态为"报价中"
UPDATE ssrc_rf_header
SET    display_rf_status = 'IN_QUOTATION',
       current_node = 'IN_QUOTATION'
WHERE  rf_header_id = {rf_header_id}
  AND  tenant_id = {tenant_id};

-- 步骤5: 更新征询单配置的截止时间和时长
UPDATE ssrc_rf_conf_rule
SET    quotation_end_date = '{new_end_date}',
       quotation_running_duration = {duration_seconds}
WHERE  rf_conf_rule_id = {rf_conf_rule_id}
  AND  tenant_id = {tenant_id};

-- 步骤6: 更新各供应商报价单的状态
-- 6.1 待回复的报价单
UPDATE ssrc_rf_quotation_header
SET    display_quotation_status = 'REPLY_PENDING'
WHERE  tenant_id = {tenant_id}
  AND  quotation_header_id = {quotation_header_id_1};

-- 6.2 已回复的报价单（可同时更新多个）
UPDATE ssrc_rf_quotation_header
SET    display_quotation_status = 'REPLIED'
WHERE  tenant_id = {tenant_id}
  AND  quotation_header_id IN ({quotation_header_id_2}, {quotation_header_id_3}, {quotation_header_id_4});
```

---

## 附录：状态值参考

### 询价单状态（RFX Status）

| 状态值 | 说明 |
|--------|------|
| `BARGAINING` | 议价中 |
| `CANCELED` | 已取消 |
| `CHECKING` | 核价中 |
| `CHECK_APPROVING` | 核价审批中 |
| `CHECK_PENDING` | 待核价 |
| `CHECK_REJECTED` | 核价审批拒绝 |
| `CLOSED` | 关闭 |
| `FINISHED` | 完成 |
| `IN_POSTQUAL` | 资格后审中 |
| `IN_PREQUAL` | 资格预审中 |
| `IN_QUOTATION` | 报价中 |
| `LACK_QUOTED` | 报价响应不足 |
| `NEW` | 新建 |
| `NOT_START` | 未开始 |
| `OPENED` | 已开标 |
| `OPEN_BID_PENDING` | 待开标 |
| `PAUSED` | 暂停 |
| `PENDING_PREQUAL` | 待预审审批 |
| `POSTQUAL_CUTOFF` | 资格后审截止 |
| `PRETRIAL_PENDING` | 待初审 |
| `PRE_EVALUATION_APPROVING` | 候选人审批中 |
| `PRE_EVALUATION_PENDING` | 待定候选人 |
| `PRE_EVALUATION_PENDING_REJECT` | 候选人审批拒绝 |
| `RELEASE_APPROVING` | 发布审批中 |
| `RELEASE_REJECTED` | 发布审批拒绝 |
| `RFX_EVALUATION_PENDING` | 待评分汇总 |
| `ROUNDED` | 再次询价 |
| `ROUND_QUOTATION` | 多轮报价 |
| `SCORING` | 评分中 |
| `UN_SOURCE` | 未寻源 |

### 征询单状态（RF display_rf_status）

| 状态值 | 说明 |
|--------|------|
| `CANCELED` | 取消 |
| `CHECK_APPROVING` | 结果审批中 |
| `CHECK_PENDING` | 待确定供应商 |
| `CHECK_REJECTED` | 结果审批拒绝 |
| `CLOSED` | 关闭 |
| `COMPLIANCE_CHECKING` | 符合性检查中 |
| `COMPLIANCE_CHECK_CONFIRMATION` | 符合性检查结果确认 |
| `CONFIRM_CANDIDATES_PENDING` | 待定候选人 |
| `FINISHED` | 已完成 |
| `IN_QUOTATION` | 回复中 |
| `LACK_QUOTED` | 响应不足 |
| `NEW` | 新建 |
| `NOT_START` | 未开始 |
| `RELEASE_APPROVING` | 发布审批中 |
| `RELEASE_REJECTED` | 发布审批拒绝 |
| `SCORE_SUMMARY_PENDING` | 待评分汇总 |
| `SCORING` | 评分中 |

### 报价单状态（Quotation Status）

| 状态值 | 说明 |
|--------|------|
| `REPLY_PENDING` | 待回复 |
| `REPLIED` | 已回复 |

### 专家评分状态（Scored Status）

| 状态值 | 说明 |
|--------|------|
| `NEW` | 未评分 |
| `SCORED` | 已评分 |
