---
name: sql-generator
description: 基于SRM采购寻源系统的SQL生成助手，支持快速生成业务查询SQL、调整现有SQL、查询表结构及关联关系。采用渐进式披露设计，按需加载表详细结构，避免上下文臃肿。专门针对租户的询价单、报价单、评分、资格预审等核心业务场景。
---

# SQL生成助手

## 使用流程

本Skill专门针对SRM采购寻源系统的SQL生成需求，当用户提出以下需求时自动触发:

### SRM业务场景
- 生成或修改SRM系统的SQL查询语句
- 查询SRM表结构或表之间的关联关系  
- 基于已有SQL模板调整SRM业务查询逻辑
- 按租户分析SRM-AUX租户的询价单、报价单、评分等数据
- 修复SRM数据问题或生成数据修复SQL

### 典型触发语句
- "租户SRM-AUX查询询价单"
- "参考已有SQL模板,修复报价单数据"
- "列出询价单表和报价单表的关联关系"
- "生成SRM-AUX租户的单据RFX2026022600014的评分专家查询SQL"
- "查询资格预审表的字段结构"

## 执行步骤

1. **识别涉及的表**: 从用户需求中提取SRM表名,对照 `table_meta.md` 确认表是否存在
2. **按需加载详细结构**: 仅读取用户需求中涉及的 `table_detail/[表名].md` 文件
3. **补充关联关系**: 参考 `relations.md` 确认SRM表之间的关联键
4. **应用SQL模板**: 从 `sql_templates.md` 中匹配适用于SRM业务的SQL例子然后改写条件
5. **生成/调整SQL**: 结合SRM表结构、关联关系和模板,生成符合SRM业务逻辑的SQL
6. **标注信息**: 在SQL注释中标注使用的SRM表、关联关系和核心业务字段

## 核心规则

### SQL生成规则
- 必须先确认表关联键的正确性(参考 `relations.md`)
- 使用明确的表别名避免字段歧义
- 聚合统计时明确 GROUP BY 字段和聚合函数
- 生成的SQL必须包含关键注释说明
- 生成的UPDATE/DELETE SQL只能是单表操作，必须包含WHERE条件，且条件只能是tenant_id和主键

### 上下文加载规则
- 严格按需加载,只读取 `table_detail/[表名].md` 中涉及的表
- 不加载全量表结构,保持上下文精简
- 如果某个表的详细结构不存在,仅使用 `table_meta.md` 中的核心字段

### 准确性保障
- 生成SQL前必须验证:
  - 表名拼写是否正确(对照 `table_meta.md`)
  - 关联键是否匹配(对照 `relations.md`)
  - 字段是否存在于对应表(对照 `table_detail/[表名].md`)
- 对于复杂的查询逻辑,建议分步生成并验证

## 参考文件指引

本Skill基于SRM采购寻源系统的数据库结构设计，包含以下参考文件：

### 核心元数据
- **表极简元数据**: `references/table_meta.md`
  - SRM系统的核心表元数据，包括：hpfm_tenant、ssrc_rfx_header、ssrc_rfx_quotation_header等
  - 包含主键、核心字段、关联键信息
  - 用途: 快速匹配表名和确认基本信息

### 表详细信息
- **单表详细结构**: `references/table_detail/[表名].md`
  - 替换 `[表名]` 为具体的表名
  - 包含完整字段列表、字段类型、字段说明、索引信息
  - 示例: `references/table_detail/ssrc_rfx_header.md`
  - 用途: 获取表的完整结构信息

### 关联关系
- **表关联关系**: `references/relations.md`
  - SRM系统表之间的关联键和关联类型
  - 包含询价单、报价单、评分、资格预审等模块的关联关系
  - 用途: 确保多表关联查询的正确性

### SQL模板
- **通用SQL模板**: `references/sql_templates.md`
  - 时间范围过滤、表关联、聚合统计等通用SQL模板
  - 针对SRM业务场景优化的查询模式
  - 用途: 快速生成符合规范的SQL片段

### 历史字段信息
- **历史字段快照**: `references/columns_202603131733.md`
  - 数据库字段的历史快照，用于字段变更追踪
  - 用途: 当需要了解字段历史变更时参考

### SQL示例
- **完整SQL示例**: `assets/sql_template_examples/[场景名].sql`
  - 按SRM业务场景分类的完整SQL文件
  - 用途: 参考类似业务场景的SQL写法

## 输出格式

生成的SQL应包含以下信息:
```sql
-- 业务场景: [描述用户需求]
-- 涉及表: [表1, 表2, ...]
-- 关联关系: [表1.key = 表2.key, ...]
-- 核心字段: [主要查询和统计字段]

SELECT ...
FROM ...
WHERE ...
GROUP BY ...
```

## SRM常见业务场景

### 场景1: 询价单查询与分析
- **业务需求**: 查询租户SRM-AUX的询价单数据
- **涉及表**: `ssrc_rfx_header`, `ssrc_rfx_header_expand`, `hpfm_tenant`
- **关键字段**: `rfx_num`(单号), `rfx_status`(状态), `rfx_title`(标题), `quotation_start_date`(报价开始时间)
- **处理流程**: 
  1. 从 `sql_templates.md` 匹配时间过滤模板
  2. 结合 `table_detail/ssrc_rfx_header.md` 确认时间字段
  3. 标注租户过滤和时间范围

### 场景2: 报价单与询价单关联查询
- **业务需求**: 查询询价单对应的报价情况
- **涉及表**: `ssrc_rfx_header`, `ssrc_rfx_quotation_header`, `ssrc_rfx_line_supplier`
- **关联关系**: `ssrc_rfx_header.rfx_header_id` ↔ `ssrc_rfx_quotation_header.rfx_header_id`
- **处理流程**:
  1. 从 `relations.md` 确认询价单-报价单关联关系
  2. 为每个SRM表设置业务相关的别名
  3. 在注释中列出所有业务关联键

### 场景3: 评分统计分析
- **业务需求**: 统计专家评分情况
- **涉及表**: `ssrc_evaluate_expert`, `ssrc_evaluate_score`, `ssrc_evaluate_summary`
- **聚合统计**: 按专家、按指标、按总分统计
- **处理流程**:
  1. 从 `sql_templates.md` 匹配聚合统计模板
  2. 确认 GROUP BY 字段的准确性(专家ID、指标ID等)
  3. 标注评分统计逻辑和排名规则

### 场景4: 资格预审状态查询
- **业务需求**: 查询供应商资格预审进度
- **涉及表**: `ssrc_prequal_header`, `ssrc_prequal_line`
- **状态字段**: `prequal_status`, `prequal_line_status`
- **处理流程**:
  1. 识别状态字段和日期字段
  2. 应用状态过滤模板
  3. 生成带状态说明的查询SQL

## 错误处理与边界情况

### SRM表不存在
- **情况**: 请求的SRM表在 `table_meta.md` 中不存在
- **处理**: 建议用户确认表名是否正确，或提供表的业务描述以便匹配

### 关联关系未定义
- **情况**: SRM表关联关系在 `relations.md` 中未定义且无法推断
- **处理**: 提示用户提供关联键信息，或建议分步查询

### 缺少详细结构
- **情况**: 某个SRM表缺少 `table_detail/[表名].md` 详细结构文件
- **处理**: 使用 `table_meta.md` 中的核心字段生成SQL，并提示用户补充详细结构

### 业务需求模糊
- **情况**: 用户需求过于模糊，需要进一步澄清
- **处理**: 询问具体业务场景，如:
  - 需要查询哪个租户的数据(SRM-AUX等)
  - 需要分析哪个时间范围的数据
  - 需要关注哪些业务状态(询价单状态、报价单状态等)
  - 需要统计哪些业务指标

### 字段变更检测
- **情况**: 用户提到的字段在当前表中不存在
- **处理**: 参考 `columns_202603131733.md` 检查字段历史，提示可能的字段变更

## SRM系统扩展指南

### 新增SRM表
1. **添加元数据**: 在 `table_meta.md` 中添加SRM表的极简元数据
   - 格式: `表名: 主键、核心字段1、核心字段2、关联键`
   - 示例: `ssrc_new_table: new_id(主键)、tenant_id(关联hpfm_tenant)、field1、field2`
2. **创建详细结构**: 创建 `references/table_detail/[表名].md` 文件
   - 包含完整字段列表、类型、说明
   - 注明业务含义和常见查询场景
3. **补充关联关系**: 在 `relations.md` 中补充SRM业务关联关系
   - 说明关联的业务含义
   - 提供关联SQL示例

### 新增SRM业务SQL模板
1. **添加模板**: 将SRM业务通用SQL模板添加到 `sql_templates.md`
2. **分类组织**: 按SRM业务模块分类
   - 询价单相关模板
   - 报价单相关模板  
   - 评分相关模板
   - 资格预审相关模板
3. **提供说明**: 提供清晰的占位符说明和业务场景示例

### 新增SRM业务SQL示例
1. **创建示例**: 在 `assets/sql_template_examples/` 中创建 `[业务场景].sql`
2. **命名规范**: 使用SRM业务场景命名，如:
   - `rfx_supplier_analysis.sql` (询价单供应商分析)
   - `quotation_comparison.sql` (报价单对比分析)
   - `expert_scoring_statistics.sql` (专家评分统计)
3. **注释说明**: 在文件头部添加详细的业务逻辑注释

### 维护字段历史
1. **记录变更**: 当SRM表字段变更时，更新 `columns_202603131733.md`
2. **版本管理**: 定期备份字段快照，便于追踪历史变更
3. **兼容性**: 确保新旧字段的SQL兼容性处理
