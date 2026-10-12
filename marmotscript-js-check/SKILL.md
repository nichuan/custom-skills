---
name: marmotscript-js-check
description: 检查与排查 SRM 后端定制开发中的 MarmotScript（JS 脚本）代码问题。适用于全部 MarmotScript 类型脚本：ADAPTOR 适配器（文件名含 |ADAPTOR|，如 SITF_*/SSRC_*）、SCRIPT_LIB 脚本库（文件名含 |SCRIPT_LIB|）、QUERY_BLOCK 查询块、埋点脚本。覆盖 SCRIPT_LIB 五种触发形态（marmot_api_rewrite 挂载 / marmot_api_publish 发布 / marmot_data_import 导入 / marmot_scheduler 调度 / marmot_queue_consumer 消费）与工作流服务调用（hwfp_process_service，serviceMode=SCRIPT）的入参出参契约核对，以及 v3.3 编码规范（require 优先 / 极简 / 乐观锁不自校验）与 checkJs 类型问题排查。当用户要求检查/审查/review JS 脚本、排查脚本报错或不生效、核对挂载点/API 出入参数、校验脚本引用的表/字段/查询块/代码块/虚拟表/Lov 配置时使用。触发关键词：检查脚本、review 脚本、排查、脚本报错、不生效、找不到挂载点、QueryBlock not found、出入参数、调度脚本、cron、工作流脚本、serviceCategory、serviceCode、租户分表、spfm_rel_table_record、marmot_script_library、类型爆红、MarmotScript、SRM 脚本。
---

# MarmotScript（SRM JS 脚本）检查

## Overview

按八阶段 SOP 检查 MarmotScript 脚本：语法与结构 → 全局对象/API 签名 → 数据表与字段 → 数据配置 → 依赖脚本 → 业务逻辑 → 输出报告 → 编码规范核对（v3.3）。规范依据 `srm-adaptor` / `srm-script-container` / `srm-script-parent` 三个代码库源码梳理。完整 API 表、执行流程、存储表清单、易错点见 `references/spec.md`。

**任务分流（先判断再动手）**：

| 现象 | 走法 |
|---|---|
| 线上报错 / 有 traceId / 脚本"没被调用" | **先看日志**：SLS 按 traceId 拉全链路（`java-troubleshoot`）→ 再回本 skill 做静态校验。「日志 → 代码 → 数据库」顺序不可打乱，禁止跳过日志直接断言根因 |
| 静态审查脚本（没报错，要 review） | 直接进下面的前置规则 0 + 强制校验 + 八阶段 |
| 只想核对某脚本"挂在哪、能不能触发" | 直接做强制校验 B/C（含 ★6 工作流），输出「命中触发场景」表 |

## 前置规则 0：环境与库名/分表名取值（强制，所有检查必先做）

SRM MarmotScript 运行时数据分两类：① **物理表**（`STD.Database` / `object.query` 直连的真表——库名由 `SchemaUtil.loadSchemaFromTableName` 决定）；② **Rel-Table 虚拟表**（`spfm_rel_table_definition` + `spfm_rel_table_record_<tenantNum>`）。**两类的库名/分表名取值路径完全不同**，搞反了就会查不到数据或越权。

### 0.1 数据分类与库名格式

| 数据来源 | 库/表名格式 | 取值方法 | 示例 |
|---|---|---|---|
| 物理业务表 | `srm`（默认）/ 自定义 schema（按 0.2 顺序匹配） | 由 `SchemaUtil.loadSchemaFromTableName(tableName)` 自动按四层匹配取 schema；运行时 `STD.CurrentContext.getExecutionTenantId()` 路由 | `srm.sodr_po_header`、脚本里写 `STD.Database.table("sodr_po_header")` 即可 |
| **配置表分表**（核心） | `spfm_rel_table_record_<tenantNum>` | `<tenantNum>` = 脚本文件名第一段 `split[0]`（如 `SRM-AUX`），或运行时 `STD.CurrentContext.getTenantNum()` | `SRM-AUX\|SCRIPT_LIB\|X.js` → 查 `spfm_rel_table_record_srm_aux` |
| 公共/0 租户记录 | `spfm_rel_table_record_srm` | 0 租户/平台共享，查 Marmot 全局配置（`global_cross_schema_rule`、`marmot_config` 等） | 平台级 Lov、平台级配置、Marmot 文档 |

### 0.2 物理表 schema 取值——四层顺序匹配（核心，必须背下来）

**实现位置**：`org.srm.boot.marmotscript.util.SchemaUtil.loadSchemaFromTableName(String tableName)`——脚本引擎内由 `ScriptCrossSchemaInterceptor` 自动拦截 SELECT，给 Table 加 schemaName。**默认 schema 写死是 `srm`**（`ConstantsStory.SRM_UNCHANGEABLE_SCHEMA_NAME="srm"`，注释：SRM 设计写死了主库 Schema，实务上无法变动）。

**四层匹配按以下顺序执行，第一层命中即返回**：

| 顺序 | 匹配条件 | 返回 schema | 说明 |
|---|---|---|---|
| ★1 | `tableName.startsWith("spfm")` | `srm` | `SRM_PLATFORM_TABLE_PREFIX="spfm"`（处理配置表历史名称问题；spfm 开头也走 srm） |
| ★2 | 命中配置表 `global_cross_schema_rule` 的某条规则 | 该规则记录的 `schema` | **平台级配置表，0 租户**；字段：`order`（排序）/ `prefix`（表前缀）/ `schema`（目标 schema 名）；Vo：`org.srm.boot.marmotscript.interceptors.CrossSchemaRule`；缓存 30 分钟（`CacheEnabledRelTable.global_cross_schema_rule(null, true)` 全量缓存） |
| ★3 | `tableName == "dual"` | `""` | Oracle dual 表兼容 |
| ★4（兜底） | 上面都不命中 | `srm` | 默认 `srm`（**全部走 SRM 主库**） |

**关键 SQL：查 `global_cross_schema_rule` 当前生效的规则**（0 租户/平台库）：

```sql
-- 0 租户下读 spfm_rel_table_record，按 table_code + 顺序排序
SELECT value1 AS prefix, value2 AS schema, longvalue1 AS description
FROM spfm_rel_table_record
WHERE table_code = 'global_cross_schema_rule'
ORDER BY CAST(value3 AS SIGNED) ASC;   -- value3 = order 字段
```

> 已确认 `global_cross_schema_rule` 是脚本引擎**唯一**的跨库查 schema 配置入口（`ScriptCrossSchemaInterceptor` 头注释："这东西只解决跨库查，不解决跨库写；有且只有脚本引擎依赖这个东西，别的地方不要用"）。

### 0.3 配置表分表名（tenantNum）取值优先级

1. **脚本文件名**：`SRM-AUX|SCRIPT_LIB|SCUX_AUX_DO.js` → `tenantNum = split[0] = "SRM-AUX"`（实现见 `ScriptLoadingRepositoryImpl.loadPlainScript`，断言 `split.length==3`）
2. **运行时 API**：`STD.CurrentContext.getTenantNum()`（返回字符串编码，如 `"SRM-AUX"`）/ `getExecutionTenantId()`（返回数字 ID，用于物理表路由）
3. **不确定时兜底**：先查共享库 `spfm_rel_table_record_srm`（用 table_code + value2/code 看是否有该挂载点/编码），命中即获 `tenantNum`；再切到对应分表复验

**库名小写化规则**：分表实际物理名 = `spfm_rel_table_record_` + `tenantNum.toLowerCase()`（租户编码统一转小写做后缀）。已确认命名样例（见 `DatabaseBlackList.TENANT_REL_ALLOW_LIST`）：`spfm_rel_table_record_srm_xtep` / `srm_ntes` / `srm_weilong` / `srm_hlgf` / `srm_xxjt` / `srm_lotuseu` / `srm_cfmoto`。

**⚠️ `tenantNum` ≠ `tenant_id`（高频搞反，必查项）**：`tenantNum` 是**租户编码字符串**（如 `SRM-ISIMCERE`），`tenant_id` 是**数字主键**（如 `158677`）。分表后缀只能取 `tenantNum.toLowerCase()`（→ `spfm_rel_table_record_srm_isimcere`），**绝不能拼成 `spfm_rel_table_record_158677`**（会报表不存在/查空）。两类表的租户过滤方式不同：

| 表类型 | 租户怎么限 | 说明 |
|---|---|---|
| **Rel-Table 记录表**（`spfm_rel_table_record_<tenantNum>`） | **靠分表名**，不要再加 `tenant_id` 条件 | 分表已按租户隔离；记录常以 `tenant_id=0` + `value1=租户编码` 存储，**加 `tenant_id` 过滤会查空** |
| **物理表**（`hwfp_*`、`sodr_*` 等） | 必须 `tenant_id IN (<当前租户>, 0)` | 与分表机制无关，按租户列过滤 |

### 0.4 铁律

- **禁止跳过 0.2 / 0.3 直接拼 SQL**——`FROM spfm_rel_table_record_<租户>` 必须先确定 `<租户>` 取值；`STD.Database.table("xxx")` 操作的物理 schema 必须先按 0.2 四层匹配确认
- **物理表不存在 ≠ 表不存在**：必须按「物理表 → 虚拟表 → 都不存在」三级判定
- 数据库黑名单：`spfm_rel_table_definition` / `spfm_rel_table_definition_tl` / `spfm_rel_table_record` / `spfm_rel_table_record_*`（除 `DatabaseBlackList.TENANT_REL_ALLOW_LIST` 列出 7 个）均在 `MarmotScript Database: table in blackList` 黑名单，禁止 `STD.Database` 直连，只能走虚拟表 API
- **跨库改写仅 SELECT 生效**：`ScriptCrossSchemaInterceptor` 只改写 SELECT（注释："只解决跨库查，不解决跨库写"）；脚本里写 UPDATE/INSERT/DELETE 不会自动加 schemaName，仍按默认 `srm`/当前租户执行，需谨慎评估
- **拦截器仅脚本引擎内有效**：业务代码（Java Controller 等）不能用此跨库改写机制——会与 SqlPaser 拦截器冲突，必须按业务代码自己的数据源访问

## Workflow Decision Tree（先识别类型，再套用强制校验）

1. 确定脚本文件路径与类型：文件名含 `|ADAPTOR|` / `|SCRIPT_LIB|` / `|QUERY_BLOCK|` 标识。
2. **按前置规则 0 取准 `<tenantNum>`，拿到对应分表 `spfm_rel_table_record_<tenantNum>`**
3. 按脚本类型执行下方强制校验 A/B/C，然后进入七阶段检查。

### 强制校验 A：QueryBlock/CodeBlock 编码（涉及 STD.QueryBlock / STD.CodeBlock 时）

脚本中引用查询块/代码块编码时，**优先在当前工作区文件查找**：本地文件名规则「租户编码|脚本类型|脚本编码」，如 `SRM-AUX|QUERY_BLOCK|SCUX_AUX_QUERY_RFX_BENCHMARK_LINE.xml`、`SRM-AUX|SCRIPT_LIB|SCUX_AUX_RFX_BENCHMARK_LINE_EXPORT.js`。本地能匹配即视为该编码存在且合法；**仅当本地无匹配时**才用 mysql-db-mcp 查数据库存储值（如 `sada_script_template.code`）。不得在本地已存在对应文件时判定「未部署」。

### 强制校验 B：ADAPTOR 类型（文件名含 |ADAPTOR|）

必须先查配置表（虚拟表）`adaptor_static_code`（定义在 `spfm_rel_table_definition`，记录在 `spfm_rel_table_record_<租户>`，字段映射 value1=service / value2=taskCode / longvalue3=description / longvalue4=script / value5=enableTenantLevel）：

```sql
SELECT value1 AS service, value2 AS taskCode, longvalue3 AS description, longvalue4 AS script, value5 AS enableTenantLevel
FROM spfm_rel_table_record_<租户>
WHERE table_code = 'adaptor_static_code' AND value2 = '<taskCode>';   -- taskCode=文件名第三段，如 SITF_SOURCE_RESULT_EXP_INVOKE
```

三步：① 确认 `service`（并查 `sada_adaptor_task_header` 的 `enabled_flag`/`input_entity_code`/`apply_tenant_num` 确认启停与输入结构）；② 按服务反查该挂载点 `script` 示例；③ 比对出入参数合规性（`input.inData.inputParam` 字段名/层级/类型）。未找到记录 → P1「挂载点未配置」，不得仅凭本地文件存在即认为已部署生效。

### 强制校验 C：独立脚本（SCRIPT_LIB，文件名含 |SCRIPT_LIB|）

> **概念定位**：SCRIPT_LIB 类型 = Marmot **独立脚本**（Independent Script）。与 ADAPTOR 埋点脚本（绑定到 SRM 标准程序某事件点）相反，独立脚本**与标准程序解耦**，仅托管在 Marmot 工作台，由其他 Marmot 配置表「挂到触发场景」上才执行。脚本文件名按 `|` 分三段：`tenantNum|type|code`（实现见 `ScriptLoadingRepositoryImpl.loadPlainScript`：`split[0]/split[1]/split[2]`）。

SCRIPT_LIB 脚本的「触发形态」是**多对一**关系——一份脚本可能被多个配置表挂载/调用，或根本没挂载（白占资源）。**优先按下表的优先级穷举五种触发形态**，命中即确定其在生产真实可触发的场景：

| 优先级 | 触发形态 | 虚拟表 table_code | 关键字段 | 命中后的处理 |
|---|---|---|---|---|
| ★1 | **功能 API 挂载**（前后置脚本） | `marmot_api_rewrite` | `value2`=apiCode / `value3`=scriptCode / `value5`=beforeScriptCode / `value4`=enable / `longvalue2`=serverName / `longvalue3`=beanName / `longvalue4`=methodName | 按 `serverName` 定位代码仓库，扫描 `beanName.methodName` 的 Controller，比对 `input.parameter / input.body / input.responseBody` 与脚本入参出参 |
| ★2 | **API 发布**（独立 API 对外） | `marmot_api_publish` | `value1`=code（API 唯一编码）/`value2`=tenantNum / `value3`=scriptCode | 按返回值约定 `{body, header, httpStatus}` 检查；body 必须 string 或 buffer，前端 URL 由 `marmot_api_publish` 自动生成 |
| ★3 | **功能数据导入** | `marmot_data_import` | value1=templateCode / value2=tenantNum / value3=scriptCode / 长字段=验证/导入方式 | 校验 `input.data/info/args`（批量数组 vs 单条对象，逐条 vs 批量的 4 种组合），校验出错返回 `{result:'false',errorMsg:{行号:msg}}` |
| ★4 | **调度任务** | `marmot_scheduler` | value1=cron / value2=tenantNum / value3=scriptCode | 校验 cron 表达式合理性、`input` 为系统传入（含 timeStamp） |
| ★5 | **Topic 消费端** | `marmot_queue_consumer` | value1=topic / value2=tenantNum / value3=scriptCode | 校验幂等处理（重复消费）、确认租户上下文 |

**核心校验 SQL（穷举所有触发，按优先级逐个查）**（库名取值见「前置规则 0」）：

```sql
-- ★1 API 挂载
SELECT value2 AS apiCode, value3 AS scriptCode, value5 AS beforeScriptCode, value4 AS enable,
       longvalue2 AS serverName, longvalue3 AS beanName, longvalue4 AS methodName
FROM spfm_rel_table_record_<tenantNum>
WHERE table_code = 'marmot_api_rewrite'
  AND (value2 = '<脚本编码>' OR value3 = '<脚本编码>' OR value5 = '<脚本编码>');

-- ★2 API 发布
SELECT value1 AS code, value2 AS tenantNum, value3 AS scriptCode
FROM spfm_rel_table_record_<tenantNum>
WHERE table_code = 'marmot_api_publish' AND value3 = '<脚本编码>';

-- ★3 数据导入
SELECT value1 AS templateCode, value2 AS tenantNum, value3 AS scriptCode
FROM spfm_rel_table_record_<tenantNum>
WHERE table_code = 'marmot_data_import' AND value3 = '<脚本编码>';

-- ★4 调度
SELECT * FROM spfm_rel_table_record_<tenantNum>
WHERE table_code = 'marmot_scheduler' AND value3 = '<脚本编码>';

-- ★5 Topic 消费
SELECT * FROM spfm_rel_table_record_<tenantNum>
WHERE table_code = 'marmot_queue_consumer' AND value3 = '<脚本编码>';
```

**★4 调度脚本专项（高频坑，命中后必查）**——调度与 API 发布的脚本形状**完全不同**，照抄 API 模板即错：

| 检查项 | 正确契约 | 错误写法（应报 P1/P2） |
|---|---|---|
| 入参 | `input` = 调度参数 `Map<String,String>`（jobParam 仅 `{marmotScriptLibraryCode}`），签名写 `function process(input)` | 照抄 `function process({ method, parameter = {}, header = {}, body = "" })` |
| 返回值 | `MarmotSchedulerTaskRunner` **丢弃返回值**并恒返回 `SUCCESS` | 以为 `return false` 能标记失败 |
| 失败标记 | **必须 `throw`** 才走任务失败策略（重试/忽略） | 静默 return |
| 执行上下文 | `UserDetailRestoreUtils.executeWithAnonymous` → **匿名用户**，取租户必须用 `STD.CurrentContext.getExecutionTenantId()`（"require 优先"的合理例外，`@M/v1/context` 的 loginUser 在匿名上下文不可靠） | 用 `loginUser.executionTenantId` 取租户 |
| 事务 | 执行器带 `@Transactional(rollbackFor = Throwable.class)`；脚本抛异常回滚本次全部更新 | 抛异常前未确认幂等/可重试 |
| 日期时区 | 凌晨执行时 `new Date().toISOString()` 仍是 UTC 前一天 → 用全局 `moment().utcOffset(8).format("YYYY-MM-DD")`（主 d.ts 已注入 `moment`，**无** `moment-timezone`） | 用 UTC / `moment-timezone` 模块 |
| 分页批处理 | `objectOperation.page` **首页是 `page: 0`**；**先只读分页收集数组**（数据不变，页码递增安全），再按批 `updateOptional({records, fields})` 提交 | 边查边改 + `page++`——已处理记录退出查询条件，后续页 offset 前移**批量漏数据** |

> 平台机制权威依据：本地适配器源码 `/Users/kaitong/project/zhenyun/srm-adaptor`（`org/srm/marmot/infra/job/MarmotSchedulerTaskRunner.java`、`org/srm/marmot/service/impl/MarmotSchedulerServiceImpl.java`），比工作区文档更权威。

**铁律**：

1. **内容载体 + 触发载体是两表**。脚本代码本体存在 `marmot_script_library`（独立于 5 个触发表，必须确认内容部署：`WHERE table_code='marmot_script_library' AND code='<脚本编码>'`）。该表带**「分类」字段**，定位脚本时必须把分类一并作为筛选条件，否则可能跨分类误命中同名 `code`。即使内容已部署、5 个触发表都没命中 → 该脚本不会被执行 → 报告中明确标出「未配置触发场景，P1」。
2. 同一脚本可能**多触发表同时命中**，必须按 ★1→★5 全量列出，不能只查 ★1 就停。
3. **跨租户防护**：所有 5 张表都按 `tenantNum` 隔离，禁止跨租户 join 5 张表（与租户隔离铁律叠加）。
4. **API 挂载命名**：`apiCode` 是基于 URL 的机械转换（`/`→`_`，大写），MARMOT_API_REWRITE 中禁止同名（重复时 spring 启动报错 `marmot api code of marmot api rewrite can not repeated`）。如脚本被挂到 1 个 apiCode 下的多个租户，按 `value1`（tenantNum）区分。
5. 不再需要"先查 rewrite、命中就当挂载"的旧假设——脚本即使被 rewrite 挂载过，也可能额外作为 publish / scheduler 的独立入口使用，必须全量查。

### 强制校验 C-扩展 ★6：工作流服务调用（serviceMode = SCRIPT）

> 业务对象：`hwfp_process_service`（流程定义使用服务定义记录表）；`serviceCode` 是工作流服务编码（**不携带脚本类型/租户编码**），通过 `hwfp_service_definition.scriptCode` 关联到 `marmot_script_library` 里的脚本本体。

**调用链**：`hwfp_process_service` → `hwfp_service_definition`（含 `scriptCode` + `serviceMode`）→ `MarmotScriptService.getMarmotScriptResult` → `MarmotScriptLibraryHelper.independentScriptExecute(scriptCode, tenantNum, inputObj)`。

**第一步：查服务定义**（按 serviceCode 找到对应 serviceMode 与 scriptCode）：

```sql
-- hwfp_service_definition：serviceCode → serviceMode + scriptCode
SELECT service_code, service_mode, service_type, service_category, script_code, service_tenant_id, enabled_flag
FROM hwfp_service_definition
WHERE service_code = '<脚本编码>' AND tenant_id IN (<当前租户>, 0);   -- 0 租户共享服务
```

**第二步：查流程绑定**（看哪些流程/节点用了该服务）：

```sql
-- hwfp_process_service：哪些 processKey + nodeId 引用了该 serviceCode
SELECT process_key, process_version, service_category, service_mode, node_id, node_type, node_name
FROM hwfp_process_service
WHERE service_code = '<脚本编码>' AND tenant_id = <当前租户>;
```

**第三步：按 `serviceCategory` 检查脚本返回值契约**（**所有 ★6 命中脚本必须按对应契约检查返回值类型**）：

| serviceCategory | 用途 | **脚本返回值契约** | 关键实现位置 |
|---|---|---|---|
| `APPROVAL_CANDIDATE_RULE`（`ActivitiConstants.APPROVAL_CANDIDATE`） | **审批规则**：决定审批人 | **返回员工编码数组**——支持 JSON 数组 `["u1","u2"]`、逗号分隔字符串 `"u1,u2"`、单值 `result="u1"` | `ServiceHelper.asCollection`（ServiceHelper.java:634-654），Collection/String/单值三态识别 |
| `SEQUENCE_CONDITION` | **跳转条件**（sequenceFlow 条件） | **必须返回 boolean**——脚本 `result` 必须是 `"true"/"false"` 或 `true/false`；不返 boolean 报错 `DATA_INVALID` | `ServiceHelper.getExpression(..., Boolean.class, "SEQUENCE_CONDITION")` + `TYPE_METHOD.put(Boolean.class, ".asBoolean()")`（ServiceHelper.java:82-89, 196-201, 206-208） |
| `APPROVAL_STRATEGY` | 审批方式 | `expression` 或常量字符串 | `ApproveChainUserTaskHandler.approveMethodFormConstructor` |
| 结束监听器（`END_LISTENER`） | 流程结束 | 返回值经 `formatScriptDataType` 刷入 `act_hi_varinst`（按 processInstanceId + variableType 自动转 Double/Boolean/Long/String） | `ServiceHelper.formatScriptDataType`（ServiceHelper.java:353-400） |
| **服务任务通用** | 任意节点 | **执行结果无效特殊返回**：① `args.NOT_EXECUTE_LISTENER="Y"` → `ServiceExecuteResult.NULL` 直接返回不执行；② 脚本抛 `BusinessException` → 抛通用异常；③ 抛 `ScriptContainerExecutionException` → 抛 `hwfp.error.service.marmot.execution_exception`；④ 脚本未抛错但 `result` 为空 → 走 default 分支返回 NULL | `MarmotScriptServiceImpl.getMarmotScriptResult`（捕获三类异常 → 抛通用异常）+ `ServiceHelper.getResult` default 分支（ServiceHelper.java:344-346） |

**`serviceCode` 与 `scriptCode` 的关系（容易混淆！）**：
- `hwfp_process_service.serviceCode` = 工作流服务编码（如 `SCUX_AUX_PR_APPROVE_CANDIDATE`）—— 流程图里 BPMN 引用的就是这个
- `hwfp_service_definition.serviceCode` = 同上
- `hwfp_service_definition.scriptCode` = **裸脚本编码**（不带 `SRM-AUX|SCRIPT_LIB|` 前缀；如 `SCUX_AUX_PR_APPROVE_CANDIDATE`）
- `marmot_script_library.code` = 同 `scriptCode`
- 走查链：脚本文件名 `SRM-AUX|SCRIPT_LIB|SCUX_AUX_PR_APPROVE.js` → `marmot_script_library.code="SCUX_AUX_PR_APPROVE"` → `hwfp_service_definition.scriptCode="SCUX_AUX_PR_APPROVE"` → `hwfp_service_definition.serviceCode="SCUX_AUX_PR_APPROVE_CANDIDATE"` → `hwfp_process_service.serviceCode="SCUX_AUX_PR_APPROVE_CANDIDATE"`

**铁律**：
1. **`serviceCode` 不携带脚本类型/租户编码**——脚本工程师配错 `serviceCode` 带了 `SRM-AUX|SCRIPT_LIB|` 前缀或带横线租户号 → 全工作流审批找不到该服务，流程会报 `ERROR_SERVICE_NOT_FOUND`（`hwfp.error.service.not_found`）
2. **三个 serviceCategory 必查返回值类型**：审批规则→员工编码数组 / 跳转条件→boolean / 服务任务→result 可空（特殊处理）。错返类型会导致流程卡死或审批人拿不到
3. **跨租户服务**：0 租户的 `hwfp_service_definition` 可被各租户 `hwfp_process_service` 引用（`service_tenant_id=0` 共享）——但脚本本体仍在引用方租户的 `marmot_script_library` 中（`independentScriptExecute` 接收的 `tenantNum` 是当前流程租户 `tenant.getTenantNum()`，不是 `service_tenant_id`）
4. **业务流程参数注入**：脚本 `process(input)` 收到 `args`（= 流程当前所有变量）+ `requestConstants`（= serviceDefinition.parameterList 转换的固定参数 Map，存到 `args.requestConstants`）
5. **脚本抛异常会被吞掉**：SCRIPT_MODE 默认事务 `Propagation.REQUIRES_NEW`（`MarmotScriptServiceImpl.java:28`），脚本回滚不影响主流程事务；脚本抛 `BusinessException` → 转 `CommonException`；抛 `ScriptContainerExecutionException` → 抛 `hwfp.error.service.marmot.execution_exception`（提示信息含 serviceCode + 错误 + scriptCode）

## 七阶段检查步骤（严格按序执行）

### 阶段一：语法与结构

- [ ] `node --check` 无语法错误
- [ ] 存在 `process(input)` 入口函数
- [ ] `input` 解析在 try 块内或做了空值兜底（GET 请求 body 可能为空串）
- [ ] 无未声明变量（隐式全局）、缺分号、死代码
- [ ] **TS 类型检查（受检目录必做）**：脚本位于 `脚本服务/`（`jsconfig` 开了 `checkJs: true`）时必须 `read_lints` 到 0 错误。判定要点：
  - `@M/v1/*` 报 TS2307 / `STD`·`BIZ`·`_` 报 TS2304 = **类型环境缺失**（jsconfig include 未引主 d.ts），属环境问题不是脚本问题
  - `@M/v1/object` 的 `query` 返回 `unknown[]`、`fetchById/update/create` 返回 `unknown` → 访问记录字段 TS2339，最省事在 **require 处**统一 `/** @type {any} */` 包装
  - `["debug","info",...].reduce((o,k)=>..., {})` 动态建对象推断不出属性（TS2339）→ 改字面量对象
  - 形参默认值 `function process({ parameter = {} })` 会把 `parameter` 收窄成 `{}` → 用 `const {...} = /** @type {any} */ (parameter)`
  - `改造案例/` 下无 jsconfig（`checkJs` 默认 false），**不能拿它「不爆红」当类型正确的依据**

### 阶段二：全局对象与 API 签名（对照 references/spec.md 的 API 表）

- [ ] `STD.xxx` / `BIZ.xxx` / `OTHER.xxx` 调用核对参数个数与类型
- [ ] `require('@M/v1/xxx')` 确认组件存在且方法签名正确
- [ ] `STD.FeignClient.selectClient(serverId)`：serverId 须在白名单（srm-interface/srm-adaptor 等）；`object.query/queryOne/update/updateOptional` 必须对象参数 `{object, condition, ...}`
- [ ] 涉及大整数/金额字段必须用 `SAFE_JSON` 或 `JSONbig`，避免默认 JSON 精度丢失
- [ ] 不要轻信 `global.d.ts` 简化定义，真实签名以 `@M/2021/std/index.js`、`@M/2021/biz/index.js`、`@M/v1/*/index.js` 为准（如 `STD.LovHelper.queryIdpLov` 实际支持 1 参或 2 参）

### 阶段三：数据表与字段（mysql-db-mcp）

> **校验顺序固定**：① 先按「前置规则 0」取准 `<tenantNum>` → 算出 `spfm_rel_table_record_<tenantNum>`；② 再按物理表 / 虚拟表分流校验

- [ ] 脚本引用的每张表用 `describe_table` 校验存在性
- [ ] 物理表不存在 → 查 `spfm_rel_table_definition`（table_code）确认是否虚拟表（字段映射在 `mapping_json`）；仅当物理表和配置表都不存在才判定「表不存在」
- [ ] **虚拟表元数据有、物理表 1146 的例外**：`spfm_rel_table_definition` 中存在该表定义，但 `SHOW CREATE TABLE` 在 archery 覆盖的 SaaS `srm` 库查不到（1146）时，**不要断言「表未建」**——先确认该租户配置表的物理存储是否落在别的实例/库
- [ ] 每个字段核对：拼写、大小写、类型、精度（decimal 位数）——尤其金额/比率字段与 `attribute_decimal10/11/12` 等扩展字段
- [ ] 虚拟表字段用 `mapping_json` 的 `name`（业务名）核对；脚本里直写 `longvalueN`/`valueN` 属规范问题（见阶段八「配置表字段」行）

### 阶段四：数据配置校验

- [ ] Lov：`hpfm_lov_value` 查脚本硬编码 value 存在且 enabled
- [ ] 虚拟表数据：`spfm_rel_table_record_<tenantNum>`（按前置规则 0 取得的分表名）查脚本查询条件对应的实际数据（如 reviewType=17）
- [ ] 查询块/代码块编码：按「租户编码|QUERY_BLOCK|脚本编码」/「租户编码|SCRIPT_LIB|脚本编码」先本地后数据库（同强制校验 A）；代码块注意跨租户 `租户号:代码块编号` 格式
- [ ] OutBound：`STD.HttpClient` 访问域名是否已配置白名单
- [ ] ADAPTOR 挂载点：执行强制校验 B，确认 `<tenantNum>` 已按前置规则 0 取得
- [ ] **独立脚本（SCRIPT_LIB）触发方式**：执行强制校验 C（★1→★5 五张触发表全量穷举），输出「命中触发列表」

### 阶段五：依赖脚本与跨脚本

- [ ] 目标脚本/查询块/代码块已部署且接口契约一致
- [ ] 同目录存在旧版本/prod-bug 副本时 diff 对比确认修复点与差异
- [ ] 独立脚本对应的 5 个触发表记录与脚本 process(input) 的入参出参一致

### 阶段六：业务逻辑正确性

- [ ] 分支遗漏（GET/POST 分支、空数组、null 对象）
- [ ] 异常路径脏数据（先写后抛错）
- [ ] 事务：`update` 带指纹校验（须用 query 结果）、`updateOptional` 用 fields 限定
- [ ] 循环/大数据量：单批 ≤ 100，记录数 > 10000 报错
- [ ] 资源：避免死循环、超长 sleep（最大 240000ms）、大数据内存占用（340s / 25s CPU / 内存限制）

### 阶段七：输出报告

- [ ] 按 P0-P3 汇总问题
- [ ] 每个问题给出：位置（文件:行号）、现象、根因、证据（SQL 结果/源码）、修复建议
- [ ] 区分「脚本代码问题」与「环境/配置缺失问题」
- [ ] **修复建议要在统一层根治**：发现一处问题要**全目录扫描同类写法**，面问题在统一层一次性修（抽公共方法/统一封装），不在调用点逐处打补丁
- [ ] **报告落盘位置**：分析/检查/排障类必须输出 `.md` 到 `<所在项目>/.codebuddy/memory/AI 输出文档/`，命名 `{主题}_{描述}_分析报告.md` 或 `diagnose-{traceId}-{日期}.md`；结构＝背景 → 证据链 → 根因 → 验证 → 建议。（纯"改代码"类任务**不出报告**，只给「改了什么 + 关键差异」）

### 阶段八：编码规范核对（v3.3 基线，出 P3/规范项）

按现行编码约定逐条核对（不满足记为 P3 或按影响升级；**不得为"更规范"而改变业务逻辑**）：

| 项 | 约定 | 违规写法 |
|---|---|---|
| 模块引入 | **require 优先**：有 `@M/v1/xxx` 模块必须 `require`；仅无对应模块才用 `STD.*` / `BIZ.*` 全局 | 明明有 `@M/v1/math` 却用 `STD.ElMath` |
| 头部极简 | 业务脚本只 `require` 实际用到的能力，不整块拷模板头部；重复片段抽常量/小函数 | 未使用模块（`math`/`language`/`momentTz`…）整段保留 |
| 租户 ID | `loginUser.executionTenantId`（非匿名场景）；匿名/调度场景才用 `STD.CurrentContext` | 混用、或在调度脚本里用 loginUser |
| 日志 | `require("@M/v1/logger2")` + 变参 `logger.info("msg {}", x)` | 旧 `logger.info({ msg, strs })` 对象形式 |
| 入口解构 | `let requestBody = JSONBig.parse(body \|\| "{}")` | 直接 `JSON.parse(body)`（大整数丢精度） |
| 乐观锁 | 业务层**不自校验** `objectVersionNumber`；只 `existing.objectVersionNumber = requestBody.objectVersionNumber` 后交 `objectOperation.update` | `Assert.isTrue(a === b, "数据已被他人修改")` 之类的自校验 |
| update 选型 | 需并发保护 → `update`（record 带 objectVersionNumber）；只改指定字段 → `updateOptional({records, fields})` | `update` 传非 query 结果 / 用 updateOptional 却期望乐观锁 |
| 配置表字段 | 写 `mapping_json` 里的业务 `name`（`templateNum`/`userId`/`businessCode`…） | 直写物理列 `longvalueN` / `valueN` |
| 头部解构 | v3.3 统一头部三段式（标准模块 / 无 require 全局 / 二次封装） | 每脚本自造一套头部 |

> 对存量脚本（`脚本服务/codeBlock.js` 为通用头部模板，243+ 处在用历史 API）**不要批量改写**，也不要逐个 `@ts-ignore`；仅对新脚本/改动过的脚本按 v3.3 要求。

## 严重级别定义

| 级别 | 定义 | 判定标准 |
|---|---|---|
| **P0** | 功能必然失败（上线阻塞） | 语法错误；必现空指针；引用的表/字段不存在；关键配置缺失导致必现报错 |
| **P1** | 部分功能不可用 / 特定路径必报错 | 分支缺失（GET 未传 body）；条件用错（reviewType=17 查不到数据）；查询块未部署；挂载点未配置 |
| **P2** | 潜在隐患 | 参数个数与 API 不符（不触发时无害）；未判空导致边界异常；低资源下超时风险 |
| **P3** | 代码规范 | 缩进/分号/未声明变量/死代码/注释缺失 |

## 高频问题速查（历史问题库，完整版见 references/spec.md）

| # | 问题 | 判定方法 | 级别 |
|---|---|---|---|
| 1 | 脚本引用的虚拟表在物理库不存在 | `describe_table` 失败 → 查 `spfm_rel_table_definition` | P0 |
| 2 | 硬编码条件查不到配置数据（如 reviewType=17 但配置只有 1-16） | 查 `spfm_rel_table_record_*` + Lov | P1 |
| 3 | Lov 值不存在/已失效 | 查 `hpfm_lov_value` | P1 |
| 4 | 查询块/代码块未部署（报 QueryBlock not found） | 本地「租户|类型|编码」查找 → 数据库兜底（强制校验 A） | P1 |
| 5 | ADAPTOR 脚本不生效/找不到挂载点（SITF_*/SSRC_*） | 强制校验 B | P1 |
| 5b | 独立脚本（SCRIPT_LIB）未配置任何触发方式（5 张触发表全未命中）— 脚本部署了但永远不会被执行 | 强制校验 C（★1→★5 全量查询） | P1 |
| 5c | 独立脚本已挂载到 marmot_api_rewrite 但 enable=0 / 入参不匹配 Controller 请求体 | `marmot_api_rewrite.value4=enable`、按 serverName+beanName+methodName 扫 Controller 比对 body/parameter 字段名层级 | P1 |
| 5d | 独立脚本被发布为 API（marmot_api_publish）但返回值 body 非 string/buffer、httpStatus 越界（不在 200-500） | 强制校验 C★2 + 校验返回结构 | P1 |
| 5e | 独立脚本被工作流 `serviceMode=SCRIPT` 调用，但 `serviceCode` 拼错（带了 `SRM-AUX\|SCRIPT_LIB\|` 前缀或租户号）—— 全工作流报 `ERROR_SERVICE_NOT_FOUND` | 强制校验 C★6 走查链：脚本文件名 → marmot_script_library.code → hwfp_service_definition.scriptCode → hwfp_service_definition.serviceCode → hwfp_process_service.serviceCode，**serviceCode 必须为裸编码** | P1 |
| 5f | 独立脚本作工作流审批规则（serviceCategory=APPROVAL_CANDIDATE_RULE）但返回值非员工编码数组（如返回对象/布尔）—— 审批人拿不到 | 强制校验 C★6 审批规则契约：脚本 `result` 必须是 JSON 数组 `["u1","u2"]` 或逗号分隔 `"u1,u2"` 或单值 `result="u1"`（ServiceHelper.asCollection 兼容三态） | P1 |
| 5g | 独立脚本作工作流跳转条件（serviceCategory=SEQUENCE_CONDITION）但返回值非 boolean—— sequenceFlow 走错分支/卡死 | 强制校验 C★6 跳转条件契约：脚本 `result` 必须是 `"true"/"false"` 或 `true/false`（ServiceHelper.getExpression + TYPE_METHOD 强制 .asBoolean()） | P1 |
| 6 | GET 分支 body 为空导致 `body.xxx` 报 TypeError | `STD.SAFE_JSON.parse(body)` 与 body 使用在 try 内/有兜底 | P1 |
| 6 | `queryOne` 返回 undefined 后直接取属性 | 判空或 `exceptionOnNotFound: true` | P1 |
| 7 | 大整数经默认 JSON 丢失精度 | 检查是否用 `SAFE_JSON`/`JSONbig` | P2 |
| 8 | FeignClient 响应未检查 `failed` 字段 | 应使用 `STD.FeignClient.checkFeignResponse` | P2 |
| 9 | HttpClient 域名未配 OutBound | 检查域名白名单 | P1 |
| 10 | `object.update` 传入非 query 结果（指纹校验失败） | 确认更新记录来自 query 结果 | P1 |
| 11 | 脚本里 SELECT 跨库表名走到了非预期 schema（应走 `srm` 却走了业务自定义库） | 查 `global_cross_schema_rule`（0 租户 `spfm_rel_table_record`）按 `value3=order` 排序看规则列表；规则顺序错（如短前缀在前）会让长前缀的表被错误短路命中 | P1 |
| 12 | 用 `tenant_id`（数字）当分表后缀，`FROM spfm_rel_table_record_158677` → 表不存在/查空 | 分表后缀必须是 `tenantNum`（编码）小写；`tenant_id` 只用于物理表 | P1 |
| 13 | Rel-Table 记录查询加了 `tenant_id` 条件 → 查不到记录（实际以 `tenant_id=0` + `value1=租户编码` 存储） | 分表已按租户隔离，去掉 `tenant_id` 条件，按分表名 + table_code/value 过滤 | P1 |
| 14 | `marmot_script_library` 按 `code` 查到多条/查错脚本（未带「分类」条件） | 定位脚本时 `code` + **分类** 同时筛选 | P2 |
| 15 | 调度脚本按 API 发布模板写（含 method/parameter/header/body）、以为 `return false` 能标失败 | ★4 调度专项：入参为 `Map<String,String>`、返回值被丢弃、**必须 `throw`** | P1 |
| 16 | 受检目录（`脚本服务/`，`checkJs: true`）下脚本 TS 报错（TS2307/TS2304/TS2339） | 环境缺 d.ts vs 脚本真问题分流；脚本侧按 object 返回值 `/** @type {any} */`、字面量 logger、`any` 承接默认形参 处理 | P2/P3 |
| 17 | `@M/v1/user.selectUserInfoById` 按旧版单值调用（旧版 1-38-0 只收单值）——本应支持批量 | 核对签名**必须看项目生产 hotfix 分支**（如 `1-69-0-hotfix`）：`{userId: 单值\|数组}`，传数组返数组；模块**无 `selectById`** | P2 |

## 报告模板

```markdown
## 检查结论：<脚本名>（<客户/变更单>）

### 〇、环境与库名/分表名取值
| 项 | 取值 |
|---|---|
| tenantNum | <脚本文件名 split[0] 或 STD.CurrentContext.getTenantNum()> |
| 分表名 | spfm_rel_table_record_<tenantNum.toLowerCase()> |

### 一、表结构校验
| 脚本引用对象 | 校验结果（存在性/字段/类型） |
|---|---|

### 二、命中触发场景（SCRIPT_LIB 类型必出）
| 触发表 | 命中 | 配置详情 | 入参出参一致性 |
|---|---|---|---|
| marmot_api_rewrite（API 挂载） | ✅/❌ | apiCode / enable / serverName.beanName.methodName | 比对 Controller 接口请求体 |
| marmot_api_publish（API 发布） | ✅/❌ | code / 自动生成 URL / 返回值约定 | 校验 body/header/httpStatus |
| marmot_data_import（数据导入） | ✅/❌ | templateCode / 验证/导入方式 | input.data/info/args 结构 |
| marmot_scheduler（调度） | ✅/❌ | cron / 触发时间 | 校验幂等/异常处理 |
| marmot_queue_consumer（Topic） | ✅/❌ | topic | 校验重复消费防护 |
| **hwfp_process_service（工作流服务调用，★6）** | ✅/❌ | serviceCode / serviceCategory / serviceMode | **按 serviceCategory 校验返回值契约**：<br>• APPROVAL_CANDIDATE_RULE → 员工编码数组<br>• SEQUENCE_CONDITION → boolean<br>• END_LISTENER / 审批方式 → result 可空（特殊） |

### 三、问题清单
#### 🔴 P0：<问题标题>
- 位置：文件:行号
- 现象：
- 根因：
- 证据（SQL/源码）：
- 修复建议：
#### 🟠 P1：...
#### 🟡 P2：...
#### ⚪ P3：...

### 四、版本对比（如有旧版/修复版）
### 五、修复建议（按优先级）
```

## Resources

### references/

- `spec.md`：完整检查规范原文——脚本执行流程、三个代码库职责、STD/BIZ/@M/v1 完整 API 表、资源限制、异常处理机制、存储表清单、检查注意事项与易错点。核对具体 API 签名、存储表字段、执行细节时加载。
