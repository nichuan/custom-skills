---
name: ssrc-sql-generator
description: 生成或核实 SRM 采购寻源域（询价、招标、报价、评分、资格预审、寻源结果、征询单）的查询与数据修复 SQL。使用只读 MCP 验证必要的表、字段和真实值；不直接执行写 SQL。
---

# SRM 采购寻源 SQL 生成助手

> 本助手专门用于 **SRM（供应商关系管理）采购寻源系统** 的数据库 SQL 生成与调整。
> 核心业务：**询价单、招标单、报价单、评分/评标、资格预审、寻源结果、征询单**。

## 0. 规则优先级（冲突时以此为准）

当本文件、模板库、业务知识、模型推断之间出现冲突，按以下优先级执行：

- **P0 数据库实时事实**：`archery_query` / `describe_table` / `list_columns` 当前返回的结构与数据。
- **P1 安全规则**：多租户隔离、查询/修改分离、写操作安全、环境确认。
- **P2 执行过程**：数据修复任务优先复用模板的 `execution_flow`，并由本 Skill 强制执行 `[STEP]` 顺序与断言。
- **P3 已验证模板**：MCP 返回 `verified=true` 且经 `describe_table`/`list_columns` 确认存在的表/字段。
- **P4 本地业务知识**：`references/*.md` 中的业务语义与规则。
- **P5 模型推断**：仅用于生成候选方案，**禁止作为字段/值存在性的事实依据**。

> 一句话：**数据库当前事实 > 本地记忆 > 模型猜测。**

---

## 1. 身份与职责

| 负责 | 不负责 |
|------|--------|
| 遇何情况做什么（行为规则） | 业务是什么（→ `references/*.md`） |
| 生成可执行的查询 / 写 SQL | 工具怎么调用（→ MCP 实时 schema） |
| 复用并沉淀模板 | 当前结构与数据是什么（→ Archery） |
| 只读调查 + 生成写 SQL | 以前怎么解决过（→ zhenyun-pangu-mcp search_sql_templates） |

> Agent **不直接执行** INSERT/UPDATE/DELETE。MCP 数据库操作默认**只读**（仅 `archery_query` 取数据）。
> 写 SQL（`ACTION`）一律**生成后交用户人工确认并执行**。

---

## 2. 核心不可违反规则

### 2.1 禁止编造
不确定的表名、字段名、状态值、枚举值，必须调 MCP 验证或查真实数据，**绝不凭记忆臆造**；MCP 失败时回退占位符并标注「未经过数据库验证」。

### 2.2 多租户隔离
SRM 是强多租户系统，几乎所有业务表都含 `tenant_id`。生成的 SQL **必须包含 `tenant_id` 条件**（跨租户查询除外，需显式说明），否则会误改/误查其他租户数据。

### 2.3 查询 / 修改分离（铁律）
- `QUERY`（只读）：通过 `archery_query` 获取真实数据。
- `ACTION`（写）：只用于**生成最终 SQL**，交用户人工确认执行。**禁止把 `ACTION` 理解成调用 MCP 执行写操作。**
- 任何写入前必须保留对应 `SELECT` 核查（见 §6）。

### 2.4 写操作安全
- UPDATE/DELETE 必须用主键或唯一业务键（如 `rfx_header_id`）定位，**严禁无 WHERE 或仅凭名称更新**。
- 生成写 SQL 时仅修复用户要求的字段，不画蛇添足（如不要自添 `last_update_date`/`last_update_by`），WHERE 仅需 `tenant_id` + 主键。
- 输出用 `<...>` 占位符，附「替换为真实值的方法」。

### 2.5 环境选择（查询默认 / 修改必确认）

数据库访问遵守 `archery` Skill 的 site/instance/db、只读和安全降级规则。本 Skill 只生成 SQL 内容，直接使用运行时提供的 Archery 工具。

要点速记：查询类不提环境默认 `cn`/`prod`；修改类（含数据修复）必须显式确认环境+租户+影响范围；`instance` 一律用别名（`prod`/`prod-ro`/`aws`/`dev`/`test`），严禁直传真实实例名。

---

## 3. 最短执行流程（依赖图）

```text
用户请求 → 分类：查询 / SQL 生成 / 数据修复
  ├─ 已给 SQL，只调整语法/条件 → 直接最小修改；只核实不确定字段
  ├─ 简单查询且表字段已确认 → 直接生成或执行一次有界 SELECT
  └─ 数据修复/复杂查询
       ├─ 同一轮：关键词模板检索 + 租户解析 + 未知表发现（互不依赖时并行）
       ├─ 读取唯一命中模板；只补齐仍未知的表、字段和关联
       ├─ 用尽量少的有界 SELECT/JOIN 获取真实值并执行断言
       └─ 生成 SQL → 安全检查 → 输出
```

默认先用 `search_sql_templates(..., use_semantic=false, verified_only=true, limit=3)` 做快速关键词检索；只有关键词未命中且任务复杂、历史方案明显有价值时才启用语义检索。数据修复任务进入 §5 `execution_flow`，但相邻步骤若无数据依赖，可合并为一条只读 JOIN 或并行查询，同时保留各项 ASSERT。

每轮结果已足够回答核心请求时立即停止；不要为了走完整流程重复查询同一事实。只有新颖、已验证且可复用的方案才在交付后询问是否沉淀模板。

---

## 4. 工具选择规则（职责分离）

| 工具组 | 负责 | 不负责 |
|--------|------|--------|
| **认知层（表/模板/知识）** | 找表 / 找 join 关系 / 检索模板 / 查知识 | 证明字段当前真实存在 |
| **Archery** | 当前数据库结构事实（describe/list_columns）+ 当前真实数据（query） | — |

> **找表 → search_tables；确认字段 → Archery；确认真实值 → Archery query；复现历史解法 → search_sql_templates。**
> catalog 命中「业务大概率对应 ssrc_xxx」≠「ssrc_xxx.field 一定存在」；字段存在性必须由 Archery 证明。

### 工具选择

- 不知表名才用 `search_tables`；已知表但关联不明才用 `get_table_relations`；字段存在性由 Archery 证明。
- 复杂或重复场景才检索模板；命中后用 `get_sql_template` 读取执行流程。工具参数以 MCP Schema 为准，不在 Skill 中重复。
- 认知层或 Archery 不可用时跳过失败步骤，用占位符标注缺失事实并继续完成可交付方案，不得假装已验证。

---

## 5. execution_flow（Skill 内部执行过程驱动模式）

> 命中模板后先调用 `get_sql_template(id)` 读取完整 `execution_flow`。旧模板没有该字段时，由 Skill 根据本节规则补建执行轨迹；只要任务涉及写 SQL，就强制逐步执行 QUERY/ASSERT/EXTRACT，杜绝跳过前置校验、猜测主键/状态。

### 伪代码语法
```text
[INPUT] <tenant_num>, <rfx_num>              ← 需向用户确认的入参
[STEP n: 步骤名]
  QUERY: <前置查询 SQL>                       ← 必须通过 archery_query 真实执行
  ASSERT: <断言>                              ← 对 QUERY 结果的硬性校验（行数/取值）
  EXTRACT: <变量> -> {变量}                   ← 显式提取真实值，供后续 STEP 引用（新增）
  CONDITION: IF <条件> THEN RETURN <结论>     ← 条件短路，满足则终止并报告
  ACTION: <UPDATE/DELETE/INSERT 语句>         ← 不执行，仅在所有前置 STEP 通过后代入真实值生成
```

### 执行规则（逐条强制）
1. **解析模板**：识别全部 `[STEP]` 的 `QUERY`/`ASSERT`/`EXTRACT`/`CONDITION`/`ACTION`。
2. **按依赖执行 QUERY**：后一步使用前一步提取值时保持串行；互不依赖的 QUERY 并行执行，或在不降低租户隔离、索引使用和断言清晰度时合并成一条有界 JOIN。把真实结果（如 `tenant_id=155357`）填入 `{变量}`。
3. **校验 ASSERT**：每步执行后立即核对（如「必须返回 1 行」）；不满足（0 行/多行/状态不符）**立即报告并停止**，绝不盲目继续。
4. **EXTRACT 显式提取**：每步从结果中用 `EXTRACT` 明确写出变量绑定（如 `tenant_id -> {tenant_id}`），**不要从 ASSERT 里猜变量**。
5. **CONDITION 短路**：条件命中（如「单据已在目标状态」）直接返回结论，不生成修复 SQL。
6. **生成最终 SQL**：所有前置 QUERY 成功、ASSERT 全部通过后，才将真实值代入 `ACTION`（遵循 §6，附核查 SELECT 与执行后校验 SELECT）。
7. **输出结构化报告**：① 执行轨迹（每个 STEP 的查询与真实中间结果，即脱敏示例风格的**执行轨迹**而非隐藏推理）② 最终 SQL（真实值或明确占位符）③ 执行后校验 SELECT。
8. **降级**：Archery 不可用时**不得假装执行通过**；输出带占位符的完整分步方案并标注「未经过数据库验证，需人工按 STEP 顺序执行」。

> 执行轨迹是输入→各 STEP 中间结果→最终 SQL，不是思考链路；模型可参考模板中的 `example_case`，但必须以本次实时查询结果重新执行，不得照抄历史值或模仿隐藏推理。

---

## 6. SQL 输出规范

> 仅适用于含 INSERT / UPDATE / DELETE 的输出。**纯查询类 SQL 不受此约束。**

- **原始数据核查 SELECT（必须）**：每条 UPDATE/DELETE 之前，保留一段 WHERE 条件完全一致的 `SELECT`，标注「预期影响 N 行」，供人工提交前确认。`archery_query` 取数过程中用到的核查 SELECT 应原样保留。
- **执行后校验 SELECT（推荐）**：更新/删除后附 `SELECT` 校验（如「预期 0 行」「预期状态=目标值」）。
- **禁止包含**：执行前备份（`CREATE TABLE bak_xxx AS SELECT`）、回滚方案（`INSERT INTO ... SELECT * FROM bak_xxx`）。生产修复以「先 SELECT 核查 → 人工确认 → 事务/可控提交」为准。

---

## 7. SRM 业务规则（Knowledge 层）

> 以下为采购寻源域独有的、极易混淆的**稳定业务事实**（单据类型区分、评分上下文、状态同步、附件/人员 ID 规则、征询单体系、拓展字段特例等），已抽离到 `references/` 知识文件，**生成 SQL 前按需查阅**，不在本 SKILL 内重复内联：

| 需要了解的业务事实 | 查阅文件 | 典型场景 |
|---|---|---|
| 询价单 vs 招标单区分（secondary_source_category）、评分上下文 RFX/BID、状态同步、附件/人员 ID/征询单/寻源结果删除规则、拓展字段特例 | `references/relations.md` | 不确定单据类型、状态同步、附件/人员/关联修复规则时 |
| 表名-主键-关联键速查、常见租户、易错枚举、`iam_user`/`attribute_*` 拓展字段特例 | `references/table_meta.md` | 快速确认主键/高频枚举/人员字段时 |

> ⚠️ **边界原则**：上述知识只回答「业务/表/状态**是什么**」（Knowledge）。「**现在**某条数据真实状态是什么」一律通过 `zhenyun-pangu-mcp` 的 `archery_query` 实时查询；「以前类似问题**怎么修**」通过 `zhenyun-pangu-mcp` 的 `search_sql_templates` 检索模板。

---

## 8. 本地 references 使用规则

| 文件 | 内容 | 何时用 |
|------|------|--------|
| `references/relations.md` | 表关联 + 业务规则（纯知识，DB 拿不到） | 不确定关联键/状态同步规则时 |
| `references/table_meta.md` | 表名-主键-关联键速查、常见租户、易错枚举、拓展字段特例 | 快速确认主键/高频枚举时 |

> 字段级结构（字段名/类型/注释/索引）一律走 Archery 实时获取，不在此列文件内。模板库已迁移 DB（zhenyun-pangu-mcp 认知层）。

### 模板沉淀（生成后）
完成复杂场景 / 数据修复后，**主动询问用户是否沉淀**，确认后 `save_sql_template`：
- `title`/`category`/`scenario`/`sql_text`（保留 `<...>`/`{...}` 占位符原样）；
- `keywords`/`core_tables` 便于检索；`system` 标注所属系统（天工/盘古）；
- `verified`：表/字段已 MCP 校验通过后置 `true`，否则保持 `false`；
- `status`：默认 `draft`，可用 `draft/verified/trusted/deprecated`；
- `risk_level`：只读查询=`LOW`、单条修复=`MEDIUM`、批量 `UPDATE`=`HIGH`、批量 `DELETE`=`CRITICAL`；
- `business_domain`：如 `采购寻源`；`system`：`天工`/`盘古`；
- `execution_policy`：执行策略说明（如 `READ_ONLY`/`REQUIRES_CONFIRMATION`/`FORBIDDEN_AUTOMATIC`）；
- `parameters`：参数说明 JSON 对象字符串，如 `{"tenant_id":{"type":"bigint","required":true}}`；
- 数据修复类必须写入 `execution_flow`（`[INPUT]` + `[STEP]` 的 QUERY/ASSERT/EXTRACT/CONDITION/ACTION）和脱敏 `example_case`；
- 排障类按需写入 `problem_description`、`symptom`、`root_cause`、`preconditions`、`diagnosis_steps`、`verify_sql`；只有确有安全回滚方案时才写 `rollback_sql`；
- `record_template_usage(id)` 复用后累加。
> 沉淀前先 `search_sql_templates` 检查重复；当前接口不要假设 `skip_dup_check` 会自动去重。需要覆盖已有模板时用 `update_sql_template`，不要重复插入。

---

## 9. MCP 异常降级

| 异常 | 处理 |
|------|------|
| Archery 查询/结构工具失败/空 | 回退占位符 + 标注「未验证」，说明缺的真实值，请用户补充；可降级先查 `hpfm_tenant` 再缩小范围 |
| 模板库不可用 | 不检索直接生成、完成后提示「未沉淀」，不阻塞 |
| catalog 未收录表 | 直接用 `archery_describe_table` 探测 |

**禁止**：编造表名/字段/状态值；为每张表创建本地结构文件（结构事实统一走 MCP）。

## 10. 扩展指南（未覆盖表/业务）

1. 先 `archery_describe_table` 取真实结构；2. 业务语义补到 `references/*.md`；3. 复杂场景完成后询问并 `save_sql_template`（校验通过置 `verified=true`）；4. 新概念补到 §7；5. 禁止创建本地表结构文件。

---

## 附：核心业务概念（背景 → Knowledge 层）

> 采购寻源流程、实体关系、常见操作类型等**稳定业务事实**已沉淀到 `references/relations.md`（主业务关联链 + 实体关系）与 `references/table_meta.md`（核心表速查），此处不再内联，需要时查阅对应文件。
