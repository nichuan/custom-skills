# 核心表关联关系

## 主业务流程关联链

```
hpfm_tenant (租户)
    └── ssrc_rfx_header (询价单头) [tenant_id]
            ├── ssrc_rfx_header_expand (询价单头拓展) [rfx_header_id]
            ├── ssrc_rfx_line_item (询价单物料行) [rfx_header_id]
            ├── ssrc_rfx_line_supplier (询价单供应商行) [rfx_header_id]
            ├── ssrc_rfx_member (寻源小组成员) [rfx_header_id]
            ├── ssrc_source_template (寻源模板) [template_id]
            ├── ssrc_prequal_header (资格预审头) [rfx_header_id]
            │       └── ssrc_prequal_line (资格预审行) [prequal_header_id]
            ├── ssrc_rfx_quotation_header (报价单头) [rfx_header_id]
            │       └── ssrc_rfx_quotation_line (报价单行) [quotation_header_id]
            ├── ssrc_evaluate_expert (评分专家) [source_header_id]
            ├── ssrc_evaluate_indic (评分要素) [source_header_id]
            ├── ssrc_evaluate_score (评分头) [source_header_id]
            │       └── ssrc_evaluate_score_line (评分行) [evaluate_score_id]
            ├── ssrc_evaluate_summary (评分汇总) [source_header_id]
            └── ssrc_source_result (寻源结果) [source_header_id]
```

## 详细关联关系

### 1. 租户与询价单
| 主表 | 主表字段 | 关联表 | 关联字段 | 说明 |
|------|----------|--------|----------|------|
| hpfm_tenant | tenant_id | ssrc_rfx_header | tenant_id | 租户下的询价单 |
| hpfm_tenant | tenant_id | hpfm_company | tenant_id | 租户下的公司信息 |

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

## 注意事项

1. **source_from 过滤**：`ssrc_evaluate_expert`、`ssrc_evaluate_indic`、`ssrc_evaluate_score`、`ssrc_evaluate_summary`、`ssrc_source_result` 均需加 `source_from = 'RFX'` 条件（区分询价单与招标单）。
2. **tenant_id 过滤**：所有表均需加 `tenant_id` 条件过滤租户数据（通过 `hpfm_tenant` 查询获取具体值）。
3. **1对1 关系**：`ssrc_rfx_header` ↔ `ssrc_rfx_header_expand`；`ssrc_rfx_quotation_header` ↔ `ssrc_evaluate_score`（同一供应商同一轮）；`ssrc_rfx_quotation_header` ↔ `ssrc_evaluate_summary`。
4. **状态同步**：`ssrc_rfx_header.rfx_status` 与 `ssrc_rfx_header_expand.rfx_real_status` 必须同步更新。修改询价单状态时，必须同时 UPDATE 两张表，否则会导致状态不一致。
