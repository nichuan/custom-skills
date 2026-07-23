---
name: sql-generator
description: 基于SRM采购寻源系统的SQL生成助手，支持快速生成业务查询SQL、调整现有SQL、查询表结构及关联关系。通过 sql-ops MCP 对接真实数据库：不确定的表名/字段名必须先校验，逐步执行只读查询获取真实值（先租户、再单据、再业务）后生成可执行SQL，MCP 异常时回退占位符，严禁编造。采用渐进式披露设计，按需加载表详细结构。专门针对租户的询价单（招标单）、报价单、评分、资格预审等核心业务场景。
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
- 处理招标单（BID）相关的查询与数据修复，招标单与询价单共用相同的表（`ssrc_rfx_*`）

### 典型触发语句
- "租户SRM-AUX查询询价单"
- "参考已有SQL模板,修复报价单数据"
- "列出询价单表和报价单表的关联关系"
- "生成SRM-AUX租户的单据RFX2026022600014的评分专家查询SQL"
- "查询资格预审表的字段结构"
- "修复征询单RF2026010100001的报价时间，恢复为报价中状态"
- "查询招标单BID2026070100001的投标情况"
- "将招标单BID2026070100001修复为待定标状态"

## 工具能力 (sql-ops MCP)

本技能通过 `sql-ops` MCP 服务对接真实数据库（Archery 平台），**所有表/字段验证与只读查询都必须走该服务，严禁凭空臆造表名或字段名**。包含三个工具：

- **`validate_table_columns(tb_name, columns?, instance_name?, db_name?, schema_name?)`**
  校验表与字段是否存在。不传 `columns` → 仅校验表是否存在并返回全部字段；传 `columns`（字段名列表）→ 返回每个字段的命中/缺失及类型定义。用于生成 SQL 前确认表名、字段名拼写是否正确。
- **`describe_table(tb_name, instance_name?, db_name?, schema_name?)`**
  获取表完整结构（DDL + 字段列表），用于确认字段拼写、类型与注释。
- **`execute_sql(sql, instance_name?, db_name?, limit_num=100, schema_name?, tb_name?)`**
  在 Archery 执行**只读查询**（SELECT/SHOW/EXPLAIN/WITH/DESC 等），返回真实数据（Markdown 表格 + 行数/耗时/脱敏标记）。

默认实例/库：实例 `SAAS-SRM-PROD数据库`、库 `srm`，`instance_name`/`db_name` 一般不传即用默认值。

## 执行步骤

> **核心原则（铁律）**
> 1. **不确定就验证**：任何你将在 SQL 中用到的、不确定的表名或字段名，生成前必须先用 `validate_table_columns` / `describe_table` 校验；`references/table_detail/*.md` 仅供参考，**真实字段以 `sql-ops` 返回为准，禁止靠记忆编造**。
> 2. **逐步生成、逐步验证**：按依赖顺序分步（如先解析租户 → 再解析单据主键 → 再执行业务查询），每一步都先调用 `execute_sql` 拿到真实结果，再推进下一步；不要一次性臆测所有参数。
> 3. **异常即占位**：若某一步 MCP 返回异常或查询无结果，该步应填入的具体值改用占位符（`{tenant_id}` / `{rfx_header_id}` 等），并在注释标注异常原因，**绝不编造**。

0. **工具与约定**：确认使用 `sql-ops` 的 `execute_sql` / `validate_table_columns` / `describe_table`；默认实例 `SAAS-SRM-PROD数据库`、库 `srm`。

1. **识别单据类型**：单号 `BID`→招标单，`RFX`→询价单，`RFI`/`RFP`→征询单；招标单与询价单共用 `ssrc_rfx_*` 表，区分字段 `ssrc_rfx_header.secondary_source_category = 'NEW_BID'`；评标/结果表 `source_from` 统一 `'RFX'`。

2. **校验表与字段（强制）**：
   - 列出你将在 SELECT/WHERE/JOIN 中用到的所有表与字段，对**不确定是否存在**的逐一校验：
     - 校验整表：`validate_table_columns(tb_name="ssrc_rfx_header")`
     - 校验字段：`validate_table_columns(tb_name="ssrc_rfx_header", columns=["rfx_num","rfx_status","secondary_source_category"])`
   - 需要完整结构确认拼写/类型时：`describe_table(tb_name="ssrc_rfx_header")`。
   - ✅ 校验通过的表/字段才允许写进最终 SQL；🚫 未校验且不敢确定的，**必须校验，不得臆造**。

3. **逐步查询（一步步推进，每步带入真实值）**：
   - **步骤 A 解析租户**：若只有租户编码、无 `tenant_id`，先调用：
     `execute_sql(sql="SELECT tenant_id, tenant_num FROM hpfm_tenant WHERE tenant_num = 'SRM-AUX';")`
     取得真实 `tenant_id` 后，后续 SQL 一律用真实值，不再写 `{tenant_id}`。
   - **步骤 B 解析单据主键**：若只有业务单号，用步骤 A 的真实 `tenant_id` 查主键：
     `execute_sql(sql="SELECT rfx_header_id, rfx_status FROM ssrc_rfx_header WHERE tenant_id = <真实id> AND rfx_num = 'RFX20260...';")`
   - **步骤 C 业务查询/统计**：基于 A、B 已取得真实值构造并执行真正的业务 SQL（只读查询在此步用 `execute_sql` 验证）。
   - 每一步都依据上一步返回的真实值生成下一步 SQL，**禁止并行臆测全部参数**。

4. **汇总生成最终可执行 SQL**：将各步真实结果代入，产出带注释头的完整 SQL（业务场景/涉及表/关联/核心字段/source_from/字段命名）。只读查询已在步骤 3 用真实数据验证，可交付并附结论。

5. **MCP 异常回退（占位符模式）**：若某步 `execute_sql` / `validate_table_columns` / `describe_table` 返回异常或查询无结果：
   - 该步本应填入的具体值**改用占位符** `{tenant_id}` / `{rfx_header_id}` / `{字段名}`；
   - 在 SQL 注释/回复明确标注：`⚠️ 以下占位符因 sql-ops 校验/查询异常未能获取真实值，请人工确认后替换：xxx`；
   - 写操作（UPDATE/DELETE/INSERT）**禁止**用 `execute_sql` 执行，保持占位符交人工处理。

## 核心规则

### SQL生成规则
- 必须先确认表关联键的正确性(参考 `relations.md`)
- 使用明确的表别名避免字段歧义
- 生成的SQL必须包含关键注释说明
- 如果用户已经告知了租户id，则直接SQL中使用租户id，无需再输出查询租户id的SQL
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
    - 文本类型：`attribute_varchar1` ~ `attribute_varchar10`
    - 长文本类型：`attribute_longtext1` ~ `attribute_longtext10`
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
- **查询SQL规范（必须严格遵守）**:
  - 生成查询SQL时，**默认添加 `tenant_id` 条件**（如果表中有该字段）
  - 租户过滤是SRM系统的基本要求，几乎所有SRM表都包含 `tenant_id` 字段
  - 示例：
    ```sql
    -- ✅ 正确：默认包含 tenant_id 过滤
    SELECT rfx_header_id, rfx_num, rfx_status
    FROM ssrc_rfx_header
    WHERE tenant_id = {tenant_id}
      AND rfx_num = 'RFX2026032600012';

    -- ❌ 错误：缺少 tenant_id 过滤
    SELECT rfx_header_id, rfx_num, rfx_status
    FROM ssrc_rfx_header
    WHERE rfx_num = 'RFX2026032600012';
    ```
- **附件删除规则（必须严格遵守）**:
  - 在SRM系统中，**将附件对应的UUID字段更新为NULL，即为删除/清除该附件**
  - 适用于所有 `*_attachment_uuid` 字段，包括但不限于：
    - `business_attachment_uuid`（商务附件UUID）
    - `tech_attachment_uuid`（技术附件UUID）
    - `current_business_attachment_uuid`（当前商务附件UUID）
    - `current_tech_attachment_uuid`（当前技术附件UUID）
    - `round_business_attachment_uuid`（多轮商务附件UUID）
    - `bargain_business_attachment_uuid`（议价商务附件UUID）
  - 清除附件时，必须同时清除对应的 `current_*` 字段，确保彻底删除
  - 示例：
    ```sql
    -- ✅ 正确：将UUID字段置NULL即删除附件
    UPDATE ssrc_rfx_quotation_header
    SET    business_attachment_uuid = NULL,
           current_business_attachment_uuid = NULL
    WHERE  tenant_id = {tenant_id}
      AND  quotation_header_id = {quotation_header_id};
    ```
- **人员ID修复规则（必须严格遵守）**:
  - 所有SRM业务表中存储的人员ID（`user_id`、`expert_user_id`、`created_by`、`last_updated_by`、`process_user_id`、`deliver_from_user_id`、`deliver_to_user_id`、`pur_user_id`、`prequal_user_id`、`request_user_id`、`contact_user_id`、`recipient_user_id` 等）**最终都指向 `iam_user.id`**
  - `iam_user.organization_id` 即为租户ID，**等价其他表的 `tenant_id`**；但 `iam_user` 表本身**没有 `tenant_id` 字段**，过滤租户必须用 `organization_id = {tenant_id}`
  - 任何"涉及修复数据中人员"的需求，都必须先查 `iam_user` 把账号/姓名解析为 `id`，再用该 `id` 更新业务表的人员字段，不要直接写入账号字符串
  - 详细结构见 `references/table_detail/iam_user.md`，关联关系见 `relations.md` 的"1.2 用户（人员）关联"
- **UPDATE/DELETE 安全规则（必须严格遵守）**:
  - UPDATE 和 DELETE 必须是单表操作，必须包含 WHERE 条件
  - **WHERE 条件必须使用 `tenant_id` + 表主键**，禁止使用任何非主键字段（包括外键、业务单号等）
  - **表主键识别规则**：
    - 主键是表的唯一标识字段，可通过 `references/table_detail/[表名].md` 查询
    - 常见表的主键：
      - `ssrc_rfx_header`: `rfx_header_id`（询价单和招标单共用此表）
      - `ssrc_rfx_header_expand`: `rfx_header_expand_id`（注意：不是 `rfx_header_id`）
      - `ssrc_rf_header`: `rf_header_id`
      - `ssrc_rfx_quotation_header`: `quotation_header_id`（询价单和招标单共用此表）
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
- **询价单/招标单状态同步规则（必须严格遵守）**:
  - `ssrc_rfx_header.rfx_status` 与 `ssrc_rfx_header_expand.rfx_real_status` 必须保持同步
  - 修改询价单或招标单状态时（两者共用同一套表），必须同时更新两张表，缺一不可：
    ```sql
    -- 同步更新主表状态（使用主键）
    UPDATE ssrc_rfx_header SET rfx_status = '{new_status}' WHERE tenant_id = ? AND rfx_header_id = ?;
    -- 同步更新扩展表状态（必须查询并使用主键）
    -- 步骤2.1: 先查询拓展表主键
    SELECT rfx_header_expand_id FROM ssrc_rfx_header_expand WHERE tenant_id = ? AND rfx_header_id = ?;
    -- 步骤2.2: 用拓展表主键更新
    UPDATE ssrc_rfx_header_expand SET rfx_real_status = '{new_status}' WHERE tenant_id = ? AND rfx_header_expand_id = ?;

    -- 注意，如果是要查询或者修复询价单或者新招标单据的状态，建议直接使用连接查询一次性查出ssrc_rfx_header，ssrc_rfx_header_expand的字段，避免多执行一次SQL，如下SQL
     select srh.rfx_header_id,
            srh.tenant_id,
            srh.rfx_title,
            srh.rfx_status,
            srh.template_id,
            srhe.rfx_header_expand_id,
            srhe.rfx_real_status
      from ssrc_rfx_header srh
      join ssrc_rfx_header_expand srhe on srh.rfx_header_id = srhe.rfx_header_id
      where srh.tenant_id = ? and srh.rfx_num = ?;
    ```
- **招标单(BID)与询价单(RFX)共用表体系规则（必须严格遵守）**:
  - SRM系统中，招标单/新招标单（单号以 `BID` 开头）与询价单（单号以 `RFX` 开头）**共用同一套数据库表**（`ssrc_rfx_*` 系列表），只是**术语叫法不同**（如"定标"对应"核价"、"评标"对应"评分"、"投标"对应"报价"等）
  - **区分询价单与新招标的字段是 `ssrc_rfx_header.secondary_source_category`**：
    - `'NEW_BID'` = 新招标单
    - 常规询价单 = 该字段的非 `NEW_BID` 取值
    - （如存在竞价等其它类型，可见 `RFA` 等取值）
  - ⚠️ **关键澄清（极易混淆，必须严格遵守）**：
    - `ssrc_rfx_header.source_from` 是**单据来源**（如手工新建、申请转单、立项转单等），**不是**用于区分询价单/招标单的字段，切勿用它来区分单据类型
    - 评标相关表（`ssrc_evaluate_*`）、寻源结果表（`ssrc_source_result`）中的 `source_from` **才是**上下文区分字段，但需注意：
      - `'RFX'` = 询价单上下文，且**新招标单在评标/结果表中的 `source_from` 同样为 `'RFX'`**（新招标与询价单共用同一上下文）
      - `'BID'` = **老招标**上下文（老招标几乎已不再使用，无特殊说明时一律按 `'RFX'` 处理）
      - `'RFI'` / `'RFP'` = 征询单上下文
  - **术语映射速查表**：

  | 招标单(BID)术语 | 询价单(RFX)术语 | 状态值（同址复用） |
  |:---|---:|:---|
  | 招标单 | 询价单 | — |
  | 投标 | 报价 | — |
  | 评标 | 评分 | — |
  | 待定标 | 待核价 | `CHECK_PENDING` |
  | 定标审批中 | 核价审批中 | `CHECK_APPROVING` |
  | 定标审批拒绝 | 核价审批拒绝 | `CHECK_REJECTED` |
  | 定标中 | 核价中 | `CHECKING` |
  | 投标中 | 报价中 | `IN_QUOTATION` |
  | 投标响应不足 | 报价响应不足 | `LACK_QUOTED` |
  | 评标中 | 评分中 | `SCORING` |
  | 已完成 | 已完成 | `FINISHED` |
  | 已开标 | 已开标 | `OPENED` |
  | 待开标 | 待开标 | `OPEN_BID_PENDING` |
  | 已取消 | 已取消 | `CANCELED` |
  | 已关闭 | 已关闭 | `CLOSED` |
  | 新建 | 新建 | `NEW` |
  | 未开始 | 未开始 | `NOT_START` |
  | 暂停 | 暂停 | `PAUSED` |
  | 待初审 | 待初审 | `PRETRIAL_PENDING` |
  | 资格预审中 | 资格预审中 | `IN_PREQUAL` |
  | 资格后审中 | 资格后审中 | `IN_POSTQUAL` |
  | 资格后审截止 | 资格后审截止 | `POSTQUAL_CUTOFF` |
  | 待预审审批 | 待预审审批 | `PENDING_PREQUAL` |
  | 待定候选人 | 待定候选人 | `PRE_EVALUATION_PENDING` |
  | 候选人审批中 | 候选人审批中 | `PRE_EVALUATION_APPROVING` |
  | 候选人审批拒绝 | 候选人审批拒绝 | `PRE_EVALUATION_PENDING_REJECT` |
  | 待评分汇总 | 待评分汇总 | `RFX_EVALUATION_PENDING` |
  | 发布审批中 | 发布审批中 | `RELEASE_APPROVING` |
  | 发布审批拒绝 | 发布审批拒绝 | `RELEASE_REJECTED` |
  | 再次招标 | 再次询价 | `ROUNDED` |
  | 多轮投标 | 多轮报价 | `ROUND_QUOTATION` |
  | 未寻源 | 未寻源 | `UN_SOURCE` |

  - 查询新招标单时：单号用 `BID` 前缀匹配；如需在 `ssrc_rfx_header` 上区分，使用 `secondary_source_category = 'NEW_BID'`；**关联评标/结果表时 `source_from` 仍使用 `'RFX'`（`'BID'` 仅指几乎不用的老招标，不要误用）**；其他表关联、字段、状态值均与询价单一致，仅术语翻译不同
  - 生成招标单SQL时，注释中可以使用招标术语（如"待定标""评标"等），但SQL中的状态值、关联字段值与询价单完全一致
  - 示例：
    ```sql
    -- 查询新招标单BID2026070100001的评标汇总（与询价单完全共用：ssrc_rfx_header用secondary_source_category区分，评标表source_from仍为'RFX'）
    SELECT ses.evaluate_summary_id,
           qh.supplier_company_name  AS 投标供应商,
           ses.score                 AS 评标得分,
           ses.score_rank            AS 排名,
           ses.invalid_flag          AS 无效投标
    FROM   ssrc_evaluate_summary ses
           INNER JOIN ssrc_rfx_quotation_header qh ON ses.quotation_header_id = qh.quotation_header_id
    WHERE  ses.tenant_id = {tenant_id}
      AND  ses.source_header_id = {rfx_header_id}
      AND  ses.source_from = 'RFX'   -- 新招标与询价单共用'RFX'；'BID'仅指几乎不用的老招标
    ORDER BY ses.score_rank ASC;
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
- **寻源结果删除规则（必须严格遵守）**:
  - 删除/清除寻源结果时，必须区分以下两种场景：
    1. **普通删除寻源结果**：仅操作 `ssrc_source_result` 表，使用模板 2.6.5（删除寻源结果）
    2. **释放被订单错误占用的寻源结果**：需同时操作 `ssrc_source_result` 和 `ssrc_source_result_change_history` 表，使用模板 2.6.6（释放被订单错误占用的寻源结果）
  - `ssrc_source_result_change_history`（寻源结果变更历史表）**仅在寻源结果被订单错误占用时**才需要删除，普通删除寻源结果场景下不需要操作此表
  - 错误示例：
    ```sql
    -- ❌ 错误：普通删除寻源结果时不应操作 change_history 表
    DELETE FROM ssrc_source_result_change_history WHERE source_result_id = ?;
    DELETE FROM ssrc_source_result WHERE result_id = ?;
    ```
  - 正确示例（普通删除）：
    ```sql
    -- ✅ 正确：仅删除 ssrc_source_result
    DELETE FROM ssrc_source_result WHERE result_id = ? AND tenant_id = ?;
    ```
- **询价单/招标单回退至"报价中"/"投标中"(IN_QUOTATION)延时消息规则（必须严格遵守）**:
  - 当询价单状态回退至"报价中"(IN_QUOTATION)时（如核价回退、评分回退、修复报价截止时间等），除了修复状态外，**必须额外插入一条 `spfm_pending_message` 延时消息**
  - 延时消息的作用：确保在新的报价截止时间到达后，系统能自动刷新询价单状态
  - 需要执行3条SQL：
    1. `UPDATE ssrc_rfx_header` — 修复状态 + 报价截止时间（rfx_status='IN_QUOTATION', quotation_end_date, latest_quotation_end_date）
    2. `UPDATE ssrc_rfx_header_expand` — 同步状态（rfx_real_status='IN_QUOTATION'）
    3. `INSERT INTO spfm_pending_message` — 插入延时消息
  - `spfm_pending_message` 插入规则：
    - `tenant_id` = 当前租户ID
    - `biz_id` = rfx_header_id
    - `biz_type` = 'RFX'
    - `server_name` = 'srm-source'
    - `execute_type` = 'QUOTATION_END_REFRESH_RFX_STATUS'
    - `execute_time` = 新的报价截止时间（即 quotation_end_date 的值）
    - `executed_flag` = '0'
    - `expand_param` = null
    - `object_version_number` = '1'
    - `created_by` 和 `last_updated_by` = 操作人user_id(数据修复场景没有特殊说明可以直接默认0)
    - `adaptor_code` = null
  - 完整示例：
    ```sql
    -- ✅ 询价单回退至报价中，必须插入延时消息
    UPDATE ssrc_rfx_header
    SET    rfx_status = 'IN_QUOTATION',
           quotation_end_date = '{new_end_date}',
           latest_quotation_end_date = '{new_end_date}'
    WHERE  rfx_header_id = {rfx_header_id}
      AND  tenant_id = {tenant_id};
    UPDATE ssrc_rfx_header_expand
    SET    rfx_real_status = 'IN_QUOTATION'
    WHERE  rfx_header_expand_id = {rfx_header_expand_id}
      AND  tenant_id = {tenant_id};
    INSERT INTO spfm_pending_message (tenant_id, biz_id, biz_type, server_name, execute_type, execute_time,
                                      executed_flag, expand_param, object_version_number, creation_date,
                                      created_by, last_updated_by, last_update_date, adaptor_code)
    VALUES ({tenant_id}, {rfx_header_id}, 'RFX', 'srm-source', 'QUOTATION_END_REFRESH_RFX_STATUS', '{new_end_date}', '0',
            null, '1', now(), 0, 0, now(), null);
    ```

### 上下文加载规则
- 严格按需加载,只读取 `table_detail/[表名].md` 中涉及的表
- 不加载全量表结构,保持上下文精简
- 如果某个表的详细结构不存在,仅使用 `table_meta.md` 中的核心字段
- ⚠️ 招标单(BID开头)与询价单共用 `ssrc_rfx_*` 系列表，加载表结构时无需区分

### 准确性保障
- **验证优先级（务必遵守）**：`sql-ops` MCP 返回的真实结构 **> 本地参考文件**。`table_meta.md` / `table_detail/*.md` / `relations.md` 只作为快速索引与业务语义参考；**只要对表名或字段名有任何不确定，就必须用 `validate_table_columns` / `describe_table` 向真实库确认，严禁凭记忆或猜测编造表/字段**。
- 生成SQL前必须验证:
  - 表名是否真实存在(先查 `table_meta.md` 索引，**不确定则用 `validate_table_columns` / `describe_table` 确认**)
  - 关联键是否匹配(参考 `relations.md`，涉及的关联字段不确定时用 `validate_table_columns` 校验两侧字段存在)
  - 字段是否存在于对应表(参考 `table_detail/[表名].md`，**不确定则用 `validate_table_columns(tb_name, columns=[...])` 逐字段校验，以返回结果为准**)
  - **字段命名是否符合下划线格式**（snake_case）
  - **拓展字段（attribute前缀）是否按规则命名**
  - ⚠️ **source_from 是否正确**：评标/结果表中 `'RFX'` 同时覆盖询价单与新招标（新招标不再使用 `'BID'`），`'BID'` 仅指几乎不再使用的老招标；征询单用 `'RFI'`/`'RFP'`。另需注意 `ssrc_rfx_header.source_from` 是**单据来源**，不是单据类型区分字段（区分用 `secondary_source_category`）
- **逐步验证**：复杂查询必须分步生成并逐步用 `execute_sql` 验证（先租户、再单据主键、再业务查询），每步以上一步真实结果为输入。
- **异常回退**：任一验证/查询步骤 MCP 异常或无结果时，对应值改用占位符并显式标注，绝不编造真实值。

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
    - **询价单（RFX）SQL模板**: 询价单和新招标单相关的查询、统计和数据修复（两者共用同一套模板与 `source_from='RFX'` 上下文，仅 `ssrc_rfx_header.secondary_source_category` 不同）
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
-- 单据类型: [询价单(RFX/常规) / 新招标单(BID, secondary_source_category='NEW_BID') / 征询单(RF)]
-- 涉及表: [表1, 表2, ...]
-- 关联关系: [表1.key = 表2.key, ...]
-- 核心字段: [主要查询和统计字段]
-- source_from: [评标/结果表上下文: RFX(询价单+新招标) / BID(老招标,极少用) / RFI / RFP]
-- 字段命名: 使用下划线格式（snake_case）
-- 拓展字段: attribute_decimal1~10, attribute_datetime1~10等

SELECT ...
FROM ...
WHERE ...
GROUP BY ...
```

## SRM常见业务场景

### 场景1: 询价单/招标单查询与分析
- **业务需求**: 查询租户SRM-AUX的询价单/招标单数据（BID开头→招标单，询价单模板同样适用）
- **涉及表**: `ssrc_rfx_header`, `ssrc_rfx_header_expand`, `hpfm_tenant`
- **关键字段**: `rfx_num`(单号), `rfx_status`(状态), `rfx_title`(标题), `quotation_start_date`(报价开始时间)
- **处理流程**:
  1. 从 `sql_templates.md` 匹配时间过滤模板
  2. 结合 `table_detail/ssrc_rfx_header.md` 确认时间字段
  3. 标注租户过滤和时间范围
  4. ⚠️ 如查询招标单：用 `BID...` 前缀匹配单号，SQL模板完全相同

### 场景2: 报价单/投标单与询价单/招标单关联查询
- **业务需求**: 查询询价单/招标单对应的报价/投标情况（BID开头→招标投标场景，同模板）
- **涉及表**: `ssrc_rfx_header`, `ssrc_rfx_quotation_header`, `ssrc_rfx_line_supplier`
- **关联关系**: `ssrc_rfx_header.rfx_header_id` ↔ `ssrc_rfx_quotation_header.rfx_header_id`
- **处理流程**:
  1. 从 `relations.md` 确认询价单-报价单关联关系
  2. 为每个SRM表设置业务相关的别名
  3. 在注释中列出所有业务关联键
  4. 确保所有字段使用下划线格式（如 `quotation_line_id`）
  5. 如果使用拓展字段，按 `attribute_decimal1~10` 等规则命名

### 场景3: 评分/评标统计分析
- **业务需求**: 统计专家评分/评标情况（询价单与新招标均用 `source_from='RFX'`；`'BID'` 仅指几乎不用的老招标）
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

### 场景9: 新招标单(BID)查询与数据修复
- **业务需求**: 查询或修复新招标单（BID开头）的数据，如评标结果查询、修复为待定标状态等
- **共用表**: 新招标单与询价单共用 `ssrc_rfx_*` 系列表（详见"招标单与询价单共用表体系规则"）
- **关键区分**: 
  - `ssrc_rfx_header.secondary_source_category = 'NEW_BID'` 标识新招标单（注意：不是 `source_from`，`source_from` 是单据来源字段）
  - 评标/结果等关联表 `source_from = 'RFX'`（与询价单相同，新招标不再使用 `'BID'`；`'BID'` 仅指几乎不用的老招标）
  - 状态值与询价单相同，仅术语叫法不同（如"待定标"实质是 `CHECK_PENDING`）
- **处理流程**:
  1. 按BID单号前缀识别新招标单（如 `BID2026070100001`）
  2. 使用相同的 `ssrc_rfx_header` 表查询，状态值使用询价单的枚举值
  3. 在 `ssrc_rfx_header` 上区分单据类型时使用 `secondary_source_category = 'NEW_BID'`
  4. 关联评分/结果表时统一使用 `source_from = 'RFX'`
  5. SQL注释中使用招标术语便于理解（如"待定标"而非"待核价"），但SQL字段值不变

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
  - 需要关注哪些业务状态(询价单状态/招标单状态、报价单/投标单状态等)
  - 需要统计哪些业务指标

### 字段变更检测
- **情况**: 用户提到的字段在当前表中不存在
- **处理**: 参考 `columns_202603131733.md` 检查字段历史，提示可能的字段变更

### MCP (sql-ops) 工具异常或返回空结果
- **情况**: `execute_sql` / `validate_table_columns` / `describe_table` 调用失败、超时、鉴权异常，或查询返回 0 行/无匹配字段
- **处理（必须遵循，禁止编造）**:
  - 该步骤本应取得的真实值（如 `tenant_id`、`rfx_header_id`、字段值）**一律改用占位符** `{tenant_id}` / `{rfx_header_id}` / `{字段名}` 等
  - 在 SQL 注释/回复中显式标注：`⚠️ 以下占位符因 sql-ops 校验/查询异常未能获取真实值，请人工确认后替换：xxx`
  - 若关键前置值（如 `tenant_id`）缺失，且后续逻辑强依赖它，应**停止生成可执行 SQL**，先向用户说明异常并请求确认，不要臆造串联
  - 写操作（UPDATE/DELETE/INSERT）本就禁止用 `execute_sql` 执行，异常时更应保留占位符交人工处理

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
   - **询价单（RFX）SQL模板**: 包含询价单/招标单基础查询、公司信息查询、报价单/投标单查询、评分/评标查询、聚合统计、数据修复等子分类
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
   - `bid_result_statistics.sql` (招标单定标结果统计)
   - `quotation_comparison.sql` (报价单对比分析)
   - `expert_scoring_statistics.sql` (专家评分统计)
3. **注释说明**: 在文件头部添加详细的业务逻辑注释，新招标单SQL需标注 `secondary_source_category = 'NEW_BID'`，评标/结果表 `source_from` 仍为 `'RFX'`


