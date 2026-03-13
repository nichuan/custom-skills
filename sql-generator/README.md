# SQL Generator Skill

## 概述

本 Skill 是一个高效的 SQL 查询生成助手,基于 Anthropic Skill 设计原则,采用"渐进式披露"和"精简上下文"的核心策略,能够快速生成准确的业务查询 SQL。

## 核心特性

### 1. 渐进式披露
- 仅在需要时加载详细的表结构,避免一次性加载全量表结构导致上下文臃肿
- 通过 `table_meta.md` 快速匹配表名,按需从 `table_detail/` 加载详细结构

### 2. 精简上下文
- 使用极简元数据(表名+核心字段+关联键)进行快速匹配
- 详细结构仅在 SQL 生成时按需加载,保持上下文精简

### 3. 高度可扩展
- 新增表只需在 `table_detail/` 中创建对应的 `.md` 文件
- 无需修改 SKILL.md,符合 Skill 的低维护原则

### 4. 维护成本低
- 仅需维护高频使用的核心表和字段
- 低频表仅在 `table_meta.md` 中记录,详细结构按需补充

## 目录结构

```
sql-generator/
├── SKILL.md                                    # Skill 入口文件(必填)
├── README.md                                   # 本文件
├── references/                                 # 参考文档目录
│   ├── table_meta.md                           # 表极简元数据
│   ├── relations.md                           # 表关联关系
│   ├── sql_templates.md                       # SQL 通用模板
│   └── table_detail/                          # 单表详细结构
│       ├── user.md
│       ├── user_profile.md
│       ├── order.md
│       ├── order_item.md
│       ├── product.md
│       ├── category.md
│       ├── cart.md
│       ├── payment.md
│       ├── logistics.md
│       └── review.md
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

当用户提出以下需求时,本 Skill 会自动触发:

1. "生成查询近7天用户下单金额的SQL"
2. "参考已有SQL模板,调整时间范围为近30天的订单统计"
3. "列出user和order表的关联关系,并生成用户购买频次分析SQL"
4. "根据表结构,生成按商品分类统计销量的SQL"

### 工作流程

1. **识别涉及的表**: 从用户需求中提取表名,对照 `table_meta.md` 确认表是否存在
2. **按需加载详细结构**: 仅读取 `table_detail/[表名].md` 文件
3. **补充关联关系**: 参考 `relations.md` 确认表之间的关联键
4. **应用 SQL 模板**: 从 `sql_templates.md` 中匹配适用的通用模板
5. **生成/调整 SQL**: 结合表结构、关联关系和模板,生成符合语法的 SQL
6. **标注信息**: 在 SQL 注释中标注使用的表、关联关系和核心字段

## 核心文件说明

### SKILL.md

Skill 的入口文件,定义了:
- Skill 的基本信息(name, description)
- 使用流程和执行步骤
- 核心规则(SQL生成规则、上下文加载规则、准确性保障)
- 参考文件指引
- 输出格式和常见场景

### references/table_meta.md

存储所有表的极简元数据:
- 表名
- 主键
- 核心字段(3-5个高频字段)
- 关联键(外键)

示例:
```markdown
- user: id(主键)、user_name、register_time
- order: id(主键)、user_id(关联user.id)、order_no、order_amount、create_time
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
- 时间范围过滤
- 表关联(INNER JOIN, LEFT JOIN)
- 聚合统计(GROUP BY, HAVING)
- 条件过滤(WHERE)
- 排序和分页(ORDER BY, LIMIT)
- 窗口函数(ROW_NUMBER, LAG/LEAD)
- CASE WHEN 判断

### assets/sql_template_examples/[场景名].sql

存储按业务场景分类的完整 SQL 示例:
- 用户订单分析
- 商品销量分析
- 用户购买频次
- 商品分类统计

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

### 示例1: 查询近7天用户订单

**用户请求**: "生成查询近7天用户订单的SQL"

**Skill 处理**:
1. 从 `table_meta.md` 识别涉及的表: user, order
2. 加载 `table_detail/user.md` 和 `table_detail/order.md`
3. 从 `relations.md` 确认关联关系: user.id ↔ order.user_id (1:N)
4. 从 `sql_templates.md` 匹配时间过滤模板
5. 生成 SQL:

```sql
-- 业务场景: 查询近7天用户订单
-- 涉及表: user, order
-- 关联关系: user.id = order.user_id (1:N)
-- 核心字段: user_id, user_name, order_no, order_amount, create_time

SELECT
    u.id AS user_id,
    u.user_name,
    COUNT(o.id) AS order_count,
    SUM(o.order_amount) AS total_amount
FROM user u
INNER JOIN `order` o ON u.id = o.user_id
WHERE o.create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND o.order_status IN (2, 3)
GROUP BY u.id, u.user_name
ORDER BY total_amount DESC;
```

### 示例2: 调整已有SQL的时间范围

**用户请求**: "参考已有SQL模板,调整时间范围为近30天"

**Skill 处理**:
1. 从 `assets/sql_template_examples/user_order_analysis.sql` 加载示例
2. 将 `{days}` 替换为 30
3. 输出调整后的 SQL

### 示例3: 查询表关联关系

**用户请求**: "列出user和order表的关联关系"

**Skill 处理**:
1. 从 `relations.md` 查找 user 和 order 的关联
2. 输出关联关系:

```markdown
- **user.id** ↔ **order.user_id** (1:N)
  - 说明: 一个用户可以有多个订单
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
