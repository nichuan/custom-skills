---
name: sql-generator-skill-optimization
overview: 对 SRM SQL 生成技能进行全面优化，解决寻源结果删除逻辑不精确、表定义缺失、征询单关联不全等问题。
todos:
  - id: fix-sql-templates
    content: 拆分sql_templates.md模板2.6.5为两个场景，补充占位符，调整后续编号
    status: pending
  - id: add-skill-rule
    content: 在SKILL.md核心规则中新增"寻源结果删除规则"
    status: pending
    dependencies:
      - fix-sql-templates
  - id: fix-source-result-detail
    content: 补充ssrc_source_result.md缺失的关键字段(receipts_status等)
    status: pending
  - id: create-change-history-detail
    content: 新建ssrc_source_result_change_history.md表详细结构
    status: pending
  - id: fix-table-meta
    content: 补充table_meta.md中change_history表和RF子表元数据
    status: pending
    dependencies:
      - create-change-history-detail
  - id: fix-relations
    content: 补充relations.md中征询单(RF)关联关系和change_history关联
    status: pending
---

## 用户需求

检查当前 sql-generator 技能项目有无明显需要优化改动的地方，并列出改进项。用户已知核心问题：每次生成寻源结果删除语句时，总会默认生成 `ssrc_source_result_change_history` 的删除，但实际只有"寻源结果被订单错误占用"场景才需要删除该表数据，其余删除寻源结果的场景只需处理 `ssrc_source_result` 表。

## 发现的问题清单（共7项）

1. **[核心]** SQL模板2.6.5"释放寻源结果占用"默认包含 `ssrc_source_result_change_history` 的查询和删除 — 应拆分为两个独立场景模板：普通删除寻源结果（仅处理ssrc_source_result）和订单占用释放（需同时处理change_history）
2. **[核心]** SKILL.md 缺少"寻源结果删除规则" — 需要新增明确规则，区分普通删除和订单占用释放两种场景
3. **[中等]** `ssrc_source_result.md` 表详细结构缺少模板2.6.5已使用的关键字段（receipts_status、occupation_quantity、source_result_execute_status、result_execution_strategy）
4. **[中等]** `ssrc_source_result_change_history` 表缺少元数据(table_meta.md)和详细结构(table_detail/)定义 — 模板引用了该表但无任何定义
5. **[中等]** `relations.md` 缺少征询单(RF)相关的表关联关系 — 只有询价单(RFX)的关联，征询单部分的关联完全缺失
6. **[低]** `table_meta.md` 缺少征询单(RF)的多个子表元数据（ssrc_rf_quotation_header、ssrc_rf_line_item、ssrc_rf_line_supplier、ssrc_rf_item_sup_assign等），虽table_detail/中已有
7. **[低]** `sql_templates.md` 占位符说明中缺少寻源结果相关占位符（result_id、history_id）

## 改动范围

- 修改：SKILL.md、sql_templates.md、table_meta.md、relations.md、ssrc_source_result.md
- 新增：ssrc_source_result_change_history.md（table_detail/）

## 改动方案

### 核心改动：拆分寻源结果删除模板

将 sql_templates.md 中模板 2.6.5"释放寻源结果占用"拆分为两个独立模板：

1. **2.6.5 删除寻源结果** — 普通场景，仅处理 `ssrc_source_result` 表的DELETE操作
2. **2.6.6 释放寻源结果占用（订单占用场景）** — 仅当寻源结果被订单错误占用时使用，同时处理 `ssrc_source_result_change_history` 和 `ssrc_source_result` 的UPDATE释放

同时在 SKILL.md 核心规则中新增"寻源结果删除规则"，明确两种场景的区分条件。

### 附属改动

- 补全 `ssrc_source_result.md` 中缺失的 receipts_status 等关键字段
- 新增 `ssrc_source_result_change_history.md` 表详细结构文件
- 在 `table_meta.md` 中补充 `ssrc_source_result_change_history` 和征询单(RF)子表元数据
- 在 `relations.md` 中补充征询单(RF)相关表关联关系和寻源结果变更历史关联
- 在 `sql_templates.md` 占位符说明中补充 result_id、history_id

### 涉及文件

```
sql-generator/
├── SKILL.md                                              # [MODIFY] 新增"寻源结果删除规则"
├── references/
│   ├── sql_templates.md                                  # [MODIFY] 拆分模板2.6.5、补充占位符、原2.6.6及后续编号顺延
│   ├── table_meta.md                                     # [MODIFY] 补充ssrc_source_result_change_history和RF子表元数据
│   ├── relations.md                                      # [MODIFY] 补充RF表关联关系和change_history关联
│   └── table_detail/
│       ├── ssrc_source_result.md                         # [MODIFY] 补充receipts_status等关键字段
│       └── ssrc_source_result_change_history.md          # [NEW] 新建表详细结构
```