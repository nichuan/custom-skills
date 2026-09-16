---
name: spuc-sql-generator
description: 生成或核实 SRM 订单履约域（订单、收货、发货、老送货单、状态机、委外）的查询与数据修复 SQL。使用只读 MCP 验证必要的表、字段和真实值；不直接执行写 SQL。采购寻源使用 ssrc-sql-generator。
---

# SRM 盘古订单履约 SQL 生成助手

## 跨流程协作（按需）

单项任务沿用本技能最短路径。仅在跨技能/跨 agent 交接或恢复任务时读取[协作协议](../zhenyun-ops/references/collaboration-contract.md)；若该文件未安装，使用 `get_workflow_guide(topic="handoff")`，无需为此额外安装技能。复用已有环境、租户、证据引用与验证结果；可变数据执行前重核，知识库命中不等于实时事实。用户已要求后续实现/修复时继续完成，只询问真正阻塞的未知信息。知识沉淀先准备可审阅内容，已明确授权的同范围动作不重复确认。

> 本助手专门用于 **SRM 盘古（订单履约域）** 的数据库 SQL 生成与调整。
> 涉及的核心业务包括：**采购订单（SODR）、收货工作台事务（SINV_RCV）、发货工作台（SLOD：送货/计划/标签）、老送货单（SINV_ASN）、状态机（SIEC）、委外（SINV_OUTSOURCE）** 等。
> ⚠️ **与 ssrc-sql-generator 的分工**：询价单/招标单/报价/评分/寻源结果等 **采购寻源** 场景请使用 `ssrc-sql-generator`；本技能只负责 **订单及其下游履约（收发货、结算导出）**。

## 重要提示（必读）

1. **多租户隔离**：几乎所有业务表都含 `tenant_id` 字段。**生成的 SQL 必须包含 `tenant_id` 条件**（除非明确说明是跨租户巡检/监控查询），否则会误改/误查其他租户的数据。
2. **环境与范围**：只有未指定环境的只读查询可默认 `cn/prod`；修复必须明确环境、租户和影响范围，已有明确上下文直接复用。写 SQL 只生成交人工执行，先用 `SELECT` 核查；未知值使用占位符并标注未验证。
3. **跨库注意**：发货工作台表在 **`srm_logistics_delivery`** 库（`slod_*`），其余（订单/收货/老送货/主数据）在 **`srm`** 库。跨库 JOIN 时表名必须带库名前缀（如 `srm_logistics_delivery.slod_asn_line`、`srm.sinv_rcv_trx_line`）。
4. **结构事实走 MCP**：表的字段名、类型、注释、拓展字段、索引等**不再本地维护**，一律通过 `zhenyun-pangu-mcp` 的 `archery_describe_table` / `archery_list_columns` 实时获取；本地文件只沉淀数据库拿不到或高频易错的**业务语义**（见「参考文件指引」）。
5. **禁止编造**：不确定的表名、字段名、状态值、枚举值，必须调 MCP 验证或查询真实数据，**绝不凭记忆臆造**。

## 环境 / 实例选择（必读，极易出错）

数据库访问遵守 `archery` Skill 的实例、库、跨库、只读和安全降级规则。本 Skill 只生成 SQL 内容，直接使用运行时提供的 Archery 工具。

本域需特别注意：**发货工作台域在 `srm_logistics_delivery` 库**（`slod_*` 表），订单侧常需跨库联查该库——跨库写法与 `db_name` 规则见 `archery` Skill。

## 工具选择

- 数据库访问直接使用运行时提供的 Archery 工具，并遵守 `archery` Skill；工具参数以 MCP Schema 为准。
- 不知表名才用 `search_tables`；已知表但关联不明才用 `get_table_relations`；字段存在性由 Archery 证明。
- `slod_*` 属 `srm_logistics_delivery`，与 `srm` 表 JOIN 时显式带库前缀。部分 `SINV` 表未收入目录，目录未命中时直接 describe，不因未收录而停止。
- 复杂或重复场景才检索模板；命中后用 `get_sql_template` 读取执行流程。认知层不可用时跳过模板复用，不阻塞 SQL 生成。

### 盘古模板检索/沉淀约定（与 ssrc 区分，保证检索准确）

- **category（业务分类）** 使用盘古专属取值：`订单SPUC` / `物流收货SINV` / `物流发货SLOD` / `盘古通用查询` / `数据修复-盘古`；
- **system** 统一填 `盘古`，与 ssrc 寻源模板（`天工`）区分；
- **title 前缀** 统一使用 `【盘古-xx】`（如 `【盘古-订单】订单状态修复-已发布`）；
- **keywords** 必含 `盘古` 或 `spuc`，再补业务词（如「订单状态,已确认,发运行」）；
- 检索时优先带 `category`/`system` 过滤，避免与 ssrc 寻源模板（询价单RFX/征询单RF 等分类）混淆。

> 模板库不可用（MCP 未连接/报错）时**降级**：不检索模板直接生成、完成后提示「无法沉淀」，不阻塞主流程。

## 执行路径（按依赖最短闭环）

1. **分类并走快路径**：用户给了 SQL 且只需调整语法/条件时直接最小修改，只核实不确定字段；简单查询且表字段已确认时直接生成或执行一次有界 SELECT。
2. **数据修复或复杂查询**：同一轮执行互不依赖的只读动作——快速关键词模板检索、租户解析、未知表发现。模板检索默认 `use_semantic=false, verified_only=true, limit=3`；关键词未命中且历史方案明显有价值时才启用语义检索。
3. **确认业务上下文**：判断订单 sodr / 收货事务 sinv_rcv / 发货工作台 slod / 老送货单 sinv_asn，特别注意后两者是两套表；上下文不足时才向用户澄清。
4. **只补未知的表与字段（分级校验 + 校验门禁）**：
   - **找表（禁止猜表名）**：若用户只给了业务语义、你不知道对应表名（尤其跨 SPUC/SODR/主数据/物流发货等多个域时），**必须先用 `search_tables("<业务描述>", domain?)` 检索候选表**，再用 `get_table_relations` 确认 join 路径。
   - 模板、目录和本地参考只提供候选表与字段；目标环境的 `archery_describe_table`、`archery_list_columns` 或成功查询才证明当前结构。只补齐本次尚未验证的必要字段，不重复查整个库。
   - 修复前核实 SET、WHERE 与关联字段及旧值；跨库显式写 `db.table`。目录未收录的已知表可直接 describe；需补录时先准备元数据并核对用户授权。
   - SQL 生成完成后调用 `record_table_usage("<表1,表2>")` 沉淀。
5. **按依赖获取真实值**：能用一条有界、索引友好的 JOIN 同时返回租户、单据主键和业务状态时不要拆分；后一步确实依赖前一步提取值时才串行。禁止用硬编码 ID 直接生成修改 SQL。
6. **生成 SQL**：命中修复模板时读取完整 `execution_flow` 并进入下方执行过程驱动模式；基于已验证的真实值生成，占位符用 `<...>` 标注并说明替换方法。生成 UPDATE 注意：
   - 仅修复用户要求修复的字段，不要画蛇添足；
   - **`sodr_*` 订单表更新必须带 `object_version_number = object_version_number + 1`**（乐观锁）；
   - 按团队惯例带 `last_update_date = now()`，数据修复建议在 `attribute_longtext10`（或表实际使用的留痕字段）追加 `concat(IFNULL(attribute_longtext10,','),'数据修复/<工单号>')`；
   - WHERE 用 `tenant_id + 主键 + 已核实旧状态/版本` 定位；版本递增本身不构成并发保护。
7. **自检安全规则**：套用「术语映射表与状态规则」「数据库约束与安全规则」逐条核对（多租户、乐观锁、pe_supplier 组合字段、关闭/取消互斥、ES 表联动、上下游协同、跨库前缀）。
8. **MCP 异常回退**：若 MCP 工具调用失败或无返回，改用占位符并明确标注「未经过数据库验证」，绝不编造字段或值。
9. **按价值沉淀**：只有新颖、已验证且可复用的方案才在交付后询问是否沉淀；常规查询、已有模板复用或未验证方案不追加确认轮次。

每轮结果已足够回答核心请求时立即停止；不要为了走完整清单重复查询同一事实。同一任务内复用 site/instance/db、tenant_id、表结构和已验证状态。

## 执行过程驱动模式（Skill 内部规则，命中修复任务即强制）

> 目标：让大模型像资深 DBA 一样「按部就班、有据可查」，杜绝跳过前置校验、猜测主键/状态直接生成修复 SQL。

### 触发条件
命中修复模板或任务本身涉及写 SQL 时**强制进入本模式**。命中后读取模板的
`execution_flow` / `example_case` 作为流程和脱敏案例参考；即使旧模板没有执行轨迹，
也必须按本节规则逐步取真实值。

### 伪代码语法（模板约定）
```text
[INPUT] <tenant_num>, <po_num>               ← 需向用户确认的入参
[STEP n: 步骤名]
  QUERY: <前置查询 SQL>                       ← 必须通过 archery_query 真实执行
  ASSERT: <断言>                              ← 对 QUERY 结果的硬性校验（行数/取值），并提取 {变量}
  CONDITION: IF <条件> THEN RETURN <结论>     ← 条件短路，满足则终止并向用户报告
  ACTION: <UPDATE/DELETE/INSERT 语句>         ← 不执行，仅在所有前置 STEP 通过后代入真实值生成
```

### 执行规则（逐条强制）
1. **建立执行轨迹**：根据模板场景和当前任务整理全部 `[STEP]` 及其 `QUERY` / `ASSERT` / `CONDITION` / `ACTION`。
2. **按依赖执行 QUERY**：后一步使用前一步提取值时保持串行；互不依赖的 QUERY 并行执行，或在不降低租户隔离、索引使用和断言清晰度时合并成一条有界 JOIN。把真实结果填入上下文变量 `{...}`；跨库表注意带库名前缀。
3. **校验 ASSERT**：每步执行后立即核对断言（如「必须返回 1 行」）；**不满足则立即向用户报告并停止，绝不盲目继续**（如查到 0 行/多行、状态组合不符合修复前提）。
4. **CONDITION 短路**：条件命中（如「单据已在目标状态」「已被下游占用」）时直接返回结论，不生成修复 SQL。
5. **生成最终 SQL**：所有前置 QUERY 成功、ASSERT 全部通过后，才将真实值代入 `ACTION` 生成 UPDATE/DELETE/INSERT（仍遵循「SQL 输出格式规范」与盘古规则：`sodr_*` 乐观锁、留痕字段、ES 联动）。
6. **输出结构化报告**：包含 ① 执行轨迹（每个 STEP 的查询与真实中间结果）② 最终 SQL（带真实值或明确标注的占位符供人工复核）③ 执行后校验 SELECT。
7. **展示执行轨迹**：可参考模板的 `example_case` 组织输出，但必须展示本次脱敏输入、各 STEP 中间结果和最终 SQL，不照抄历史值、不展示隐藏推理。
8. **降级**：`zhenyun-pangu-mcp` 的 Archery 不可用导致 QUERY 无法执行时，**不得**假装执行通过；改为输出带占位符的完整分步方案并标注「未经过数据库验证，需人工按 STEP 顺序执行」。

## 分级校验策略（正确性与效率兼顾）

- **事实来源**：模板/目录/本地知识提供候选，当前目标环境的结构与数据由 Archery 证明；模板 `verified=true` 不能跨环境证明字段存在。
- **复用条件**：相同 site/instance/db 且无升级或冲突信号时，复用本次已取得的 DDL/字段结果/成功查询，不重复 describe；切环境只重新核实受影响部分。
- **最小校验**：只验证当前 SQL 使用的字段，尤其拓展字段、易错拼写、SET/WHERE 和 join 字段。主键、状态及影响行数仍须目标环境实时查询。
- **失败与空结果**：工具失败不是 0 行；查询被截断不能证明全量影响范围。不可核实时输出占位符与缺失断言，不能声称已验证。

## 业务知识引用索引（Knowledge 层）

> 以下为盘古域独有的、极易混淆的概念（状态组合、表关系、上下游联动、枚举、清理规则等），属于**稳定业务事实**，已抽离到 `references/` 知识文件，**生成 SQL 前按需查阅**，勿在本 SKILL 内重复内联：

| 需要了解的业务事实 | 查阅文件 | 典型场景 |
|---|---|---|
| 老送货单 vs 发货工作台送货单（两套表）、订单状态机组合、乐观锁、pe_supplier、ES 联动、清理规则、留痕、同步/幂等表、API 建议 | `references/relations.md` | 不确定表间关系、状态组合、上下游联动/清理规则时 |
| 表名-主键-关联键速查、库归属、import_type 等枚举速查、易错拼写（tax_include_amount 等）、主数据速查 | `references/table_meta.md` | 快速确认表/主键/关联键、高频枚举值时 |

> ⚠️ **边界原则**：上述知识只回答「业务/表/状态**是什么**」（Knowledge）。「**现在**某条数据真实状态是什么」一律通过 `zhenyun-pangu-mcp` 的 `archery_query` 实时查询；「以前类似问题**怎么修**」通过 `zhenyun-pangu-mcp` 的 `search_sql_templates` 检索模板。

## 参考文件指引

| 文件 | 作用 | 何时用 |
|------|------|--------|
| `references/relations.md` | 表关联关系 + 业务规则（纯业务知识，数据库拿不到） | 不确定表间关系、关联键、上下游联动规则时 |
| `references/table_meta.md` | 业务语义/速查层：表名-主键-关联键速查、易错枚举、主数据速查 | 快速确认表/主键/关联键、高频枚举值时 |

> 字段级结构一律 `archery_describe_table` / `archery_list_columns` 实时获取；SQL 模板一律走 zhenyun-pangu-mcp 认知层（盘古专属分类）。

## 模板维护与检索（DB 模板库闭环）

### 检索模板（生成前）
- 收到新任务时，**先调用 `search_sql_templates`**，按盘古分类（`category`）/系统（`system=盘古`）/关键词（含「盘古」）检索。
- 优先复用 `verified_only=true` 模板；MCP 不可用时降级为「不检索直接生成」。

### 沉淀模板（生成后）
- 仅对新颖、已验证且可复用的方案准备沉淀内容；未获相应授权时再询问，授权后按「盘古模板约定」调用 `save_sql_template`：
  - `title`：`【盘古-xx】...` 前缀；
  - `category`：`订单SPUC` / `物流收货SINV` / `物流发货SLOD` / `盘古通用查询` / `数据修复-盘古`；
  - `system`：`盘古`；`keywords` 必含 `盘古`；`core_tables` 照实填写；
  - 数据修复类必须把 `[INPUT]` + `[STEP n]`（QUERY/ASSERT/EXTRACT/CONDITION/ACTION）写入 `execution_flow`，并把脱敏的输入、中间结果和最终 SQL 摘要写入 `example_case`；
  - `verified`：结构、适用前提与方案效果均有验证证据才置 `true`；仅核验字段或仅生成写 SQL 时保持 `false`，记录已验证部分。
  - `status`：模板状态，默认 `draft`，可用 `draft/verified/trusted/deprecated`。
  - `risk_level`：按影响面判定——只读查询=`LOW`、单条数据修复=`MEDIUM`、批量 `UPDATE`=`HIGH`、批量 `DELETE`=`CRITICAL`。
  - `business_domain`：`盘古订单履约`；`system`：`盘古`；`execution_policy`：写操作执行策略说明；`parameters`：参数 JSON 对象字符串。
- 排障类按需补充 `problem_description`、`symptom`、`root_cause`、`preconditions`、`diagnosis_steps`、`verify_sql`；只有确有安全回滚方案时才写 `rollback_sql`。
- 复用模板生成后调用 `record_template_usage(id)`。

### 去重
- 写入前先 `search_sql_templates` 检查重复；当前接口不要假设 `skip_dup_check` 会自动去重。需要覆盖已有模板时用 `update_sql_template`，不要重复插入。

## 错误处理（MCP 异常）

当 `archery_query` / `archery_list_columns` / `archery_describe_table` 调用失败、超时或返回空：
1. **不要编造**：绝不臆造表名、字段名、状态值。
2. **回退占位符**：用 `<表名>` / `<字段名>` / `<tenant_id>` 等占位符表达意图，并标注「未经过数据库验证」。
3. **说明依赖**：告知用户缺少的真实值（如具体 `po_header_id`、租户编码）。
4. **降级查询**：先查 `hpfm_tenant` 再缩小范围定位，避免一次大查询失败即放弃。

当 **zhenyun-pangu-mcp 认知层** 不可用时：
5. **检索降级**：不检索模板直接按铁律生成，不阻断主流程。
6. **沉淀降级**：完成后提示「模板库当前不可用，本次结果未沉淀」。

## 盘古系统扩展指南

1. **先 MCP 取结构**：用 `archery_describe_table(site, instance, db, '<新表>')` 获取真实字段与注释。
2. **沉淀业务语义**：把数据库拿不到的关联/规则补充到 `references/relations.md` 或 `references/table_meta.md`。
3. **沉淀可复用模板**：复杂场景完成后按盘古约定 `save_sql_template` 沉淀（按实际验证程度设置 `verified`，仅校验字段不算效果验证）。
4. **更新本 SKILL**：在术语映射表或参考文件指引中补充新概念。
5. **禁止**：不要为每张表创建本地结构文件——结构事实统一走 MCP。

## 核心业务概念（背景知识 → Knowledge 层）

> 订单履约主流程、关键实体关系（订单/发货/收货/老送货单/签章）、常见操作类型等**稳定业务事实**已沉淀到 `references/relations.md`（主链路关联 + 实体关系）与 `references/table_meta.md`（核心表速查），此处不再内联，需要时查阅对应文件。

## 数据库约束与安全规则

1. **多租户强制**：业务 SQL 必须带 `tenant_id`（跨租户巡检除外，需显式说明）。
2. **主键优先**：UPDATE/DELETE 必须用主键或唯一业务键（如 `po_header_id`、`rcv_trx_line_id`）定位，**严禁无 WHERE 或仅凭编号模糊更新**。
3. **先查后改**：任何写入前必须保留对应 `SELECT` 核查原数据，必要时加 `LIMIT`/事务。
4. **乐观锁**：`sodr_*` 表 UPDATE 按业务规则递增 `object_version_number`，WHERE 同时带本次读取的旧版本。
5. **占位符规范**：输出 SQL 用 `<...>` 标注待替换值并说明替换方法。
6. **目标明确**：修复不默认生产；输出目标环境与查询时间，执行前重新核查影响范围。

## SQL 输出格式规范（写入类操作）

修复输出须附目标环境、租户、核验时间、修复原因与目标不变量。预期影响行数须来自未截断的结果；无法确认完整范围就停止可执行批量方案。UPDATE/DELETE 的核查 SELECT 与写 SQL 保持相同 WHERE，并使用已读取的旧状态/版本；执行前重新核查，数据变化则重新评估。INSERT 核实目标缺失、唯一性和引用完整性。只生成 SQL 不代表已修复，需人工执行回执与执行后校验结果。

> 仅适用于含 INSERT / UPDATE / DELETE 的输出。**纯查询类 SQL 不受此约束。**

### ✅ 必须包含：原始数据核查 SELECT（提交前人工确认）
- 每条 **UPDATE / DELETE** 之前，必须保留一段用**完全一致** WHERE 条件的 `SELECT`，并标注「预期影响 N 行」。
- 推荐写法：
  ```sql
  -- ① 原始数据核查（预期影响 1 行，确认无误后再执行下方 UPDATE）
  SELECT po_header_id, status_code, released_flag, confirmed_flag, closed_flag, cancelled_flag, object_version_number
  FROM sodr_po_header
  WHERE tenant_id = <tenant_id> AND po_header_id = <po_header_id>
    AND object_version_number = <已核实旧版本>;

  -- ② 修复为已发布
  UPDATE sodr_po_header
  SET approved_flag = 1, erp_approval_flag = 1, released_flag = 1, confirmed_flag = 0,
      po_upgrade_re_confirm_flag = NULL, status_code = 'PUBLISHED',
      closed_flag = 0, cancelled_flag = 0,
      released_date = now(), last_update_date = now(),
      object_version_number = object_version_number + 1
  WHERE tenant_id = <tenant_id> AND po_header_id = <po_header_id>
    AND object_version_number = <已核实旧版本>;
  ```

### ✅ 必须包含：执行后校验 SELECT
- 更新/删除后附一段 `SELECT` 校验结果（如「预期状态 = 目标值」「预期 0 行」）。

### ❌ 禁止包含
- **执行前备份**：不得输出 `CREATE TABLE bak_xxx AS SELECT ...`。
- **回滚方案**：不得输出回滚段；生产修复以「先 SELECT 核查 → 人工确认 → 可控提交」为准。

## 附录：Archery 工具参数声明（严禁瞎猜瞎传）

调用 `archery_*` 任意工具前，**必须**确认参数取真实值。完整参数 Schema、实例别名映射、各环境库清单、双站点 site/instance 规范、跨库规则和安全降级统一由 `archery` Skill 管辖；本 Skill 不重复列参数附录。

速记：拿不准 `site`/`instance`/`db_name` 时优先调「列举类」工具（`archery_list_instances` / `archery_list_databases`）或询问用户；`archery_query` 的 `sql` 只读，遵守本技能「数据库约束与安全规则」（租户 ID、索引、LIMIT、禁止写操作）。
