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
- 按租户分析SRM-AUX租户的询价单、报价单、征询单、评分等数据
- 修复SRM数据问题或生成数据修复SQL

### 典型触发语句
- "租户SRM-AUX查询询价单"
- "参考已有SQL模板,修复报价单数据"
- "列出询价单表和报价单表的关联关系"
- "生成SRM-AUX租户的单据RFX2026022600014的评分专家查询SQL"
- "查询资格预审表的字段结构"
- "修复征询单RF2026010100001的报价时间，恢复为报价中状态"

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
- 生成的SQL必须包含关键注释说明
- **字段命名规则（必须严格遵守）**:
  - 所有字段名必须使用**下划线格式**（snake_case），不能使用驼峰格式（camelCase）
  - 表名必须使用下划线格式，例如：`ssrc_rfx_quotation_line`（不是 `ssrcRfxQuotationLine`）
  - 字段名必须使用下划线格式，例如：
    - `quotation_line_id`（不是 `quotationLineId`）
    - `quotation_header_id`（不是 `quotationHeaderId`）
    - `rfx_header_id`（不是 `rfxHeaderId`）
    - `supplier_company_name`（不是 `supplierCompanyName`）
    - `attribute_decimal5`（不是 `attributeDecimal5`）
    - `attribute_datetime5`（不是 `attributeDatetime5`）
- **拓展字段规则（attribute前缀）**:
  - SRM系统每个表都包含标准的拓展字段，以 `attribute` 开头
  - 拓展字段在 `table_detail/[表名].md` 的表结构中**不会体现**，属于隐含字段
  - 常见的拓展字段格式：
    - 数字类型：`attribute_decimal1` ~ `attribute_decimal10`
    - 时间类型：`attribute_datetime1` ~ `attribute_datetime10`
    - 文本类型：`attribute_char1` ~ `attribute_char10`
    - 长文本类型：`attribute_varchar1` ~ `attribute_varchar10`
  - 使用拓展字段时，直接按上述命名规则构造字段名，无需查询表结构
  - 示例：
    ```sql
    SELECT
        ql.attribute_decimal5,
        ql.attribute_datetime5,
        ql.attribute_decimal6,
        ql.attribute_datetime6
    FROM ssrc_rfx_quotation_line ql
    WHERE ql.attribute_decimal5 IS NULL;
    ```
- **UPDATE/DELETE 安全规则（必须严格遵守）**:
  - UPDATE 和 DELETE 必须是单表操作，必须包含 WHERE 条件
  - **WHERE 条件必须使用 `tenant_id` + 表主键**，禁止使用任何非主键字段（包括外键、业务单号等）
  - **表主键识别规则**：
    - 主键是表的唯一标识字段，可通过 `references/table_detail/[表名].md` 查询
    - 常见表的主键：
      - `ssrc_rfx_header`: `rfx_header_id`
      - `ssrc_rfx_header_expand`: `rfx_header_expand_id`（注意：不是 `rfx_header_id`）
      - `ssrc_rf_header`: `rf_header_id`
      - `ssrc_rfx_quotation_header`: `quotation_header_id`
      - `hpfm_tenant`: `tenant_id`
  - **多步查询规则**：当更新非主表（如拓展表）时，必须通过关联字段查询出该表的主键
  - 当用户提供的是业务单号或外键而非主键时，必须分两步执行：
    1. **查询主键**: 通过业务单号或外键查出目标表的主键ID
    2. **修改**: 用查到的主键ID 构造 UPDATE/DELETE 语句（必须使用 `tenant_id + 主键`）
  - 错误示例：
    ```sql
    -- ❌ 错误：使用外键作为条件
    UPDATE ssrc_rfx_header_expand 
    SET rfx_real_status = 'CHECK_PENDING' 
    WHERE tenant_id = ? AND rfx_header_id = ?;
    
    -- ❌ 错误：使用业务单号作为条件
    UPDATE ssrc_rfx_header 
    SET rfx_status = 'CHECK_PENDING' 
    WHERE tenant_id = ? AND rfx_num = 'RFX2026022400003';
    ```
  - 正确示例：
    ```sql
    -- 步骤1: 查询询价单头表主键（通过业务单号）
    SELECT rfx_header_id 
    FROM ssrc_rfx_header 
    WHERE tenant_id = ? AND rfx_num = 'RFX2026022400003';
    
    -- 步骤2: 查询拓展表主键（通过外键）
    SELECT rfx_header_expand_id 
    FROM ssrc_rfx_header_expand 
    WHERE tenant_id = ? AND rfx_header_id = ?;
    
    -- 步骤3: 更新主表（使用主键）
    UPDATE ssrc_rfx_header 
    SET rfx_status = 'CHECK_PENDING' 
    WHERE tenant_id = ? AND rfx_header_id = ?;
    
    -- 步骤4: 更新拓展表（使用主键）
    UPDATE ssrc_rfx_header_expand 
    SET rfx_real_status = 'CHECK_PENDING' 
    WHERE tenant_id = ? AND rfx_header_expand_id = ?;
    ```
- **询价单状态同步规则（必须严格遵守）**:
  - `ssrc_rfx_header.rfx_status` 与 `ssrc_rfx_header_expand.rfx_real_status` 必须保持同步
  - 修改询价单状态时，必须同时更新两张表，缺一不可：
    ```sql
    -- 同步更新主表状态（使用主键）
    UPDATE ssrc_rfx_header SET rfx_status = '{new_status}' WHERE tenant_id = ? AND rfx_header_id = ?;
    -- 同步更新扩展表状态（必须查询并使用主键）
    -- 步骤2.1: 先查询拓展表主键
    SELECT rfx_header_expand_id FROM ssrc_rfx_header_expand WHERE tenant_id = ? AND rfx_header_id = ?;
    -- 步骤2.2: 用拓展表主键更新
    UPDATE ssrc_rfx_header_expand SET rfx_real_status = '{new_status}' WHERE tenant_id = ? AND rfx_header_expand_id = ?;
    ```
- **征询单类型识别规则（必须严格遵守）**:
  - 征询单根据单号前缀判断类型，`source_from` 字段必须正确设置：
    - RFI开头（如RFI2025112000002）：信息征询，`source_from = 'RFI'`
    - RFP开头（如RFP2025112000002）：方案征询，`source_from = 'RFP'`
  - 查询评分相关表（`ssrc_evaluate_expert`、`ssrc_evaluate_score`、`ssrc_evaluate_score_line`）时，必须使用正确的 `source_from` 值
  - 错误示例：
    ```sql
    -- ❌ 错误：使用 'RF' 作为 source_from
    SELECT * FROM ssrc_evaluate_expert WHERE source_header_id = ? AND source_from = 'RF';
    ```
  - 正确示例：
    ```sql
    -- ✅ 正确：根据单号前缀判断 source_from
    -- RFI2025112000002 -> source_from = 'RFI'
    SELECT * FROM ssrc_evaluate_expert WHERE source_header_id = ? AND source_from = 'RFI';
    -- RFP2025112000002 -> source_from = 'RFP'
    SELECT * FROM ssrc_evaluate_expert WHERE source_header_id = ? AND source_from = 'RFP';
    ```

### 上下文加载规则
- 严格按需加载,只读取 `table_detail/[表名].md` 中涉及的表
- 不加载全量表结构,保持上下文精简
- 如果某个表的详细结构不存在,仅使用 `table_meta.md` 中的核心字段

### 准确性保障
- 生成SQL前必须验证:
  - 表名拼写是否正确(对照 `table_meta.md`)
  - 关联键是否匹配(对照 `relations.md`)
  - 字段是否存在于对应表(对照 `table_detail/[表名].md`)
  - **字段命名是否符合下划线格式**（snake_case）
  - **拓展字段（attribute前缀）是否按规则命名**
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
  - 按业务场景分类的SQL模板，包含三大类：
    - **通用基础查询模板**: 租户、公司等基础信息查询
    - **询价单（RFX）SQL模板**: 询价单相关的查询、统计和数据修复
    - **征询单（RF）SQL模板**: 征询单相关的查询和数据修复
  - 每个模板都包含业务场景说明、占位符说明和状态值参考
  - 用途: 快速生成符合规范的SQL片段

### 历史字段信息
- **历史字段快照**: `references/columns_202603131733.md`
  - 数据库字段的历史快照，用于字段变更追踪
  - 用途: 当需要了解字段历史变更时参考

### SQL示例（可选）
- **完整SQL示例**: `assets/sql_template_examples/[场景名].sql`
  - 按SRM业务场景分类的完整SQL文件
  - 用途: 参考类似业务场景的SQL写法
  - 说明: 按需添加，非必填

## 输出格式

生成的SQL应包含以下信息:
```sql
-- 业务场景: [描述用户需求]
-- 涉及表: [表1, 表2, ...]
-- 关联关系: [表1.key = 表2.key, ...]
-- 核心字段: [主要查询和统计字段]
-- 字段命名: 使用下划线格式（snake_case）
-- 拓展字段: attribute_decimal1~10, attribute_datetime1~10等

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
  4. 确保所有字段使用下划线格式（如 `quotation_line_id`）
  5. 如果使用拓展字段，按 `attribute_decimal1~10` 等规则命名

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
  4. 确保所有字段使用下划线格式
  5. 拓展字段按 attribute 前缀规则命名

### 场景5: 征询单查询与分析
- **业务需求**: 查询租户的征询单数据
- **涉及表**: `ssrc_rf_header`, `ssrc_rf_conf_rule`, `ssrc_rf_quotation_header`
- **关键字段**: `rf_num`(征询单号), `display_rf_status`(显示状态), `current_node`(当前节点), `rf_title`(标题), `quotation_start_date`(报价开始时间)
- **处理流程**:
  1. 从 `sql_templates.md` 匹配征询单查询模板
  2. 结合 `table_detail/ssrc_rf_header.md` 确认字段
  3. 标注租户过滤和状态过滤

### 场景6: 征询单修复
- **业务需求**: 延长征询单报价时间，恢复为"报价中"状态
- **涉及表**: `ssrc_rf_header`, `ssrc_rf_conf_rule`, `hpfm_tenant`
- **关键字段**: `rf_num`(征询单号), `display_rf_status`(显示状态), `current_node`(当前节点), `quotation_end_date`(报价截止时间), `quotation_running_duration`(报价时长)
- **处理流程**:
  1. 从 `sql_templates.md` 查询租户ID
  2. 通过征询单号查询 `rf_header_id` 和 `rf_conf_rule_id`
  3. 同步更新 `ssrc_rf_header` 的状态为 `IN_QUOTATION`
  4. 更新 `ssrc_rf_conf_rule` 的报价截止时间和时长

### 场景7: 征询单状态修复为评分中
- **业务需求**: 将征询单状态修复为"评分中"，重新进行评分
- **涉及表**: `ssrc_rf_header`, `ssrc_evaluate_expert`, `ssrc_evaluate_score`, `ssrc_evaluate_score_line`
- **关键字段**: `rf_num`(征询单号), `display_rf_status`(显示状态), `scored_status`(评分状态), `source_from`(来源类型)
- **征询单类型说明**:
  - RFI开头（如RFI2025112000002）：信息征询，`source_from = 'RFI'`
  - RFP开头（如RFP2025112000002）：方案征询，`source_from = 'RFP'`
- **处理流程**:
  1. 从 `sql_templates.md` 查询租户ID和征询单信息
  2. 根据征询单号前缀判断类型（RFI/RFP），确定 `source_from` 值
  3. 查询专家表和评分表数据（使用正确的 `source_from`）
  4. 更新征询单状态为 `SCORING`
  5. 重置专家状态为 `NEW`
  6. 删除已存在的评分数据

### 场景8: 修复供应商物料分配
- **业务需求**: 修复询价单中供应商的物料分配情况，将未邀请的物料设置为已邀请状态
- **涉及表**: `ssrc_rfx_header`, `ssrc_rfx_line_supplier`, `ssrc_rfx_item_sup_assign`
- **关键字段**: `rfx_num`(询价单号), `supplier_company_id`(供应商公司ID), `invite_flag`(邀请标识)
- **处理流程**:
  1. 从 `sql_templates.md` 查询租户ID和询价单信息
  2. 通过供应商编码查询 `rfx_line_supplier_id`
  3. 查询该供应商的物料分配情况
  4. 更新 `invite_flag` 为 1（已邀请）
- **说明**: `invite_flag = 1` 表示已邀请，`invite_flag = 0` 表示未邀请

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
2. **分类组织**: 按SRM业务模块分类，当前已分为三大类：
   - **通用基础查询模板**: 租户、公司等基础信息查询
   - **询价单（RFX）SQL模板**: 包含询价单基础查询、公司信息查询、报价单查询、评分查询、聚合统计、数据修复等子分类
   - **征询单（RF）SQL模板**: 包含征询单基础查询、报价查询、数据修复等子分类
3. **提供说明**:
   - 每个模板必须包含**业务场景**说明
   - 提供清晰的占位符说明（在 `## 占位符说明` 部分）
   - 提供状态值参考（在 `## 附录：状态值参考` 部分）
   - SQL格式需美观，关键字大写，字段换行对齐

### 新增SRM业务SQL示例
1. **创建示例**: 在 `assets/sql_template_examples/` 中创建 `[业务场景].sql`
2. **命名规范**: 使用SRM业务场景命名，如:
   - `rfx_supplier_analysis.sql` (询价单供应商分析)
   - `quotation_comparison.sql` (报价单对比分析)
   - `expert_scoring_statistics.sql` (专家评分统计)
3. **注释说明**: 在文件头部添加详细的业务逻辑注释


