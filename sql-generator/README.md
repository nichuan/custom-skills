# SRM SQL Generator Skill

## 概述

本 Skill 是专门为 SRM(Supplier Relationship Management)采购寻源系统设计的 SQL 查询生成助手。基于 Anthropic Skill 设计原则,采用"渐进式披露"和"精简上下文"的核心策略,能够快速生成符合 SRM 业务逻辑的准确 SQL 查询。

## 核心特性

### 1. 渐进式披露
- 仅在需要时加载详细的表结构,避免一次性加载全量表结构导致上下文臃肿
- 通过 `table_meta.md` 快速匹配表名,按需从 `table_detail/` 加载详细结构

### 2. 精简上下文
- 使用极简元数据(表名+核心字段+关联键)进行快速匹配
- 详细结构仅在 SQL 生成时按需加载,保持上下文精简

### 3. 高度可扩展
- 新增表只需在 `table_detail` 中创建对应的 `.md` 文件
- 无需修改 SKILL.md,符合 Skill 的低维护原则

### 4. 维护成本低
- 仅需维护高频使用的核心表和字段
- 低频表仅在 `table_meta.md` 中记录,详细结构按需补充

## 目录结构

```
sql-generator/
├── SKILL.md                                    # Skill 入口文件(必填)
├── README.md                                   # 本文件
├── skill.json                                 # Skill 配置文件
├── references/                                 # SRM系统参考文档目录
│   ├── table_meta.md                           # SRM表极简元数据
│   ├── relations.md                           # SRM表关联关系
│   ├── sql_templates.md                       # SQL 通用模板
│   ├── columns_202603131733.md                # 历史字段快照
│   └── table_detail/                          # SRM单表详细结构
│       ├── hpfm_tenant.md                     # 租户表
│       ├── ssrc_rfx_header.md                 # 询价单头表
│       ├── ssrc_rfx_header_expand.md          # 询价单扩展表
│       ├── ssrc_rfx_line_item.md              # 询价单行物料表
│       ├── ssrc_rfx_line_supplier.md          # 询价单行供应商表
│       ├── ssrc_rfx_member.md                 # 询价单成员表
│       ├── ssrc_rfx_quotation_header.md       # 报价单头表
│       ├── ssrc_rfx_quotation_line.md         # 报价单行表
│       ├── ssrc_evaluate_expert.md            # 评分专家表
│       ├── ssrc_evaluate_indic.md             # 评分指标表
│       ├── ssrc_evaluate_score.md             # 评分表
│       ├── ssrc_evaluate_score_line.md        # 评分行表
│       ├── ssrc_evaluate_summary.md           # 评分汇总表
│       ├── ssrc_prequal_header.md             # 资格预审头表
│       ├── ssrc_prequal_line.md               # 资格预审行表
│       ├── ssrc_source_result.md              # 寻源结果表
│       └── ssrc_source_template.md            # 寻源模板表
├── assets/                                     # 资源文件目录
│   └── sql_template_examples/                 # SQL 示例文件
│       ├── user_order_analysis.sql
│       ├── product_sales_analysis.sql
│       ├── user_purchase_frequency.sql
│       └── product_category_statistics.sql
└── scripts/                                    # 脚本目录(可选)
```

## 快速开始

### 基本使用

本Skill专门处理SRM采购寻源系统的SQL需求，当用户提出以下需求时自动触发:

1. **询价单查询**: "租户SRM-AUX查询询价单"
2. **报价单分析**: "生成SRM-AUX租户近7天的报价统计"
3. **关联关系查询**: "列出询价单表和报价单表的关联关系"
4. **数据修复**: "修复报价单状态不一致的数据"
5. **评分统计**: "统计专家评分情况和排名"

### 工作流程

1. **识别涉及的表**: 从用户需求中提取表名,对照 `table_meta.md` 确认表是否存在
2. **按需加载详细结构**: 仅读取 `table_detail/[表名].md` 文件
3. **补充关联关系**: 参考 `relations.md` 确认表之间的关联键
4. **应用 SQL 模板**: 从 `sql_templates.md` 中匹配适用的通用模板
5. **生成/调整 SQL**: 结合表结构、关联关系和模板,生成符合语法的 SQL
6. **标注信息**: 在 SQL 注释中标注使用的表、关联关系和核心字段

## 核心文件说明

### SKILL.md

Skill 的入口文件，专门为SRM系统优化，定义了:
- Skill 的基本信息(name, description) - 明确SRM系统定位
- 使用流程和执行步骤 - 针对SRM业务场景设计
- 核心规则(SQL生成规则、上下文加载规则、准确性保障) - 符合SRM业务规范
- 参考文件指引 - 涵盖SRM系统所有核心表
- 输出格式和常见场景 - 基于SRM实际业务需求

### references/table_meta.md

存储SRM系统的极简表元数据:
- 表名(按SRM业务模块分类)
- 主键(业务主键标识)
- 核心字段(3-5个高频业务字段)
- 关联键(外键，标注关联业务表)

示例:
```markdown
### 询价单
- **ssrc_rfx_header**: rfx_header_id(主键)、tenant_id(关联hpfm_tenant)、rfx_num(单号)、rfx_status(状态)、rfx_title(标题)

### 报价单
- **ssrc_rfx_quotation_header**: quotation_header_id(主键)、rfx_header_id(关联ssrc_rfx_header)、tenant_id、supplier_company_id、quotation_status(报价状态)
```

### references/table_detail/[表名].md

存储单表的详细结构:
- 完整字段列表
- 字段类型和说明
- 索引信息
- 常用查询场景
- 注意事项

### references/relations.md

存储表之间的关联关系:
- 关联类型(1:1, 1:N, N:M)
- 关联键说明
- SQL 关联示例

### references/sql_templates.md

存储常用的 SQL 模板:


### assets/sql_template_examples/[场景名].sql

存储常用的 SQL 示例:
- 使用清晰的命名描述业务场景
- 在文件头部添加注释说明业务逻辑

## 扩展指南

### 新增表

1. 在 `table_meta.md` 中添加表的极简元数据
2. 创建 `references/table_detail/[表名].md` 文件
3. 如有高频关联,在 `relations.md` 中补充关联关系

### 新增 SQL 模板

1. 将通用 SQL 模板添加到 `sql_templates.md`
2. 按模板类型分类(如: 时间过滤、关联查询、聚合统计)
3. 提供清晰的占位符说明

### 新增 SQL 示例

1. 在 `assets/sql_template_examples/` 中创建 `[场景名].sql`
2. 使用清晰的命名描述业务场景
3. 在文件头部添加注释说明业务逻辑

## 使用示例

### 示例1: 查询租户SRM-AUX的询价单

**用户请求**: "生成查询租户SRM-AUX询价单的SQL，统计最近7天的数据"

**Skill 处理**:
1. 从 `table_meta.md` 识别涉及的表: `hpfm_tenant`, `ssrc_rfx_header`
2. 加载 `table_detail/hpfm_tenant.md` 和 `table_detail/ssrc_rfx_header.md`
3. 从 `relations.md` 确认关联关系: `hpfm_tenant.tenant_id` ↔ `ssrc_rfx_header.tenant_id`
4. 从 `sql_templates.md` 匹配时间过滤模板
5. 生成 SQL:

```sql
-- 业务场景: 查询SRM-AUX租户近7天询价单
-- 涉及表: hpfm_tenant, ssrc_rfx_header
-- 关联关系: hpfm_tenant.tenant_id = ssrc_rfx_header.tenant_id
-- 核心字段: tenant_num(租户编码), rfx_num(单号), rfx_status(状态), rfx_title(标题), quotation_start_date(报价开始时间)

SELECT
    t.tenant_num,
    t.tenant_name,
    r.rfx_header_id,
    r.rfx_num,
    r.rfx_status,
    r.rfx_title,
    r.quotation_start_date,
    r.quotation_end_date,
    r.create_time
FROM hpfm_tenant t
INNER JOIN ssrc_rfx_header r ON t.tenant_id = r.tenant_id
WHERE t.tenant_num = 'SRM-AUX'
  AND r.create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND r.enabled_flag = 1
ORDER BY r.create_time DESC;
```

### 示例2: 报价单与询价单关联分析

**用户请求**: "查询SRM-AUX租户询价单对应的报价情况"

**Skill 处理**:
1. 从 `table_meta.md` 识别涉及的表: `ssrc_rfx_header`, `ssrc_rfx_quotation_header`, `ssrc_rfx_line_supplier`
2. 加载相关表的详细结构
3. 从 `relations.md` 确认关联关系
4. 生成关联查询SQL

### 示例3: 查询SRM表关联关系

**用户请求**: "列出询价单表和报价单表的关联关系"

**Skill 处理**:
1. 从 `relations.md` 查找 `ssrc_rfx_header` 和 `ssrc_rfx_quotation_header` 的关联
2. 输出业务关联关系:

```markdown
### 询价单 → 报价单关联
- **ssrc_rfx_header.rfx_header_id** ↔ **ssrc_rfx_quotation_header.rfx_header_id** (1:N)
  - 业务说明: 一个询价单可以对应多个供应商的报价单
  - 关联键: rfx_header_id (询价单ID)
  - 关联类型: 一对多

- **ssrc_rfx_header.tenant_id** ↔ **ssrc_rfx_quotation_header.tenant_id** (1:1)
  - 业务说明: 同租户数据关联
  - 关联键: tenant_id (租户ID)
  - 关联类型: 一对一
```

## 最佳实践

### SQL 生成规则
- 必须先确认表关联键的正确性(参考 `relations.md`)
- 使用明确的表别名避免字段歧义
- 时间范围过滤优先使用 `sql_templates.md` 中的模板
- 聚合统计时明确 GROUP BY 字段和聚合函数
- 生成的 SQL 必须包含关键注释说明

### 上下文加载规则
- 严格按需加载,只读取 `table_detail/[表名].md` 中涉及的表
- 不加载全量表结构,保持上下文精简
- 如果某个表的详细结构不存在,仅使用 `table_meta.md` 中的核心字段

### 准确性保障
- 生成 SQL 前必须验证:
  - 表名拼写是否正确(对照 `table_meta.md`)
  - 关联键是否匹配(对照 `relations.md`)
  - 字段是否存在于对应表(对照 `table_detail/[表名].md`)
- 对于复杂的查询逻辑,建议分步生成并验证

## 维护建议

### 定期更新
- 定期检查 `table_meta.md` 中的表是否仍然高频使用
- 定期更新 `table_detail/[表名].md` 中的字段信息
- 定期清理低频表的详细结构

### 优化建议
- 如果发现某类 SQL 生成频繁出错,补充对应的表详细结构/SQL 模板
- 如果用户常问某几个表的关联,把这些关联补充到 `relations.md` 中
- 如果发现某些字段不再使用,从详细结构中移除,保持轻量化

## 版本历史

### v1.0 (2026-03-13)
- 初始版本
- 包含 9 个核心表的详细结构
- 提供常用 SQL 模板和示例
- 完全符合 Anthropic Skill 设计原则

## 许可证

本 Skill 采用 MIT 许可证。
