# 核心表关联关系

## 主业务流程关联链

```
hpfm_tenant (租户)
    ├── ssrc_rfx_header (询价单头) [tenant_id]
    │       ├── ssrc_rfx_header_expand (询价单头拓展) [rfx_header_id]
    │       ├── ssrc_rfx_line_item (询价单物料行) [rfx_header_id]
    │       ├── ssrc_rfx_line_supplier (询价单供应商行) [rfx_header_id]
    │       ├── ssrc_rfx_member (寻源小组成员) [rfx_header_id]
    │       ├── ssrc_source_template (寻源模板) [template_id]
    │       ├── ssrc_prequal_header (资格预审头) [rfx_header_id]
    │       │       └── ssrc_prequal_line (资格预审行) [prequal_header_id]
    │       ├── ssrc_rfx_quotation_header (报价单头) [rfx_header_id]
    │       │       └── ssrc_rfx_quotation_line (报价单行) [quotation_header_id]
    │       ├── ssrc_evaluate_expert (评分专家) [source_header_id]
    │       ├── ssrc_evaluate_indic (评分要素) [source_header_id]
    │       ├── ssrc_evaluate_score (评分头) [source_header_id]
    │       │       └── ssrc_evaluate_score_line (评分行) [evaluate_score_id]
    │       ├── ssrc_evaluate_summary (评分汇总) [source_header_id]
    │       ├── ssrc_source_result (寻源结果) [source_header_id]
    │       │       └── ssrc_source_result_change_history (变更历史) [source_result_id]
    └── ssrc_rf_header (征询单头) [tenant_id]
            ├── ssrc_rf_conf_rule (征询单配置规则) [rf_header_id]
            ├── ssrc_rf_line_item (征询单物料行) [rf_header_id]
            │       └── ssrc_rf_item_sup_assign (物料供应商分配) [rf_line_item_id]
            ├── ssrc_rf_line_supplier (征询单供应商行) [rf_header_id]
            │       └── ssrc_rf_item_sup_assign (物料供应商分配) [rf_line_supplier_id]
            └── ssrc_rf_quotation_header (征询单报价头) [rf_line_supplier_id]
```

## 详细关联关系

### 1. 租户与询价单
| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| hpfm_tenant | tenant_id | ssrc_rfx_header | tenant_id | 租户下的询价单 |
| hpfm_tenant | tenant_id | hpfm_company | tenant_id | 租户下的公司信息 |

### 1.2. 用户（人员）关联 —— 核心基础表 iam_user
> ⚠️ **极重要规则**
> - **所有 SRM 业务表中存储的人员ID，最终都指向 `iam_user.id`**（如 `user_id`、`expert_user_id`、`created_by`、`last_updated_by`、`process_user_id`、`deliver_from_user_id`、`deliver_to_user_id`、`pur_user_id`、`prequal_user_id`、`request_user_id`、`contact_user_id`、`recipient_user_id` 等）。
> - `iam_user.organization_id` 即为租户ID，**等价其他表的 `tenant_id`**；但本表**没有 `tenant_id` 字段**，查询本表时必须用 `organization_id = {tenant_id}` 过滤，不能用 `tenant_id`。
> - 任何"涉及修复数据中人员"的需求，都必须先查询 `iam_user` 得到正确的 `id`，再用该 `id` 去更新业务表的人员字段。

| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| iam_user | id | ssrc_rfx_member | user_id | 寻源小组成员用户 |
| iam_user | id | ssrc_evaluate_expert | expert_user_id | 评分专家子账户 |
| iam_user | id | ssrc_rfx_header | pur_user_id / created_by / last_updated_by | 采购联系人、创建人、更新人 |
| iam_user | id | ssrc_rfx_action | process_user_id / deliver_from_user_id / deliver_to_user_id | 处理人、转交人 |
| iam_user | id | ssrc_rf_action | deliver_from_user_id / deliver_to_user_id | 征询单转交人 |
| iam_user | id | ssrc_prequal_header | prequal_user_id | 资格预审人 |
| iam_user | id | ssrc_prequal_line | user_id | 资审成员 |
| iam_user | id | 任意业务表 | created_by / last_updated_by | 创建人/更新人（审计字段，几乎每张表都有） |

### 1.5. 公司信息关联
| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| hpfm_company | company_id | ssrc_rfx_header | company_id | 询价单的采购方公司 |
| hpfm_company | company_id | ssrc_rfx_line_supplier | supplier_company_id | 询价单供应商行的供应商公司 |
| hpfm_company | company_id | ssrc_rfx_quotation_header | supplier_company_id | 报价单的供应商公司 |

### 2. 询价单头与扩展/子表
| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| ssrc_rfx_header | rfx_header_id | ssrc_rfx_header_expand | rfx_header_id | 询价单头拓展，1对1 |
| ssrc_rfx_header | rfx_header_id | ssrc_rfx_line_item | rfx_header_id | 询价单物料行，1对多 |
| ssrc_rfx_header | rfx_header_id | ssrc_rfx_line_supplier | rfx_header_id | 询价单供应商行，1对多 |
| ssrc_rfx_header | rfx_header_id | ssrc_rfx_member | rfx_header_id | 寻源小组成员，1对多 |
| ssrc_rfx_header | template_id | ssrc_source_template | template_id | 关联寻源模板，多对1 |

### 3. 报价单关联
| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| ssrc_rfx_header | rfx_header_id | ssrc_rfx_quotation_header | rfx_header_id | 询价单下的报价单，1对多 |
| ssrc_rfx_quotation_header | quotation_header_id | ssrc_rfx_quotation_line | quotation_header_id | 报价单行，1对多 |
| ssrc_rfx_line_item | rfx_line_item_id | ssrc_rfx_quotation_line | rfx_line_item_id | 报价行关联询价物料行 |
| ssrc_rfx_line_supplier | rfx_line_supplier_id | ssrc_rfx_quotation_header | rfx_line_supplier_id | 供应商行关联报价单头 |

### 4. 资格预审关联
| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| ssrc_rfx_header | rfx_header_id | ssrc_prequal_header | rfx_header_id | 资格预审头，1对1 |
| ssrc_prequal_header | prequal_header_id | ssrc_prequal_line | prequal_header_id | 资格预审行（按供应商），1对多 |

### 5. 评分关联
| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| ssrc_rfx_header | rfx_header_id | ssrc_evaluate_expert | source_header_id | 评分专家，需加 source_from='RFX' |
| ssrc_rfx_header | rfx_header_id | ssrc_evaluate_indic | source_header_id | 评分要素，需加 source_from='RFX' |
| ssrc_rfx_header | rfx_header_id | ssrc_evaluate_score | source_header_id | 评分头（供应商维度），需加 source_from='RFX' |
| ssrc_rfx_quotation_header | quotation_header_id | ssrc_evaluate_score | quotation_header_id | 报价单与评分头，1对1 |
| ssrc_evaluate_score | evaluate_score_id | ssrc_evaluate_score_line | evaluate_score_id | 评分行，1对多 |
| ssrc_evaluate_indic | evaluate_indic_id | ssrc_evaluate_score_line | evaluate_indic_id | 评分要素与评分行 |
| ssrc_evaluate_expert | evaluate_expert_id | ssrc_evaluate_score | evaluate_expert_id | 专家与评分头 |

### 6. 评分汇总关联
| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| ssrc_rfx_header | rfx_header_id | ssrc_evaluate_summary | source_header_id | 评分汇总，需加 source_from='RFX' |
| ssrc_rfx_quotation_header | quotation_header_id | ssrc_evaluate_summary | quotation_header_id | 报价单与评分汇总，1对1 |

### 7. 寻源结果关联
| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| ssrc_rfx_header | rfx_header_id | ssrc_source_result | source_header_id | 寻源结果，需加 source_from='RFX' |
| ssrc_rfx_quotation_line | quotation_line_id | ssrc_source_result | quotation_line_id | 报价行与寻源结果 |
| ssrc_rfx_line_item | rfx_line_item_id | ssrc_source_result | source_line_item_id | 询价物料行与寻源结果 |

### 7.5 寻源结果变更历史关联
| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| ssrc_source_result | result_id | ssrc_source_result_change_history | source_result_id | 寻源结果变更历史，仅在释放被订单错误占用的寻源结果时操作 |

### 8. 征询单关联
| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| ssrc_rf_header | rf_header_id | ssrc_rf_conf_rule | rf_header_id | 征询单配置规则，1对1 |
| ssrc_rf_header | rf_header_id | ssrc_rf_line_item | rf_header_id | 征询单物料行，1对多 |
| ssrc_rf_header | rf_header_id | ssrc_rf_line_supplier | rf_header_id | 征询单供应商行，1对多 |
| ssrc_rf_line_item | rf_line_item_id | ssrc_rf_item_sup_assign | rf_line_item_id | 物料供应商分配，1对多 |
| ssrc_rf_line_supplier | rf_line_supplier_id | ssrc_rf_item_sup_assign | rf_line_supplier_id | 物料供应商分配，1对多 |
| ssrc_rf_line_supplier | rf_line_supplier_id | ssrc_rf_quotation_header | rf_line_supplier_id | 征询单报价头，1对多 |
| hpfm_company | company_id | ssrc_rf_quotation_header | supplier_company_id | 报价单的供应商公司 |

## 注意事项

1. **source_from 过滤（仅用于 `ssrc_evaluate_*` 评分表与 `ssrc_source_result` 寻源结果表的上下文区分）**：
   - `source_from = 'RFX'`：**询价单**上下文，且**新招标单（BID开头）同样使用 `'RFX'`**（新招标与询价单共用同一上下文，不要写成 `'BID'`）
   - `source_from = 'BID'`：**老招标**上下文（老招标几乎已不再使用，无特殊说明时一律按 `'RFX'` 处理）
   - `source_from = 'RFI'`：信息征询单（RFI开头）
   - `source_from = 'RFP'`：方案征询单（RFP开头）
   - ⚠️ 注意：`ssrc_rfx_header.source_from` 是**单据来源**（手工新建/申请转单/立项转单等），**不是**区分询价单/新招标的字段；区分字段是 `ssrc_rfx_header.secondary_source_category`（新招标 = `'NEW_BID'`）
2. **tenant_id 过滤**：所有表均需加 `tenant_id` 条件过滤租户数据（通过 `hpfm_tenant` 查询获取具体值）。
3. **1对1 关系**：`ssrc_rfx_header` ↔ `ssrc_rfx_header_expand`；`ssrc_rfx_quotation_header` ↔ `ssrc_evaluate_score`（同一供应商同一轮）；`ssrc_rfx_quotation_header` ↔ `ssrc_evaluate_summary`。
4. **状态同步**：`ssrc_rfx_header.rfx_status` 与 `ssrc_rfx_header_expand.rfx_real_status` 必须同步更新。修改询价单状态时，必须同时 UPDATE 两张表，否则会导致状态不一致。
5. **延时消息**：当询价单状态回退至"报价中"(IN_QUOTATION)时，必须插入 `spfm_pending_message` 延时消息，确保报价截止时间到达后系统自动刷新状态。
