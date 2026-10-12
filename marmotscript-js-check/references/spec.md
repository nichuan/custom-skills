# MarmotScript（SRM JS 脚本）检查规范（完整原文）

> 版本：v1.1（2026-10-12 增补：tenantNum≠tenant_id 辨析、★4 调度契约、marmot_script_library 分类、TS 检查、阶段八编码规范核对、报告落盘）
> 依据：`srm-adaptor`、`srm-script-container`、`srm-script-parent` 三个代码库源码（GitLab: operation-tech-platform）梳理得出。
> 适用范围：SRM 后端定制开发中的全部 MarmotScript（ADAPTOR 适配器 / SCRIPT_LIB 脚本库 / QUERY_BLOCK 查询块 / 埋点脚本）的代码检查与排查。

---

## 第一部分：脚本执行流程（检查的前置认知）

### 0. 环境与库名/分表名取值（强制前置）

> **目的**：所有 SQL 在写 `FROM spfm_rel_table_record_<租户>` 之前，必须先确定 `<租户>` 取值；写物理表操作之前，必须明确运行库。两类数据的「库/表名」路径完全不同，搞反就查不到。

#### 0.1 两类数据与库名格式

| 数据来源 | 库/表名格式 | 取值方法 | 示例 |
|---|---|---|---|
| **物理业务表** | `srm`（默认）/ 自定义 schema（按 0.2 顺序匹配） | `SchemaUtil.loadSchemaFromTableName` + `ScriptCrossSchemaInterceptor`（脚本引擎自动 SELECT 改写）；运行时 `STD.CurrentContext.getExecutionTenantId()` 路由 | `srm.sodr_po_header`、`STD.Database.table("sodr_po_header")` |
| **Rel-Table 分表** | `spfm_rel_table_record_<tenantNum>`（核心） | `<tenantNum>` = 脚本文件名 split[0]（如 `SRM-AUX`），或 `STD.CurrentContext.getTenantNum()` | `SRM-AUX\|SCRIPT_LIB\|X.js` → 查 `spfm_rel_table_record_srm_aux` |
| **共享/0 租户记录** | `spfm_rel_table_record_srm` | 0 租户/平台共享（`global_cross_schema_rule`、`marmot_config`、`sada_marmot_constants` 等） | 平台级 Lov、平台级 Marmot 文档 |

#### 0.2 物理表 schema 取值——四层顺序匹配（必背）

**实现位置**：`org.srm.boot.marmotscript.util.SchemaUtil.loadSchemaFromTableName(String tableName)`——脚本引擎内由 `ScriptCrossSchemaInterceptor` 拦截 SQL 自动给 Table 加 schemaName。**默认 schema 写死 = `srm`**（`org.srm.boot.common.ConstantsStory.SRM_UNCHANGEABLE_SCHEMA_NAME="srm"`，注释："SRM 设计写死了主库 Schema，实务上无法变动"）。

**按以下顺序逐层匹配，命中即返回**：

| 顺序 | 匹配条件 | 返回 schema | 说明 |
|---|---|---|---|
| **★1** | `tableName.startsWith("spfm")` | `srm` | `SRM_PLATFORM_TABLE_PREFIX="spfm"`（处理配置表历史名称问题，spfm 开头也走 srm） |
| **★2** | 命中平台级配置表 `global_cross_schema_rule` 某条规则 | 该规则记录的 `schema` | **平台级配置表，0 租户**；字段：`order`（排序）/ `prefix`（表前缀）/ `schema`（目标 schema 名）；Vo：`org.srm.boot.marmotscript.interceptors.CrossSchemaRule`；枚举 `CacheEnabledRelTable.global_cross_schema_rule(null, true)`（30 分钟全量缓存）；**按列表顺序找到第一条 `startsWith` 命中的规则** |
| **★3** | `tableName == "dual"` | `""` | Oracle dual 表兼容 |
| **★4（兜底）** | 上面都不命中 | `srm` | **全部走 SRM 主库 `srm`**（默认 `ConstantsStory.SRM_UNCHANGEABLE_SCHEMA_NAME`） |

**核心 SQL：查 `global_cross_schema_rule` 当前生效规则**（0 租户/平台库，按顺序排序）：

```sql
SELECT value1 AS prefix, value2 AS schema, longvalue1 AS description, value3 AS ruleOrder
FROM spfm_rel_table_record
WHERE table_code = 'global_cross_schema_rule'
ORDER BY CAST(value3 AS SIGNED) ASC;   -- value3 = order 字段
```

**作用域与限制**（来自 `ScriptCrossSchemaInterceptor` 头部注释）：
- "**这东西只解决跨库查，不解决跨库写**"——仅 SELECT 改写；UPDATE/INSERT/DELETE 不会自动加 schemaName，仍走默认 `srm`/当前租户
- "**有且只有脚本引擎依赖这个东西，别的地方不要用**（这个拦截器和 SqlPaser 拦截器是冲突的）"——业务代码（Java Controller / Service）不会走这套改写机制，业务代码要按业务自己的数据源访问
- 来源验证：Release Notes "对象操作器: 支持在配置表 `global_cross_schema_rule` 中配置表对应的 schema 名称"

#### 0.3 物理表操作的两个特殊前缀

| 前缀 | 走 schema | 说明 |
|---|---|---|
| `spfm` 开头（如 `spfm_rel_table_record`、`spfm_cnf_label`、`spfm_event`） | `srm`（★1 命中） | `SRM_PLATFORM_TABLE_PREFIX`；所有 `spfm_` 表整体在 ScriptContext 自动走 srm，禁止 `STD.Database` 直连（黑名单见 `DatabaseBlackList`） |
| `information_schema` | 不改写 | `ScriptCrossSchemaInterceptor.handleTable` 对 `MYSQL_INFORMATION_SCHEMA` 直接 return（保留原 schema） |

#### 0.4 tenantNum 取值优先级（Rel-Table 分表用）

1. **脚本文件名**：`SRM-AUX|SCRIPT_LIB|SCUX_AUX_DO.js` → `split[0]` = `"SRM-AUX"`（实现：`ScriptLoadingRepositoryImpl.loadPlainScript`，断言 `split.length==3`）
2. **运行时 API**：`STD.CurrentContext.getTenantNum()`（字符串编码，如 `"SRM-AUX"`）/`getExecutionTenantId()`（数字 ID）
3. **不确定时**：先查共享库 `spfm_rel_table_record_srm` 命中后反推 `tenantNum`，再切到对应分表复验

**库名小写化规则**：物理分表名 = `spfm_rel_table_record_` + `tenantNum.toLowerCase()`。已确认的命名样例（见 `DatabaseBlackList.TENANT_REL_ALLOW_LIST`）：`spfm_rel_table_record_srm_xtep`、`srm_ntes`、`srm_weilong`、`srm_hlgf`、`srm_xxjt`、`srm_lotuseu`、`srm_cfmoto`——前缀统一 `spfm_rel_table_record_srm_<租户小写>`。

#### 0.4.1 `tenantNum` ≠ `tenant_id`（高频搞反，必查项）

| 概念 | 形态 | 示例 | 用途 |
|---|---|---|---|
| `tenantNum` | **租户编码字符串** | `SRM-AUX`、`SRM-ISIMCERE` | 拼 Rel-Table 分表后缀（`.toLowerCase()`）→ `spfm_rel_table_record_srm_isimcere` |
| `tenant_id` | **数字主键** | `158677` | 物理表（`hwfp_*`、`sodr_*` 等）的租户列过滤 |

**两个高频错误**：

1. **把 `tenant_id` 当分表后缀**：`FROM spfm_rel_table_record_158677` → 表不存在/查空。分表后缀只能是编码小写，**永不是数字**。
2. **给 Rel-Table 记录表加 `tenant_id` 条件**：`SELECT ... FROM spfm_rel_table_record_<tenantNum> WHERE table_code='marmot_api_rewrite' AND tenant_id=158677` → **查空**。配置记录常以 `tenant_id=0` + `value1=<租户编码>` 存储（如 `marmot_api_rewrite.value1=tenantNum`）；分表名本身已按租户隔离，**不要再加 `tenant_id`**。

对照表（租户怎么限）：

| 表类型 | 租户过滤方式 |
|---|---|
| Rel-Table 记录表 `spfm_rel_table_record_<tenantNum>` | **靠分表名**（编码小写）；不带 `tenant_id` |
| 物理表 `hwfp_service_definition` / `hwfp_process_service` / 业务表 | `tenant_id IN (<当前租户>, 0)`（0 = 平台共享） |

#### 0.5 铁律

- **禁止跳过 0.2 / 0.4 直接拼 SQL**——`FROM spfm_rel_table_record_<租户>` 必须先确定 `<租户>`；物理表 schema 必须先按 0.2 四层匹配确认
- **物理表不存在 ≠ 表不存在**：必须按「物理表 → 虚拟表 → 都不存在」三级判定
- **数据库黑名单**：`spfm_rel_table_definition` / `spfm_rel_table_definition_tl` / `spfm_rel_table_record` / `spfm_rel_table_record_*`（除 `DatabaseBlackList.TENANT_REL_ALLOW_LIST` 列出 7 个 `spfm_rel_table_record_srm_*`）均在 `MarmotScript Database: table in blackList` 黑名单，禁止 `STD.Database` 直连，只能走虚拟表 API（注意：这并不影响 `ScriptCrossSchemaInterceptor` 改写 SELECT 的引擎内部路由——引擎自己拿到的 schemaName 是合法 srm）
- **跨库改写仅 SELECT 生效**：UPDATE/INSERT/DELETE 不会自动改写 schemaName，需按业务场景确认是否走跨库
- **拦截器仅脚本引擎内有效**：业务代码（Java Controller / Service）不能用此跨库改写

### 1. 三个代码库的职责

| 代码库 | 职责 | 关键包/模块 |
|---|---|---|
| `srm-adaptor` | 脚本宿主服务：脚本模板部署、API 入口、SRM 业务集成 | `org.srm.adaptor.api.controller.v1`（JsExecuteController）、`org.srm.marmot`（脚本模板/管理）、`org.srm.toxotes`（异常堆栈收集） |
| `srm-script-container` | 脚本执行容器：GraalVM 沙箱、插件引擎、资源控制、异常翻译 | `org.hzero.script.domain.execution`、`org.hzero.script.domain.engine`、`org.hzero.sandbox`、`org.srm.container.domain.supports.v3.plugin`、`resources/_engine_root_/node_modules/@M/**` |
| `srm-script-parent` | 公共库：业务服务调用 adaptor 的客户端（Feign）、FEL 表达式引擎 | `srm-boot-adaptor`（client / ctrl / sandbox / marmothub）、`srm-base-fel` |

### 2. 完整调用链

```
SRM 业务服务（SSRC/SPFM 等）
  └─ srm-boot-adaptor 客户端（Feign 调用 /v1/...）
       └─ srm-adaptor
            ├─ JsExecuteController (/v1/js-execute)：js-test（试运行）/ run-script（按 taskCode 执行）
            ├─ MarmotScriptTemplateController：脚本模板管理（部署到 sada_script_template）
            └─ 各功能点埋点触发（SRM 各模块事件）
                 └─ srm-script-container
                      └─ UniversalScriptExecutionServiceImpl.execute(ScriptRequestVO)
                           ├─ 创建 FakeTxInfo（假事务，含 debugFlag）
                           ├─ ScriptCallFrequencyTracker.trackScriptCall（调用频率）
                           ├─ ServerConcurrencyCtrl.getSemaphore（并发信号量）
                           ├─ 构建 EngineInput(plainScript, rawInputJson, scriptName)
                           ├─ ScriptResourceLevelEnum.autoSettingByLevel（资源级别）
                           ├─ MarmotScriptRuntimeQueueing.checkSemaphoreStatus（队列）
                           ├─ FlyLineFix.TraceTagSupport.initTraceTag（飞线链路）
                           └─ ScriptStaticEngine.eval(engineInput)
                                ├─ buildContextInfo()：构造用户上下文 JSON（userId/tenantId/organizationId/tenantNum/roleId/roleIds/timeZone/language）
                                ├─ BasicExecutionUnitPool.executeWithBEU(scriptName, ...)（借执行单元）
                                ├─ besideContext.init(rawInputJson, userContextInfo)（注入 input）
                                └─ sandbox.eval(script, maxMemory, maxCPUTime, maxTotalTime, callbacks)
                                     └─ 实际执行内容 = 脚本源码 + "\n __storeOutput(process(__input()));"
```

**关键点**：所有脚本统一以 `process(input)` 为入口函数，由引擎自动拼接点火代码执行。检查脚本时必须确认存在 `process(input)` 入口。

### 3. 脚本执行单元（BasicExecutionUnit）的构造

`BasicExecutionUnitStaticFactory.buildBasicExecutionUnit()`：

1. 创建 GraalVM 沙箱（V3 版本）
2. 注入 `_input_box`（BesideContext：承载 input + userInfo）
3. 注入 `_safe_json`（ForScriptDefaultSafeJson：SAFE_JSON 实现）
4. 注入 `__random`（随机工具单例）
5. 将 `initializationClassMap` 中注册的全部插件类通过 `ScriptPluginCentre.newCGLibProxy` 生成代理注入沙箱（这就是 `@M/v1/*` 组件）
6. eval `base/base.js` + `classpath*:script-plugin-*.js`（Marmot 组件初始化）
7. `sandbox.setProtected()` 锁定

### 4. 全局对象体系（检查脚本时对照 API 的真实来源）

#### 4.1 无需 require 即可使用的全局对象

| 全局对象 | 定义位置 | 说明 |
|---|---|---|
| `STD` | `@M/2021/std/index.js` | 标准工具 + 平台功能 Helper |
| `BIZ` | `@M/2021/biz/index.js` | 业务功能 Helper |
| `OTHER` | `@M/2021/other/index.js` | 其他工具 |
| `_` | underscore | `_.chunk/_.groupBy/_.map/_.filter` 等 |
| `moment` | moment | 日期处理 |
| `JSONbig` | json-bigint | 大整数 JSON |
| `Buffer` | buffer | 二进制 |
| `__input()` / `__storeOutput()` | 引擎注入 | 点火函数 |

#### 4.2 `STD` 完整 API（摘自 `@M/2021/std/index.js`）

| API | 签名 | 说明 |
|---|---|---|
| `STD.SimpleException` | `new SimpleException(message)` | 简单异常（逃逸异常监控） |
| `STD.BusinessException` | `new BusinessException(message, code)` | 业务异常（多语言翻译） |
| `STD.BusinessAssert` | `isTrue(condition, message, code)` / `notEmpty(obj, message, code)` | 业务断言 |
| `STD.SAFE_JSON` | `stringify/parse` | 精度+日期安全 JSON（大整数转字符串） |
| `STD.DateUtil` | `parseByDateStr(str, format, zone)`、`formatTimestampToDateStr(ts, format, zone)`、`formatTimestampToUTCDateStr(ts)`、`currentTimestamp()` | 日期工具（`STD.DateUtils` 同义） |
| `STD.LovHelper` | `queryIdpLov(tenant, lovCode)`（**支持 1 参或 2 参**，JS 层忽略第 1 个参数、第 2 个参数作为 lovCode）、`queryLovAllData(lovCode)`、`getIdpLov(lovCode, value, ignoreEnabledOrNot=false)`、`getIdpLovMeaning(lovCode, value, ignoreEnabledOrNot=false)` | 值集查询；`querySqlLov` 已废弃 |
| `STD.CurrentContext` | `getUserId/getTenantId/getTenantNum/getOrganizationId/getRoleId/getRoleIds/getTimeZone/getExecutionTenantId/getLanguage` | 当前登录用户上下文（内部走 `@M/v1/context`） |
| `STD.EmployeeHelper` | `getEmployee(userId)` | 员工信息 |
| `STD.QueryBlock` | `selectList(code, param)`、`selectOne(code, param)`（返回首条或 undefined）、`selectPage(code, param, pageRequest)` | 查询块；param 支持对象（自动转 JSON 串） |
| `STD.RelTableHelper` | `queryRelTable(tableCode)`、`import/query/create/update/remove(tableCode, record)`（2 参）或 `(tenantId, tableCode, record)`（3 参）、`page(tableCode, record, pageRequest)`、`fastQuery(tableCode, record)` | 虚拟表操作（tenantId 省略时 = -1 即当前租户）；**不再维护** |
| `STD.Logger` | `debug/info/error/warn(msg, ...args)` | 日志（msg 支持表达式+参数） |
| `STD.ElMath` | `eval(exp, ...args)` | 高精度数学 |
| `STD.FeignClient` | `selectClient(serverId)` → `{doPost(path, body), doPut, doGet(path), doDelete(path[, body])}`；`checkFeignResponse(responseBody)` | 服务间调用；body 为对象/数组自动 SAFE_JSON.stringify；服务名白名单（srm-interface/srm-adaptor 等）；响应为 JSON 字符串 |
| `STD.HttpClient` | `doGet(url[, header[, body]])/doPost/doPut/doPatch/doDelete` + `*ForAll` + `*AsBuffer` | HTTP 调用；url 可为字符串（自动包装）或对象；**域名需 OutBound 配置** |
| `STD.PlatformMessage` | `sendMessage(configObj)`、`sendMessageNoReceiverGroup`、`sendMessageInAttachment(configObj, fileInfoList)`、`sendMessageNoReceiverGroupInAttachment` | 消息发送 |
| `STD.Crypt` | `RSA.*`、`AES.encrypt/decrypt`、`AES.CBC.*`、`SRM.idEncrypt/idDecrypt/base62/dataFieldEncrypt/dataFieldDecrypt`、`DataSecurity.encrypt/decrypt`、`SAML.decrypt` | 加解密 |
| `STD.UnilinkHelper` | `decrypt(code, isMobile)`、`encrypt(code, param)` | 链接加解密 |
| `STD.CnfHelper` | `invokeWithParameter(cnfCode, json)` | 配置中心调用 |
| `STD.CodeRuleHelper` | `generateCode(ruleCode, variableMap)`（2 参）或 4 参 | 编码规则（PLATFORM 维度） |
| `STD.Database` | `table(tableName)` → `{insert, batchInsert, deleteByPrimary, deleteByPrimaryBatch, batchDeleteByPrimary, count, updateOptional(record, ...fields), batchUpdateOptional, selectById, selectListById, select, selectOne}` | 直连物理表操作；**updateOptional 无 tx 参数** |
| `STD.LanguageHelper` | `getMessage(code, ...args)`、`getPrompt(code)` | 多语言 |
| `STD.DigestUtils` | `sha256/sha1/md5/sha256Hex/sha1Hex/md5Hex/md5Buffer` | 摘要 |
| `STD.Cache` | `put(key, value[, expire])`、`get(key)`、`remove(key)`、`getIfPresent(key, lambda[, expire])` | 缓存 |
| `STD.CodeBlock` | `execute(cnfCode, input)`（支持跨租户 `租户号:代码块编号`）、`run(cnfCode, input)` | 代码块执行 |
| `STD.Constants` | `get(code)` | 常量 |
| `STD.EventHelper` | `fireEvent(category, event, action, obj)` | 事件 |
| `STD.InterfaceInvokeSdkHelper` | `invoke(namespace, serverCode, interfaceCode, reqBody)` | 接口调用 SDK |
| `STD.System` | `sleep(millis)` | 休眠（引擎限制最大 240000ms） |
| `STD.Assert` | `isTrue(condition, message)` | 断言（抛 SimpleException） |
| `STD.SerialGeneratorUtil` | `randomUUID()`、`serialAZ09(key, maxLength)` | 序列号 |

#### 4.3 `BIZ` 完整 API（摘自 `@M/2021/biz/index.js`）

| API | 签名 | 说明 |
|---|---|---|
| `BIZ.TenantInfoHelper` | `getTenantInfoByNum(tenantNum)` / `getTenantInfoById(tenantId)` | 租户信息 |
| `BIZ.CalendarHelper` | `isOfficialHoliday(countryCode, dateStr)` / `isSettledHoliday` / `findNearOfficialHoliday` / `findNearSettledHoliday` | 日历/节假日 |
| `BIZ.EmployeeHelper` | `getEmployee(userId)` / `getEmployeeByNum(employeeNum)` | 员工信息 |
| `BIZ.UserHelper` | `selectUserInfoById(userId)`（数组传参返回数组，单个返回对象）、`selectUserInfoByLoginName(loginName)`、`selectUserInfoByPhone(phone)`、`selectUserInfoByEmployeeNum(employeeNum)`、`selectUserInfoByEmployeeId(employeeId)`、`selectUserInfoByPurchaseAgentCode(code)`、`selectUserInfoListByRoleCode(roleCode)`、`selectActiveUserList()`、`Supplier.selectByUserPhone/Email/UserId` | 用户信息查询 |
| `BIZ.RoleHelper` | `selectRoleListByCode(code)`、`selectRoleById(id)`、`selectRoleListByUserId(userId)` | 角色查询 |
| `BIZ.ItemInfoHelper` | `selectByItemId(itemId)`、`selectByItemCode(itemCode, sourceCode)`、`itemCategoryByCode(code)`、`itemCategoryById(id)` | 物料/品类 |
| `BIZ.CurrencyHelper` | `number2DocumentStyleRMBJudge(v)`、`number2DocumentStyleRMB(v)`、`selectCurrencyInfoById(id)`、`selectCurrencyInfoByCode(code)` | 币种/金额大写 |
| `BIZ.PrLineHelper` | `selectByPrHeaderId(prHeaderId)` | 采购申请行 |
| `BIZ.UomHelper` | `selectByUomCode(uomCode)` | 计量单位 |
| `BIZ.PriceLibHelper` | `read(list)`、`readAsync(list)`、`write(list)`、`operateAppScope(dto)` | 价格库（返回 JSON 数组） |
| `BIZ.CompanyHelper` | `companyInfoByNum(num)`、`companyInfoById(id)`、`selectBankAccountListByCompanyId(companyId)` | 公司/银行账户 |
| `BIZ.PurchaseAgentHelper` | `purchaseAgentInfoByCode(code)`、`purchaseAgentInfoById(id)` | 采购代理 |
| `BIZ.PrManageHelper` | `releasePr(list)`、`changeQuantity(list)` | PR 释放/数量变更（返回含 failed 的响应） |
| `BIZ.SettleChargeHelper` | `Line.selectBySettleId(settleId)` | 结算费用 |
| `BIZ.CountryHelper` | `selectByCountryId(id)` | 国家 |
| `BIZ.RegionHelper` | `selectByRegionId(id)` | 地区 |
| `BIZ.IndustryHelper` | `selectByIndustryId(id)`、`selectByIndustryCode(code)` | 行业 |

#### 4.4 `@M/v1/*` 组件（需 `require('@M/v1/xxx')`，通过 MarmotBridge 桥接 Java 插件）

常用组件：`object`（对象操作器）、`exception`（SimpleException/BusinessException）、`context`（basic() 获取登录用户）、`query-block`、`code-block`、`safe-json`、`srm-crypt`、`language`、`cache`、`logger`、`user`、`attachment`、`messenger`、`hub`、`xlsx-support`、`sftp`、`system`（sleep）、`business-rule`、`feign-client`、`http`、`math`、`mysql`、`crypt`、`serial-generator`、`queue`、`email`、`workflow`、`object-global` 等（完整清单见 `_engine_root_/node_modules/@M/v1/`）。

**`@M/v1/object` 对象操作器 API**（核心，检查脚本必查）：

| 方法 | 参数 | 返回 |
|---|---|---|
| `object.query({object, condition, tx=true, usingRead=false})` | object=表编码，condition=条件对象 | 数组 |
| `object.queryOne({object, condition, exceptionOnNotFound=false, tx})` | 同 query | 首条或 undefined |
| `object.fetchById({object, id, tx})` | id 可为单个或数组 | 对象（传数组返回数组） |
| `object.create({object, records 或 record, tx})` | record 单条/数组 | 新建记录（含自增 ID） |
| `object.update({object, records 或 record, tx})` | 必须是从 query 查出的（指纹校验） | 更新结果 |
| `object.updateOptional({object, records 或 record, fields, tx})` | fields=需更新字段（单值或数组） | 更新结果 |
| `object.remove({object, id, tx})` | id 单个或数组 | 删除结果 |
| `object.page({object, condition, pageRequest={size:10,page:0}, tx})` | | 分页对象（content 字段） |
| `object.count({object, condition, tx})` | | 数量 |
| `object.QL(ql)` | SQL 语法（仅单表 select * + 条件） | 查询结果 |
| `object.tableInfo(tableName)` | | 表信息 |

注意：`query`/`update`/`updateOptional` 内部 `_tl` 属性支持多语言（`record._tl({mapping, lang, condition})`）。

#### 4.5 其他全局

- 数组增强：`distinct()`、`groupingBy(keyFunc, valueFunc)`、`toMap(keyFunc, valueFunc, mergeFunc)`（在 `script-plugin-mamort-component-initial.js` 中定义）
- JSON：默认 `JSON`（大整数精度问题）→ 建议用 `SAFE_JSON` 或 `JSONbig`
- `MarmotBridge.get('xxx')`：JS 侧获取 Java 插件代理，异常自动包装（打 `in_bridge_exception` 标记）

### 5. 资源限制（`ScriptResourceLevelEnum`）

| 级别 | 触发条件 | 内存 | CPU | 总耗时 |
|---|---|---|---|---|
| LOW | `lowResource=true` | 1G | 12s | 65s |
| MEDIUM（默认） | 默认 | 配置默认值（`MarmotConfigCenter.TOTAL_HEAP_MEMORY_ALLOCATION`） | 25s | 340s |
| HIGH | `highResource=true` | 高内存配置 | 25s | 340s |

- `sleep` 最大 240000ms
- 并发由 `ServerConcurrencyCtrl` 信号量控制；排队由 `MarmotScriptRuntimeQueueing` 控制；`ExecutionDataHub` 跨线程执行（330s 超时）

### 6. 异常处理机制（检查脚本时判断报错形态的依据）

```
EngineRuntimeException（脚本执行异常）
├─ tryFetchCheckedExceptionResponse：识别异常中的标记字段
│   ├─ _marmot_script_business_exception_flag → BusinessException（含 code → 多语言翻译 message）
│   └─ _marmot_script_simple_exception_flag → SimpleException（message 直接返回）
└─ 其他异常 → defaultFullExceptionResponse
    ├─ 返回 jsStack（JS 堆栈）+ message
    └─ 非调试环境由 MarmotScriptRuntimeErrorHook.send 上报
```

**含义**：
- 脚本用 `throw new SimpleException('error.code')` → 会作为"业务失败"返回（前端可显示多语言 message）
- 未捕获的 JS 异常（如 `Cannot read properties of null`）→ 返回完整堆栈并上报监控

### 7. 脚本部署与存储表（检查"配置是否存在"时查这些表）

| 类型 | 存储表 | 关键字段 | 说明 |
|---|---|---|---|
| 脚本模板 | `sada_script_template` | `id/code/description/content/star/contributor/tenant_id/type` | SCRIPT_LIB 等模板 |
| 查询块 | `sada_adaptor_query_block` | 查询块定义（code + SQL/脚本） | `STD.QueryBlock` 使用；不存在时报 `MarmotScript QueryBlock not found` |
| 虚拟表（Rel-Table） | `spfm_rel_table_definition` + `spfm_rel_table_record_<租户>` | `table_code/mapping_json/record_json 或 value1..75 / longvalue0..50` | 脚本中引用的"表"可能在此定义；具体字段与槽位的映射见 `mapping_json` |
| 脚本部署 | `hmde_script` | `script_code/script_status/enabled_flag` | 埋点脚本部署记录 |
| 值集 | `hpfm_lov_value` | `lov_code/value/meaning/enabled_flag` | Lov 值 |
| 适配器挂载（埋点编码） | 虚拟表 `adaptor_static_code`（定义在 `spfm_rel_table_definition`，记录在 `spfm_rel_table_record_<租户>`，table_code=`adaptor_static_code`） | `value1`=`service`（所属服务）/`value2`=`taskCode`（挂载点编码，唯一）/`longvalue3`=`description`（描述）/`longvalue4`=`script`（示例脚本）/`value5`=`enableTenantLevel`（租户级可用） | ADAPTOR 类型脚本（SITF_*/SSRC_* 等）必须在此确认 service 与 taskCode |
| 适配器任务 | `sada_adaptor_task_header` | `task_code`（任务编码，与 apply_tenant_num 唯一）/`input_entity_code`（输入结构）/`apply_tenant_num`（应用于租户）/`running_service`（运行服务）/`script_version`/`enabled_flag`（1 启用 0 不启用）/`trustful` | ADAPTOR 脚本挂载的任务配置，校验输入结构与启停状态 |
| 功能 API 挂载 | 虚拟表 `marmot_api_rewrite`（定义在 `spfm_rel_table_definition`，记录在 `spfm_rel_table_record_<租户>`，table_code=`marmot_api_rewrite`） | `value1`=`tenantNum`（租户，唯一）/`value2`=`apiCode`（功能 API 编码，唯一）/`longvalue1`=`description`（描述）/`value3`=`scriptCode`（后置关联脚本）/`value5`=`beforeScriptCode`（前置关联脚本）/`value4`=`enable`（是否启用）/`longvalue2`=`serverName`（服务）/`longvalue3`=`beanName`/`longvalue4`=`methodName` | SCRIPT_LIB 独立脚本被挂载到功能 API 时在此配置；命中即需扫描代码仓库判断出入参数合理性 |
| **独立脚本内容载体** | 虚拟表 `marmot_script_library`（定义在 `spfm_rel_table_definition`，记录在 `spfm_rel_table_record_<租户>`，table_code=`marmot_script_library`） | `tenantNum`/`code`/`content`/`permission`/`resourceLevel`（参考 `org.srm.container.infra.vo.IndependentScript`）+ **「分类」字段** | SCRIPT_LIB 脚本的代码本体存这里；与 5 个触发表是「内容 vs 触发」关系，必须先确认脚本部署。**定位脚本时 `code` 必须与「分类」同时作为条件**，否则同名 code 可能跨分类误命中 |
| 功能 API 发布 | 虚拟表 `marmot_api_publish`（同上，table_code=`marmot_api_publish`） | `value1`=`code`（API 唯一编码，唯一）/`value2`=`tenantNum`/`value3`=`scriptCode`（关联脚本） | SCRIPT_LIB 独立脚本作为独立 API 发布时在此配置；自动生成 URL，body 必须 string 或 buffer |
| **功能数据导入** | 虚拟表 `marmot_data_import`（同上） | `value1`=`templateCode`/`value2`=`tenantNum`/`value3`=`scriptCode` + 长字段=`验证方式/导入方式/sheetIndex` | SCRIPT_LIB 脚本被用于数据导入的 4 种校验（新增逐条/批量、替换逐条/批量）或批量导入；`input.info` 含 `templateCode/tenantNum/sheetIndex` |
| **调度任务** | 虚拟表 `marmot_scheduler`（同上） | `value1`=`cron`/`value2`=`tenantNum`/`value3`=`scriptCode` + 长字段=入参 | SCRIPT_LIB 脚本作为定时任务；`input` 含 timeStamp 等系统参数 |
| **Topic 消费** | 虚拟表 `marmot_queue_consumer`（同上） | `value1`=`topic`/`value2`=`tenantNum`/`value3`=`scriptCode` | SCRIPT_LIB 脚本消费 MQ 消息；必须做幂等 |
| **RTF 填充** | 虚拟表 `marmot_template_management`（同上） | `value1`=`templateCode`/`value3`=`scriptCode` | SCRIPT_LIB 脚本为 RTF 模板填充数据（MarmotHub RTF） |
| **工作流服务定义** | 物理表 `hwfp_service_definition`（`srm` 库；与 RelTable 不同） | `service_code`（工作流服务编码，唯一）/ `service_mode`（REMOTE/EXPRESSION/LOV_VIEW/**SCRIPT**/APPROVAL_GROUP/EXPRESSION_ENGINE）/ `service_type`（值集 HWFP.SERVICE_TYPE）/ `service_category`（APPROVAL_CANDIDATE_RULE/APPROVAL_STRATEGY/SEQUENCE_CONDITION/END_LISTENER 等）/ `script_code`（裸脚本编码，对应 `marmot_script_library.code`，不带 `SRM-AUX\|SCRIPT_LIB\|` 前缀）/ `service_tenant_id`（服务定义所属租户，0 表示平台共享）/ `enabled_flag` | SCRIPT_LIB 脚本作工作流服务时的定义表（与 `hwfp_process_service` 配合使用） |
| **工作流节点服务绑定** | 物理表 `hwfp_process_service`（`srm` 库） | `process_key`（流程定义编码）/ `process_version`/`service_category`/`service_mode`/`service_id`（= `hwfp_service_definition.id`）/ `service_type`/`service_code`（= `hwfp_service_definition.service_code`）/ `service_tenant_id`/`service_param`/`form_code`/`use_data_type`/`use_data`/`node_id`/`node_type`/`node_name` | 工作流中每个节点引用的服务记录（流程图 BPMN 引用 `service_code` 即可） |

> **SCRIPT_LIB 脚本「多触发表 + 工作流」总览**：1 份脚本可同时被 N 个触发表挂载（独立脚本库 → 5 个触发形态 + 1 个工作流 serviceMode=SCRIPT）。校验时必须 ★1→★6 穷举，禁止只查 `marmot_api_rewrite`。完整字段映射见 `spfm_rel_table_definition.mapping_json` + 源码 `IndependentScript.java` + `ActivitiConstants.SERVICE_MODE_*`。

---

## 第二部分：JS 检查规范（SOP）

### 1. 检查前置准备

1. 明确脚本文件路径、类型（文件名含 `ADAPTOR|SCRIPT_LIB|QUERY_BLOCK` 标识）
2. 明确所属租户（tenant_id / tenant_num，脚本目录通常按客户/变更单组织）
3. 准备 MySQL 连接（mysql-db-mcp），必要时查询 SLS 日志/调用链
4. 若涉及特定业务对象，准备查询块定义、Lov、虚拟表配置数据
5. **环境与库名/分表名取值（强制，所有检查必先做）**：按「第一部分 0」规则取值——
   - **物理表 schema**：`SchemaUtil.loadSchemaFromTableName` 四层顺序匹配（★1 spfm 前缀 → ★2 `global_cross_schema_rule` 平台配置表 → ★3 dual → ★4 默认 `srm`）；脚本引擎自动 SELECT 改写，UPDATE/INSERT/DELETE 不会自动跨库
   - **配置表分表**：`<tenantNum>` = 脚本文件名 split[0] 或 `STD.CurrentContext.getTenantNum()`，物理分表名 = `spfm_rel_table_record_<tenantNum.toLowerCase()>`
   - **不确定时**：先查共享库 `spfm_rel_table_record_srm` 命中后反推 `tenantNum`，再切到对应分表复验
   - 禁止跳此步直接拼 SQL
6. **QueryBlock/CodeBlock 编码校验顺序（强制）**：脚本中涉及 `STD.QueryBlock` / `STD.CodeBlock` 引用的编码时，**优先**在当前工作区文件中查找——本地文件名命名规则为「租户编码|脚本类型|脚本编码」（如 `SRM-AUX|QUERY_BLOCK|SCUX_AUX_QUERY_RFX_BENCHMARK_LINE.xml`、`SRM-AUX|SCRIPT_LIB|SCUX_AUX_RFX_BENCHMARK_LINE_EXPORT.js`），能匹配到即视为该编码存在且合法；**仅当本地文件找不到时**，才用 mysql-db-mcp 查数据库存储值（`sada_script_template` 等表，按 code 精确匹配）。不得在本地文件已存在对应文件时仍判定"未部署"。
7. **ADAPTOR 类型脚本配置校验（强制）**：脚本文件名含 `|ADAPTOR|` 标识（如 `SRM-AUX|ADAPTOR|SITF_SOURCE_RESULT_EXP_INVOKE.js`、`SRM-JALA|ADAPTOR|SITF_PO_EXP_INVOKE.js`）时，**必须先用 mysql-db-mcp 查询配置表（虚拟表）`adaptor_static_code`**。字段映射（来自 `spfm_rel_table_definition.mapping_json`）：`value1`=`service`（所属服务）、`value2`=`taskCode`（挂载点编码，唯一）、`longvalue3`=`description`（描述）、`longvalue4`=`script`（示例脚本）、`value5`=`enableTenantLevel`（租户级可用）。校验 SQL：
   ```sql
   SELECT value1 AS service, value2 AS taskCode, longvalue3 AS description, longvalue4 AS script, value5 AS enableTenantLevel
   FROM spfm_rel_table_record_<tenantNum>
   WHERE table_code = 'adaptor_static_code' AND value2 = '<taskCode>';   -- taskCode 即文件名第三段，如 SITF_SOURCE_RESULT_EXP_INVOKE
   ```
   按序校验：
   - **① 确认服务**：核对记录中的 `service`（所属服务）字段，判断该挂载点是否属于脚本实际使用的服务（SITF_* 接口类 / SSRC_* 寻源类等）；同时可查 `sada_adaptor_task_header`（`task_code`/`running_service`/`input_entity_code`/`enabled_flag`/`apply_tenant_num`）确认任务启停状态与输入结构；
   - **② 按服务检索代码**：用确认的 `service` + `taskCode` 反查该挂载点的 `script`（示例脚本）与出入参约定；
   - **③ 判断出入参数合规性**：将脚本 `process(input)` 中的入参结构（如 `input.inData.inputParam`）与示例脚本/出参约定比对，确认字段名、层级、类型一致。
   若 `<tenantNum>` 不确定时，先查全局记录表 `spfm_rel_table_record_srm`（table_code=`adaptor_static_code`）确认是否存在该挂载点；未找到记录时判定为 P1「挂载点未配置」，不得仅凭本地文件存在即认为已部署生效。
8. **独立脚本（SCRIPT_LIB，文件名含 `|SCRIPT_LIB|`）多触发形态校验（强制）**：SCRIPT_LIB = Marmot **独立脚本**（Independent Script，与 ADAPTOR 埋点脚本相反）。一份脚本可被 5 个触发表同时挂载，或根本没挂载（白占资源）。脚本文件名按 `|` 分 3 段：`tenantNum|type|code`（`ScriptLoadingRepositoryImpl.loadPlainScript`：`Assert.isTrue(split.length==3)`）。校验顺序：

   **第一步：内容载体确认**——查 `marmot_script_library`（脚本代码本体）：
   ```sql
   SELECT tenantNum, code, content, permission, resourceLevel
   FROM spfm_rel_table_record_<tenantNum>
   WHERE table_code = 'marmot_script_library' AND code = '<脚本编码>';
   ```
   未找到 → P1「独立脚本未部署」（即便命中触发表也不会执行）。

   **第二步：5 个触发表全量穷举**（独立脚本被哪种方式调用就执行哪种校验）：
   ```sql
   -- ★1 API 挂载
   SELECT value2 AS apiCode, value3 AS scriptCode, value5 AS beforeScriptCode, value4 AS enable,
          longvalue2 AS serverName, longvalue3 AS beanName, longvalue4 AS methodName
   FROM spfm_rel_table_record_<tenantNum>
   WHERE table_code='marmot_api_rewrite'
     AND (value2='<脚本编码>' OR value3='<脚本编码>' OR value5='<脚本编码>');

   -- ★2 API 发布
   SELECT value1 AS code, value2 AS tenantNum, value3 AS scriptCode
   FROM spfm_rel_table_record_<tenantNum>
   WHERE table_code='marmot_api_publish' AND value3='<脚本编码>';

   -- ★3 数据导入
   SELECT value1 AS templateCode, value2 AS tenantNum, value3 AS scriptCode
   FROM spfm_rel_table_record_<tenantNum>
   WHERE table_code='marmot_data_import' AND value3='<脚本编码>';

   -- ★4 调度
   SELECT value1 AS cron, value2 AS tenantNum, value3 AS scriptCode
   FROM spfm_rel_table_record_<tenantNum>
   WHERE table_code='marmot_scheduler' AND value3='<脚本编码>';

   -- ★5 Topic 消费
   SELECT value1 AS topic, value2 AS tenantNum, value3 AS scriptCode
   FROM spfm_rel_table_record_<tenantNum>
   WHERE table_code='marmot_queue_consumer' AND value3='<脚本编码>';
   ```
   **★1 命中**：按 `serverName` 扫代码仓库，对照 `beanName.methodName` Controller 的请求体/响应与脚本 `process(input)` 入参出参。
   **★2 命中**：校验返回值 `{body, header, httpStatus}`，body 必须 string/buffer、httpStatus ∈ [200, 500]。
   **★3 命中**：校验 `input.data/info/args`（批量数组 vs 单条对象），4 种验证方式（新增逐条/批量、替换逐条/批量）。
   **★4 命中**：校验 cron 表达式合理性；并**按下列调度契约逐项核对**（调度脚本与 API 发布脚本形状完全不同，照抄 API 模板即错）：

  | 检查项 | 正确契约 | 错误写法 |
  |---|---|---|
  | 入参 | `input` = 调度参数 `Map<String,String>`（jobParam 序列化为 `{"marmotScriptLibraryCode":"<脚本编码>"}`），签名 `function process(input)` | 照抄 `function process({ method, parameter = {}, header = {}, body = "" })` |
  | 返回值 | `MarmotSchedulerTaskRunner` **丢弃返回值**、恒返回 `ReturnT.SUCCESS` → 返回值只供用例测试/人工核对 | 以为 `return false` / `return {result:false}` 能标记任务失败 |
  | 失败标记 | **必须 `throw`** 才走任务失败处理策略（重试/忽略） | 静默 return |
  | 执行上下文 | `UserDetailRestoreUtils.executeWithAnonymous(tenantNum, ...)` → **匿名用户，无登录人**；取租户用 `STD.CurrentContext.getExecutionTenantId()`（"require 优先"的合理例外） | 用 `@M/v1/context` 的 `loginUser.executionTenantId` 取租户 |
  | 事务 | 执行器带 `@Transactional(rollbackFor = Throwable.class)`，脚本抛异常回滚本次全部更新 | 抛异常前未确认该批操作幂等 / 可安全重试 |
  | 日期时区 | 调度常在凌晨跑，`new Date().toISOString()` 仍是 UTC **前一天**（业务日期整体偏移）→ 用全局 `moment().utcOffset(8).format("YYYY-MM-DD")`（主 d.ts 第 585 行已注入 `moment`；**未收录 `moment-timezone`**，不要用它也不要为它新建 d.ts） | 直接用 UTC / 用 `moment-timezone` |
  | 分页批处理 | `objectOperation.page` **首页是 `page: 0`**；**先只读分页收集成数组**（数据不变，页码递增安全），再按批 `updateOptional({records, fields})` 提交；整批失败可降级逐条 | 边查边改 + `page++`——已处理记录退出查询条件，后续页 offset 前移 → **批量漏数据**；或为拿记录再 `fetchById` 一遍（多查一次 DB） |

  > 权威依据：本地适配器源码 `/Users/kaitong/project/zhenyun/srm-adaptor`——`org/srm/marmot/infra/job/MarmotSchedulerTaskRunner.java`、`org/srm/marmot/service/impl/MarmotSchedulerServiceImpl.java`。对照其他触发方式的入参：API 发布传 `marmotApiRequestDto`（method/parameter/requestURI，`MarmotTenantApiServiceImpl`）；Topic 消费传消息体反序列化的 `Map<String,Object>`（`MarmotConsumerListener`）。
   **★5 命中**：校验幂等防护（MQ 重复消费）。

   **5 张触发表全未命中 → P1「独立脚本未配置任何触发方式」**（脚本部署但永不执行）。
   **多触发表同时命中 → 报告里枚举每张触发表命中条目**，禁止只列第一张。
9. **独立脚本作为工作流服务调用的校验（强制，★6）**：业务对象 `hwfp_process_service`（流程定义使用服务定义记录表；详见 `srm-resources/init-db/srm/groovy/hzero_workflow/hwfp_process_service.groovy`）。当 SCRIPT_LIB 脚本被 `serviceMode=SCRIPT` 形式挂到工作流时，必须按以下走查链校验，且按 `serviceCategory` 校验脚本返回值契约。

   **完整走查链**（脚本文件名 → 工作流服务编码，serviceCode 是**裸编码**，不带 `SRM-AUX|SCRIPT_LIB|` 前缀）：
   ```
   SRM-AUX|SCRIPT_LIB|SCUX_AUX_PR_APPROVE.js   ← 脚本文件名
     ↓ code
   marmot_script_library.code = "SCUX_AUX_PR_APPROVE"   ← 脚本本体表
     ↓ scriptCode（裸编码）
   hwfp_service_definition.scriptCode = "SCUX_AUX_PR_APPROVE"
   hwfp_service_definition.serviceCode = "SCUX_AUX_PR_APPROVE_CANDIDATE"   ← 工作流服务编码（可与 scriptCode 不同名）
     ↓ serviceCode
   hwfp_process_service.serviceCode = "SCUX_AUX_PR_APPROVE_CANDIDATE"
   ```
   关键发现：
   - **`serviceCode` 不携带脚本类型/租户编码**——错带 `SRM-AUX|SCRIPT_LIB|` 前缀或 `SRM-AUX-` 横线租户号 → 工作流报 `ERROR_SERVICE_NOT_FOUND`（`hwfp.error.service.not_found`）
   - **0 租户共享服务**：`hwfp_service_definition.tenant_id=0` 可被各租户 `hwfp_process_service` 引用（`service_tenant_id=0`）；但**脚本执行时** `MarmotScriptServiceImpl` 取的是当前流程租户的 `tenantNum`（`ServiceHelper.java:278` `Tenant tenant = TenantInfoHelper.selectByTenantId(tenantId)`），不是 `service_tenant_id`——所以脚本本体必须在引用方租户的 `marmot_script_library` 中存在

   **校验 SQL**（注意：工作流表是**物理表**不是 RelTable，按 tenant_id 隔离）：
   ```sql
   -- ① 查服务定义（看 scriptCode + serviceMode + 启停）
   SELECT service_code, service_mode, service_type, service_category, script_code, service_tenant_id, enabled_flag
   FROM hwfp_service_definition
   WHERE service_code = '<脚本编码>' AND tenant_id IN (<当前租户>, 0);

   -- ② 查流程绑定（看哪些 processKey + nodeId 引用了该服务）
   SELECT process_key, process_version, service_category, service_mode, node_id, node_type, node_name
   FROM hwfp_process_service
   WHERE service_code = '<脚本编码>' AND tenant_id = <当前租户>;

   -- ③ 确认脚本本体已部署（前置规则 0 取 tenantNum）
   SELECT code, content, permission, resourceLevel
   FROM spfm_rel_table_record_<tenantNum>
   WHERE table_code='marmot_script_library' AND code='<scriptCode>';
   ```

   **★6 命中后按 serviceCategory 校验脚本返回值契约**（**所有命中脚本必查**）：
   - **调用入口**：`MarmotScriptServiceImpl.getMarmotScriptResult`（事务 `Propagation.REQUIRES_NEW`）→ `MarmotScriptLibraryHelper.independentScriptExecute(scriptCode, tenantNum, inputObj)` → 取 `result` 字段作为执行结果
   - **异常处理**：`BusinessException` 转 `CommonException`；`ScriptContainerExecutionException` 转 `hwfp.error.service.marmot.execution_exception`（含 serviceCode + 错误 + scriptCode）；`MarmotScriptLibraryNotExistException` 转 "Marmot Script library find failed"
   - **入参**：`process(input)` 收到 `args`（= 流程当前所有变量）+ `args.requestConstants`（= serviceDefinition.parameterList 转换的固定参数 Map，JSON 字符串）

   | serviceCategory | 用途 | **脚本返回值契约** | 实现位置 |
   |---|---|---|---|
   | `APPROVAL_CANDIDATE_RULE`（`ActivitiConstants.APPROVAL_CANDIDATE`="APPROVAL_CANDIDATE_RULE"） | **审批规则**：决定审批人 | **返回员工编码数组**——支持 JSON 数组 `["u1","u2"]`、逗号分隔字符串 `"u1,u2"`、单值 `result="u1"`（三态兼容） | `ServiceHelper.asCollection`（ServiceHelper.java:634-654） |
   | `SEQUENCE_CONDITION` | **跳转条件**（sequenceFlow 条件） | **必须返回 boolean**——脚本 `result` 必须是 `"true"/"false"` 或 `true/false`；不返 boolean 报错 `DATA_INVALID` | `ServiceHelper.getExpression(..., Boolean.class, "SEQUENCE_CONDITION")` + `TYPE_METHOD.put(Boolean.class, ".asBoolean()")`（ServiceHelper.java:82-89, 196-201, 206-208） |
   | `APPROVAL_STRATEGY` | 审批方式 | `expression` 或常量字符串 | `ApproveChainUserTaskHandler.approveMethodFormConstructor` |
   | 结束监听器（`END_LISTENER`） | 流程结束 | 返回值经 `formatScriptDataType` 刷入 `act_hi_varinst`（按 processInstanceId + variableType 自动转 Double/Boolean/Long/String） | `ServiceHelper.formatScriptDataType`（ServiceHelper.java:353-400） |
   | **服务任务通用** | 任意节点 | **执行结果无效特殊返回**：① `args.NOT_EXECUTE_LISTENER="Y"` → `ServiceExecuteResult.NULL` 直接返回不执行（ServiceHelper.java:218-220）；② default 分支 → NULL（ServiceHelper.java:344-346）；③ 脚本抛异常 → 抛通用异常而非流程中断 | `MarmotScriptServiceImpl.getMarmotScriptResult` + `ServiceHelper.getResult` |

### 2. 检查步骤（严格按序执行）

#### 阶段一：语法与结构检查
- [ ] 用 Node 语法检查（`node --check`）确认无语法错误
- [ ] 确认存在 `process(input)` 入口函数
- [ ] 确认 `input` 的解析在 try 块内或做了空值兜底（GET 请求 body 可能为空串）
- [ ] 检查未声明变量（隐式全局）、缺分号、死代码
- [ ] **TS 类型检查（受检目录必做）**：脚本位于 `脚本服务/`（对应 `jsconfig.json` 开了 `checkJs: true`）时必须 `read_lints` 到 0 错误。判定与对策：
  - **环境问题 vs 脚本问题分流**：`@M/v1/*` 报 TS2307、`STD`/`BIZ`/`_` 报 TS2304 = jsconfig `include` 未引主 d.ts（`改造案例/代码服务/srm-script-api.d.ts`，纯 ambient，纳入即全局生效），属**环境缺失**不是脚本错；`改造案例/` 下无 jsconfig、`checkJs` 默认 false，**不能拿那里"不爆红"当类型正确的依据**（报错被掩盖，纳入 checkJs 项目会全部暴露）
  - **`@M/v1/object` 返回 `unknown`**：`query` → `unknown[]`，`fetchById`/`update`/`create` → `unknown`，访问字段 TS2339。最省事是在**引入处**统一包装：`objectOperation = /** @type {any} */ (require("@M/v1/object"))`（代价：放弃入参提示）；想保留入参校验就回调用点逐个 `/** @type {any} */`（约多 10 行）
  - **动态建对象**：`["debug","info","warn","error"].reduce((o,k)=>(o[k]=fn,o),{})` 推断不出动态属性（TS2339）→ 改**字面量对象**（多 4 行但类型正确）；`Object.fromEntries(...map(...))` 同样不行（`map` 返回 `(string|Function)[][]`，不匹配元组类型）
  - **形参默认值收窄**：`function process({ parameter = {} })` 会把 `parameter` 收窄成 `{}`，`parameter.page` TS2339 → `const { page, size } = /** @type {any} */ (parameter);` 承接
  - 本机无 node/npx/tsc，`tsc --noEmit` 不可用；`read_lints` 只覆盖已打开文件，不等于全量通过

#### 阶段二：全局对象与 API 签名校验（对照第一部分 API 表）
- [ ] 每个 `STD.xxx` / `BIZ.xxx` / `OTHER.xxx` 调用对照签名核对参数个数与类型
- [ ] 每个 `require('@M/v1/xxx')` 确认组件存在且方法签名正确
- [ ] `STD.FeignClient.selectClient(serverId)`：确认 serverId 在白名单（srm-interface/srm-adaptor 等）；doPost 的 body 为对象/数组时自动 stringify，无需手动处理
- [ ] `STD.QueryBlock.selectOne/selectList/selectPage`：param 直接传对象即可
- [ ] `object.query/queryOne/update/updateOptional`：确认参数是对象形式 `{object, condition, ...}` 而非位置参数
- [ ] JSON 处理：涉及大整数/金额字段必须用 `SAFE_JSON` 或 `JSONbig`，避免默认 JSON 精度丢失

#### 阶段三：数据表与字段校验（mysql-db-mcp）
- [ ] 脚本引用的**每张表**用 `describe_table` 校验存在性
- [ ] 若物理表不存在 → 查 `spfm_rel_table_definition`（table_code）确认是否为虚拟表；仅当物理表和配置表都不存在才判定"表不存在"
- [ ] **例外：元数据有、物理表 1146**：`spfm_rel_table_definition` 里有定义，但 `SHOW CREATE TABLE` 在 archery 覆盖的 SaaS `srm` 库查不到（1146 不存在）时，**不要断言「表未建」**——先确认该租户配置表的物理存储是否落在别的实例/库
- [ ] 脚本引用的**每个字段**核对：拼写、大小写、类型、精度（decimal 位数）——尤其金额/比率字段
- [ ] 虚拟表字段用 `mapping_json` 的 `name`（业务名）核对（如 `longvalue10.name="templateNum"` → 脚本写 `record.templateNum`）；脚本里直写 `longvalueN`/`valueN` 记规范问题
- [ ] 特殊规则：`attribute_decimal10/11/12` 等扩展字段必须逐一确认物理表确实存在该字段
- [ ] **前置规则 0**：所有 `spfm_rel_table_record_<...>` 查询的 `<tenantNum>` 已按第一部分 0 取准（编码小写，非 `tenant_id`），禁止边查边猜

#### 阶段四：数据配置校验
- [ ] Lov 值：`hpfm_lov_value` 查脚本硬编码的 value 是否存在且 enabled（如状态 `INSTANCE/REFUSE`）
- [ ] 虚拟表数据：`spfm_rel_table_record_<tenantNum>`（按前置规则 0 取到的分表名）查脚本查询条件的实际数据是否存在（如 `reviewType=17`）
- [ ] 查询块：`STD.QueryBlock` 引用的编码（如 `selectOne("SCUX_AUX_QUERY_RFX_BENCHMARK_LINE", param)`）先按「租户编码|QUERY_BLOCK|脚本编码」在当前工作区文件查找对应 `.xml`；本地无匹配再查数据库存储值（如 `sada_script_template` 的 `code` 字段 / 查询块定义表）
- [ ] 代码块：`STD.CodeBlock.execute("编码", input)` 的 cnfCode 先按「租户编码|SCRIPT_LIB|脚本编码」在当前工作区文件查找对应 `.js`；本地无匹配再查数据库存储值（如 `sada_script_template` 的 `code` 字段）；注意支持跨租户 `租户号:代码块编号` 格式
- [ ] OutBound：`STD.HttpClient` 访问的域名是否已配置白名单
- [ ] ADAPTOR 挂载点：脚本文件名含 `|ADAPTOR|` 时，查询虚拟表 `adaptor_static_code`（`spfm_rel_table_record_<tenantNum>` WHERE `table_code='adaptor_static_code' AND value2='<taskCode>'`，字段映射 value1=service/value2=taskCode/longvalue4=script/value5=enableTenantLevel）确认 `service` 与 `taskCode` 存在、`enableTenantLevel` 允许该租户，并比对示例 `script` 校验出入参数（`input.inData.inputParam` 字段名/层级/类型）；辅助查 `sada_adaptor_task_header`（`task_code`+`apply_tenant_num`）确认 `enabled_flag` 启用状态
- [ ] 独立脚本（SCRIPT_LIB）5 个触发表全量穷举：脚本文件名含 `|SCRIPT_LIB|` 时，按 ★1 marmot_api_rewrite / ★2 marmot_api_publish / ★3 marmot_data_import / ★4 marmot_scheduler / ★5 marmot_queue_consumer 逐个查，确认命中后各自的入参出参/启用状态/Cron/幂等等合理性；全未命中则 P1「未配置任何触发方式」
- [ ] **独立脚本被工作流服务调用（★6）**：脚本被 `serviceMode=SCRIPT` 形式挂到工作流时，必须按以下顺序校验：① `hwfp_service_definition` 中 `serviceCode` 存在且 `scriptCode` = 裸脚本编码（不带 `SRM-AUX|SCRIPT_LIB|` 前缀）；② `hwfp_process_service` 中该 `serviceCode` 已被流程节点引用；③ 脚本本体在 `marmot_script_library` 中已部署；④ **按 serviceCategory 校验返回值契约**：APPROVAL_CANDIDATE_RULE→员工编码数组 / SEQUENCE_CONDITION→boolean / END_LISTENER→result 经 `formatScriptDataType` 刷入 `act_hi_varinst`

#### 阶段五：依赖脚本与跨脚本校验
- [ ] 脚本调用其他脚本/查询块/代码块时，确认目标已部署且接口契约一致
- [ ] 若同目录存在 prod-bug/旧版本副本，diff 对比确认修复点与差异

#### 阶段六：业务逻辑正确性
- [ ] 分支条件是否有遗漏（如 GET/POST 分支、空数组、null 对象）
- [ ] 异常路径是否会留下脏数据（先写后抛错）
- [ ] 事务：`update` 带指纹校验（须用 query 结果）、`updateOptional` 用 fields 限定
- [ ] 循环/大数据量：批量操作单批 ≤ 100（object.update 内部已 chunk）；记录数 > 10000 报错
- [ ] 资源：避免死循环、超长 sleep、大数据内存占用

#### 阶段七：输出报告
- [ ] 按严重级别（见下）汇总问题
- [ ] 每个问题给出：位置（文件:行号）、现象、根因、证据（SQL 结果）、修复建议
- [ ] 区分"脚本代码问题"与"环境/配置缺失问题"
- [ ] **报告落盘**：分析/检查/排障类**必出 MD** 到 `<所在项目>/.codebuddy/memory/AI 输出文档/`，命名 `{主题}_{描述}_分析报告.md` 或 `diagnose-{traceId}-{日期}.md`，结构＝背景 → 证据链 → 根因 → 验证 → 建议；**纯改代码类任务不出报告**，只给「改了什么 + 关键差异（行数/影响面/取舍/可回退）」

#### 阶段八：编码规范核对（v3.3 基线，出 P3/规范项）

不满足下列约定记 P3（按实际影响可升级）。**红线：不得为"更规范/更短"而改变业务逻辑**——校验/状态机/异常分支/回滚/幂等必须等价。

| # | 项 | 约定 | 违规写法 |
|---|---|---|---|
| 1 | 模块引入 | **require 优先**：有 `@M/v1/xxx` 模块必须 `require`；仅确认无对应模块才用全局。必须 require：`exception`/`context`/`logger2`/`object`/`math`/`query-block`/`code-block`/`business-rule`/`language`/`constants`/`user`/`srm-crypt`/`serial-generator`/`cache`/`queue`/`system`/`console`/`workflow`/`json-bigint`。无 require 只能用全局：`STD.BusinessAssert`/`STD.LovHelper`/`STD.HttpClient`/`BIZ.PrManageHelper`/`BIZ.RoleHelper`/`BIZ.CompanyHelper`/`JWT_TOOL`（`STD.ElMath`→`@M/v1/math`；`BIZ.PriceLibHelper` 已不存在） | 有 `@M/v1/math` 却用 `STD.ElMath` |
| 2 | 头部极简 | 业务脚本只 `require` **实际用到**的能力，不整块拷模板头部；重复片段抽常量/小函数（`pick(r)`、`OBJECT` 常量、`fetchByIds`） | 未使用的 `math`/`language`/`momentTz`/`companyHelper` 整段保留 |
| 3 | 租户 ID | `loginUser.executionTenantId`（`@M/v1/context` 的 basic 取 loginUser）；**匿名/调度场景例外**用 `STD.CurrentContext` | 调度脚本里用 loginUser 取租户 |
| 4 | 日志 | `require("@M/v1/logger2")` + 变参 `logger.info("msg {}", x)`（logger2 两种重载都支持） | 旧 `@M/v1/logger` 的对象形式 `logger.info({ msg, strs })` |
| 5 | 入口解构 | `let requestBody = JSONBig.parse(body \|\| "{}")`；后置脚本签名 `process({ body, parameter, method, header = {}, requestURI, responseBody })` | 直接 `JSON.parse`（大整数/金额精度丢失） |
| 6 | 乐观锁 | **业务层不自校验** `objectVersionNumber`；只把前端版本号写回：`existing.objectVersionNumber = requestBody.objectVersionNumber` → `objectOperation.update({object, record: existing})`，冲突由框架抛 `ObjectOptimisticLockException` | `Assert.isTrue(a===b, "数据已被他人修改，请刷新")` 自校验；或忘了把版本号写回导致 update 必失败 |
| 7 | update 选型 | 需并发保护 → `update`（record 含 `objectVersionNumber`，须来自 query 结果）；只改指定字段 → `updateOptional({records, fields})` | 用 `updateOptional` 却期望乐观锁；`update` 传手工拼的对象（指纹校验失败） |
| 8 | 配置表字段 | 写 `mapping_json` 里的**业务 `name`**（`templateNum`/`userId`/`businessCode`/`businessType`…） | 直写物理列 `longvalueN`/`valueN` |
| 9 | 头部结构 | v3.3 三段式：`/* 标准模块（require）*/` → `/* 无 require 模块只能用 STD/BIZ 全局 */` → `/* 二次封装（Logger / languageHelper / SRMId / prManageHelper / httpHelper）*/` | 每脚本自造头部；`prManageHelper` 不用 `*AndCheck` 而手写响应校验 |
| 10 | 日志 TS 兼容 | `Logger` 若用 reduce 动态生成，在 `checkJs` 目录下需给初始值标注：`/** @type {Record<string, (msg:any, ...args:any[]) => void>} */({})`，或直接改字面量对象 | 照抄 reduce 写法后在受检目录报 TS2339 |

> 存量脚本（`脚本服务/codeBlock.js` 是通用头部模板，243+ 处在用 `STD.ElMath`/`BIZ.LovHelper`/`BIZ.PriceLibHelper` 等历史 API）**不要批量改写、也不要逐个 `@ts-ignore`**；只对新脚本/本次改动过的脚本按 v3.3 要求。

### 3. 严重级别定义

| 级别 | 定义 | 判定标准 |
|---|---|---|
| **P0** | 功能必然失败（上线阻塞） | 语法错误；必现空指针；引用的表/字段不存在；关键配置缺失导致必现报错 |
| **P1** | 部分功能不可用 / 特定路径必报错 | 分支缺失（如 GET 未传 body）；条件用错（如 reviewType=17 查不到数据）；查询块未部署 |
| **P2** | 潜在隐患 | 参数个数与 API 不符（不触发时无害）；未判空导致边界异常；低资源下超时风险 |
| **P3** | 代码规范 | 缩进/分号/未声明变量/死代码/注释缺失 |

### 4. 高频问题速查（历史问题库）

| # | 问题 | 判定方法 | 级别 |
|---|---|---|---|
| 1 | 脚本引用的虚拟表在物理库不存在 | `describe_table` 失败 → 查 `spfm_rel_table_definition` | P0（若配置表也没有） |
| 2 | 硬编码条件查不到配置数据（如 reviewType=17 但配置只有 1-16） | 查 `spfm_rel_table_record_*` + Lov | P1 |
| 3 | Lov 值不存在/已失效（如状态值拼错） | 查 `hpfm_lov_value` | P1 |
| 4 | 查询块/代码块未部署（报 `QueryBlock not found` 等） | 先按「租户编码|QUERY_BLOCK|脚本编码」/「租户编码|SCRIPT_LIB|脚本编码」在工作区文件查找；本地无匹配再查数据库存储值（`sada_script_template.code` 等） | P1 |
| 5 | ADAPTOR 脚本不生效/找不到挂载点（SITF_*/SSRC_*） | 查虚拟表 `adaptor_static_code`（`spfm_rel_table_record_<租户>` WHERE table_code='adaptor_static_code' AND value2='<taskCode>'）：①确认 service ②按服务反查 script 示例 ③比对出入参数合规性；辅助查 `sada_adaptor_task_header` 确认 `enabled_flag` | P1 |
| 5b | 独立脚本（SCRIPT_LIB）未配置任何触发方式（5 张触发表全未命中）— 脚本部署了但永远不会被执行 | 按「SCRIPT_LIB 多触发形态校验」步骤，穷举 ★1→★5 五张触发表（`marmot_api_rewrite` / `marmot_api_publish` / `marmot_data_import` / `marmot_scheduler` / `marmot_queue_consumer`），全未命中即 P1；先确认 `marmot_script_library` 中内容已部署再判定 | P1 |
| 5c | 独立脚本已挂载到 `marmot_api_rewrite` 但 `enable=0` / 入参不匹配 Controller 请求体 | `marmot_api_rewrite.value4=enable`、按 `serverName+beanName+methodName` 扫 Controller，比对 `input.body` / `input.parameter` / `input.responseBody` 字段名与层级 | P1 |
| 5d | 独立脚本被发布为 API（`marmot_api_publish`）但返回值 body 非 string/buffer、httpStatus 越界（不在 200-500） | 强制校验 C★2：返回值必须 `{body, header, httpStatus}`，body 仅 string/buffer，httpStatus ∈ [200, 500] | P1 |
| 5e | 独立脚本被工作流 `serviceMode=SCRIPT` 调用，但 `serviceCode` 拼错（带了 `SRM-AUX\|SCRIPT_LIB\|` 前缀或 `SRM-AUX-` 横线租户号）—— 全工作流报 `ERROR_SERVICE_NOT_FOUND` | 强制校验 C★6 走查链：脚本文件名 → marmot_script_library.code → hwfp_service_definition.scriptCode → hwfp_service_definition.serviceCode → hwfp_process_service.serviceCode；**serviceCode 必须为裸编码** | P1 |
| 5f | 独立脚本作工作流审批规则（serviceCategory=APPROVAL_CANDIDATE_RULE）但返回值非员工编码数组（返回对象/布尔等）—— 审批人拿不到 | 强制校验 C★6 审批规则契约：脚本 `result` 必须是 JSON 数组 `["u1","u2"]` 或逗号分隔 `"u1,u2"` 或单值 `result="u1"`（ServiceHelper.asCollection 兼容三态） | P1 |
| 5g | 独立脚本作工作流跳转条件（serviceCategory=SEQUENCE_CONDITION）但返回值非 boolean—— sequenceFlow 走错分支/卡死 | 强制校验 C★6 跳转条件契约：脚本 `result` 必须是 `"true"/"false"` 或 `true/false`（ServiceHelper.getExpression + TYPE_METHOD 强制 `.asBoolean()`） | P1 |
| 6 | GET 分支 body 为空导致 `body.xxx` 报 TypeError | 检查 `STD.SAFE_JSON.parse(body)` 与 body 使用是否在 try 内/有兜底 | P1 |
| 6 | `queryOne` 返回 undefined 后直接取属性 | `queryOne` 需判空或 `exceptionOnNotFound: true` | P1 |
| 7 | 大整数经默认 JSON 丢失精度 | 检查是否用 `SAFE_JSON`/`JSONbig` | P2 |
| 8 | FeignClient 响应未检查 `failed` 字段 | 应使用 `STD.FeignClient.checkFeignResponse` | P2 |
| 9 | HttpClient 域名未配 OutBound | 检查域名白名单 | P1 |
| 10 | `object.update` 传入非 query 结果（指纹校验失败） | 确认更新记录来自 query 结果 | P1 |
| 11 | 脚本里 SELECT 跨库表名实际走到了非预期 schema（如该走 `srm` 的走了业务自定义库） | 查 `global_cross_schema_rule`（0 租户 `spfm_rel_table_record`）按 `value3=order` 排序看规则列表；规则顺序错（短前缀在前）会让后续表名被错误短路命中 | P1 |
| 12 | 用 `tenant_id`（数字）当分表后缀 → `FROM spfm_rel_table_record_158677` 表不存在/查空 | 分表后缀必须是 `tenantNum`（编码）小写：`spfm_rel_table_record_srm_isimcere`（见 0.4.1） | P1 |
| 13 | Rel-Table 记录查询加了 `tenant_id` 条件 → 查空（记录实际以 `tenant_id=0` + `value1=租户编码` 存储） | 分表已按租户隔离，去掉 `tenant_id`，用分表名 + `table_code`/`valueN` 过滤 | P1 |
| 14 | `marmot_script_library` 定位脚本时只按 `code` 查 → 命中多条/查错脚本 | `code` + **分类** 字段同时作为条件 | P2 |
| 15 | 调度脚本照抄 API 发布模板（含 `method/parameter/header/body`）、以为 `return false` 能标失败 | 校验 ★4 调度契约：入参 `Map<String,String>`、返回值被丢弃、**必须 `throw`**、匿名上下文、`moment().utcOffset(8)`、分页 `page:0` 起始且不可边查边改递增页码 | P1 |
| 16 | 受检目录（`脚本服务/`，`checkJs: true`）下脚本 TS 报错（TS2307/TS2304/TS2339） | 先分流「环境缺 d.ts」vs「脚本真问题」；脚本侧按 object 返回值 `/** @type {any} */` 包装、logger 改字面量、默认形参用 `any` 承接 | P2/P3 |
| 17 | `@M/v1/user.selectUserInfoById` 按旧版单值调用，本应支持批量（或调用了不存在的 `selectById`） | 核对签名**必须看项目生产 hotfix 分支**（如 `1-69-0-hotfix`）：`{userId: 单值\|数组}`，传数组返数组、自动过滤系统用户；模块**无 `selectById`** | P2 |

### 5. 报告模板

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

### 二、命中触发场景（SCRIPT_LIB 类型必出，按 ★1→★6 列出）
| 触发表 | 命中 | 配置详情 | 入参出参一致性 |
|---|---|---|---|
| marmot_api_rewrite（API 挂载） | ✅/❌ | apiCode / enable / serverName.beanName.methodName | 比对 Controller 请求体 |
| marmot_api_publish（API 发布） | ✅/❌ | code / 自动生成 URL / 返回值约定 | 校验 body/header/httpStatus |
| marmot_data_import（数据导入） | ✅/❌ | templateCode / 验证/导入方式 | input.data/info/args 结构 |
| marmot_scheduler（调度） | ✅/❌ | cron / 触发时间 | 校验幂等 |
| marmot_queue_consumer（Topic） | ✅/❌ | topic | 校验重复消费防护 |
| marmot_script_library（内容） | ✅/❌ | 脚本是否部署 | — |
| **hwfp_process_service（工作流服务调用，★6）** | ✅/❌ | serviceCode / serviceCategory / serviceMode | **按 serviceCategory 校验返回值契约**：<br>• APPROVAL_CANDIDATE_RULE → 员工编码数组<br>• SEQUENCE_CONDITION → boolean<br>• END_LISTENER / 审批方式 → result 可空（特殊）<br>• 跨租户：hwfp_service_definition.tenant_id=0 可被各租户引用，但脚本本体仍在引用方租户的 marmot_script_library 中 |

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

---

## 第三部分：检查时的注意事项与易错点

1. **不要轻信 d.ts 简化定义**：`global.d.ts` 是 TS 声明（简化），真实签名的权威来源是 `srm-script-container` 的 `@M/2021/std/index.js`、`@M/2021/biz/index.js`、`@M/v1/*/index.js`。例如 `STD.LovHelper.queryIdpLov` 的 d.ts 看似只接受 1 参，实际 JS 层支持 `(tenant, lovCode)` 2 参。
2. **JS 层与 Java 层参数转换**：JS 对象传参会被 `toSafeJsonIfPossible` 自动序列化为 JSON 字符串，无需手动 stringify（但不要因此误判为"类型不符"）。
3. **虚拟表判断规则**：物理表不存在 ≠ 表不存在，必须先查 `spfm_rel_table_definition`（Rel-Table 虚拟表定义，结构在 `mapping_json`）。
4. **租户维度**：配置数据、Lov、虚拟表记录均按租户隔离（tenant_id / tenant_num），查询时必须带租户条件。
5. **表名/字段名大小写**：MySQL 表名小写、字段命名规范（snake_case）；脚本中驼峰字段在查表时需确认映射（Rel-Table mapping_json 定义了字段映射）。
6. **执行环境差异**：试运行（js-test）、调度任务、埋点触发的上下文（input 结构）不同，检查时需按实际触发场景判断 input 字段。
7. **资源与性能**：检查循环、递归、大数据量操作是否突破资源限制（340s / 25s CPU / 内存）。
8. **库名/分表名混淆**：物理直连库名是固定的 `srm`（不同环境库名前缀不同，按部署环境区分），而 Rel-Table 分表后缀 = `tenantNum.toLowerCase()`；两者职责不同——`STD.Database.table("xxx")` 操作物理业务表，`spfm_rel_table_record_<tenantNum>` 才是虚拟表记录。错把虚拟表当物理表查会查不到数据。
9. **独立脚本多触发遗漏**：1 份 SCRIPT_LIB 脚本可同时被 5 个触发表（API挂载/发布、数据导入、调度、Topic）调用，不能查到 `marmot_api_rewrite` 就停。例如同一份脚本 A 既被 `★2 API发布` 又被 `★4 调度任务` 使用，必须两处都查、各自校验入参出参。全 5 张都未命中才判定为「未配置触发方式」（独立脚本存在但永不执行 = P1）。
10. **多 API 挂载命名约束**：`apiCode`（MARMOT_API_REWRITE 中的 `value2`）必须全局唯一——spring boot 启动时若重复会直接报错 `marmot api code of marmot api rewrite can not repeated`。同一 apiCode 下用 `value1`（tenantNum）区分不同租户。检查 `★1` 时若发现 `marmot_api_rewrite` 出现重复 apiCode 必须标出。
11. **独立脚本内容载体 vs 触发表**：脚本代码本体存在 `marmot_script_library`（`org.srm.container.infra.vo.IndependentScript`：tenantNum/code/content/permission/resourceLevel）；触发配置存在 5 张触发表。两类是「内容 vs 触发」关系——校验时必须先确认 `marmot_script_library` 中内容部署，再核 5 张触发。
12. **`global_cross_schema_rule` 顺序匹配**：平台级配置表（0 租户），脚本引擎内 `SchemaUtil.loadSchemaFromTableName` 按 **★1 spfm 前缀 → ★2 此表规则 → ★3 dual → ★4 默认 srm** 四层顺序匹配。检查脚本里涉及跨库查询时必须先 `SELECT FROM spfm_rel_table_record WHERE table_code='global_cross_schema_rule' ORDER BY ruleOrder` 看实际生效规则。注意：`table_name.startsWith(rule.prefix)` 是前缀匹配——若规则列表里同时有 `prefix='a'` 和 `prefix='abc'`，按列表顺序先命中谁就返回谁，规则顺序不当会导致某些表走了非预期的 schema。规则变更后 30 分钟内 `CacheEnabledRelTable` 仍返回缓存值。
13. **跨库 SELECT 改写 ≠ 跨库写**：MyBatis 拦截器 `ScriptCrossSchemaInterceptor` 仅在 SELECT 上做 schema 改写（实现 `intercept()`：`if(!(statement instanceof Select)) return invocation.proceed()`）；脚本里写 UPDATE/INSERT/DELETE 不会自动跨库，仍按默认 `srm`/当前租户执行——涉及跨租户写入必须显式手动拼接 schemaName 或走 service 层。
14. **业务代码不能用此跨库改写机制**：`ScriptCrossSchemaInterceptor` 类注释明确"有且只有脚本引擎依赖这个东西，别的地方不要用（这个拦截器和 SqlPaser 拦截器是冲突的）"。业务代码（Java Controller / Service）走自己的数据源，不享受此规则——查业务代码相关 SQL 跨库问题不能用 `global_cross_schema_rule` 解释。
15. **工作流 serviceCode 拼错是最常见坑**：独立脚本被工作流调用时，`hwfp_service_definition.serviceCode` 和 `hwfp_process_service.serviceCode` 都必须是**裸编码**（如 `SCUX_AUX_PR_APPROVE_CANDIDATE`），**不能**带 `SRM-AUX|SCRIPT_LIB|` 前缀，也不能带 `SRM-AUX-` 横线租户号。错带任何修饰都会导致工作流报 `ERROR_SERVICE_NOT_FOUND`（`hwfp.error.service.not_found`）——流程完全找不到该服务。
16. **三种 serviceCategory 必查返回值类型**：
    - **审批规则**（`APPROVAL_CANDIDATE_RULE`）→ 脚本 `result` 必须是员工编码数组（JSON 数组/逗号分隔/单值三态）
    - **跳转条件**（`SEQUENCE_CONDITION`）→ 脚本 `result` 必须是 boolean（否则 `.asBoolean()` 转换失败报错 `DATA_INVALID`，sequenceFlow 走错分支）
    - **服务任务/结束监听器** → result 经 `formatScriptDataType` 刷入 `act_hi_varinst`（按 processInstanceId 找 variableType 转换 Double/Boolean/Long/String）；空 result 走 `ServiceExecuteResult.NULL` 特殊路径
    错返类型 → 流程卡死/审批人拿不到/异常静默丢弃。
17. **0 租户共享服务的脚本部署位置**：`hwfp_service_definition.tenant_id=0` 是平台共享服务，可被各租户 `hwfp_process_service` 引用（`service_tenant_id=0`）。但**脚本执行时**（`MarmotScriptServiceImpl.getMarmotScriptResult`）取的是当前流程租户的 `tenantNum`（`ServiceHelper.java:278`），不是 `service_tenant_id`——所以脚本本体必须在引用方租户的 `marmot_script_library` 中存在，不能图省事只部署到 0 租户。
18. **`tenantNum`（编码）≠ `tenant_id`（数字）**：分表后缀只能取编码小写（`SRM-ISIMCERE` → `spfm_rel_table_record_srm_isimcere`），**永不是数字 `158677`**；`tenant_id` 只用于物理表租户过滤。反之，**Rel-Table 记录表不要再加 `tenant_id` 条件**（记录常以 `tenant_id=0` 存储，加了必查空）。详见 0.4.1。
19. **`marmot_script_library` 定位要带「分类」**：独立脚本代码本体表除 `code` 外还有「分类」字段，只按 `code` 查可能跨分类误命中；查脚本前先把分类作为必要条件。
20. **调度脚本是最易照抄错的形态**：与 API 发布完全不同——入参是 `Map<String,String>`（非 method/parameter/header/body）、**返回值被执行器丢弃**（要标记失败必须 `throw`）、执行上下文是**匿名用户**（取租户用 `STD.CurrentContext`，这是"require 优先"的合理例外）、日期须 `moment().utcOffset(8)`（凌晨跑用 UTC 会整体偏移一天）、`objectOperation.page` **首页是 `page: 0`**。见 1.8 ★4 专项表。
21. **分页批处理不能边查边改 + 递增页码**：改了状态字段会让已处理记录退出查询条件，后续页 offset 前移造成**批量漏数据**。正确做法：先**只读**分页收集成数组（数据不变，页码递增安全），再按批 `updateOptional({records, fields})` 提交；不要为拿记录再 `fetchById` 一遍。
22. **TS 报错先分流"环境 vs 脚本"**：`@M/v1/*` TS2307、`STD/BIZ/_` TS2304 是 jsconfig 未引主 d.ts 的**环境缺失**；TS2339 才多是脚本写法。受检目录是 `脚本服务/`（`checkJs:true`），`改造案例/` 下不检查——**不能拿"那里不爆红"当类型正确依据**。见阶段一 TS 检查块。
23. **`@M/v1/*` 签名以生产 hotfix 分支为准**：GitLab `operation-tech-platform/srm-script-container`（project_id=1686）→ `_engine_root_/node_modules/@M/v1/{模块}/index.js` + `domain/supports/v3/plugin/biz/{Helper}.java`，**ref 必须用项目对应生产版本**（如 `1-69-0-hotfix`）。反例：`selectUserInfoById` 在旧 `1-38-0` 只收单值、在 `1-69-0` 支持数组；模块**无 `selectById`**。
24. **报告落盘与任务分流**：分析/检查/排障类**必出 MD** 到 `<项目>/.codebuddy/memory/AI 输出文档/`；纯改代码类**不出报告**，只给「改了什么 + 关键差异」。线上报错类任务**先看日志**（SLS 按 traceId 拉全链路），「日志 → 代码 → 数据库」顺序不可打乱，禁止跳日志直接断言根因。
25. **虚拟表"查不到物理表"≠"表未建"**：`spfm_rel_table_definition` 中有定义、但 archery 覆盖的 SaaS `srm` 库 `SHOW CREATE TABLE` 返 1146 时，先怀疑**物理存储落在别的实例/库**，不要直接下「表未建」结论（会误判 P0）。
26. **修复建议要落到统一层**：同一处问题的同类写法往往在目录内多处重复——报告建议应给「在统一层一次性根治」（抽公共方法/统一封装）而非逐调用点打补丁。

---

## 附录 A：API 前后置独立脚本契约（来自 srm-requirement-delivery/marmot-delivery.md §6-7）

> 来源：整合自 `/Users/kaitong/nichuan-custom-skills/srm-requirement-delivery/references/marmot-delivery.md` 第 6-7 章。**注意：仓库的「★6」命名指 API 前后置，与本 spec.md 的「★6 工作流」不是同一物**，本附录用「A.1 / A.2」避免冲突。

SCRIPT_LIB 脚本若被配置到 `marmot_api_rewrite`（按 `value5=beforeScriptCode` / `value3=scriptCode` 区分前后置阶段），按以下契约校验脚本 process(input) 的入参、出参、可改写范围、事务和异常。

### A.1 API 前置脚本（beforeScriptCode）

**触发场景**：标准 Controller 入口，方法前调用一次。`@MarmotApiPoint(apiCode = "...")` 注解 + `marmot_api_rewrite` 中 `value5=beforeScriptCode = <scriptCode>`。

**走查链**：
```
Controller#method(@MarmotApiPoint(apiCode="X") ... )
  → MarmotApiPointInterceptor.beforeExecute
  → api_rewrite（value1=tenantNum / value2=apiCode=X / value5=beforeScriptCode=<script>）
  → independent_script_get(scriptCode)
  → MarmotScriptLibraryHelper.independentScriptExecute(...)
  → process(input)
```

**入参契约**（`input` 对象结构）：

| 字段 | 来源 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| `input.apiCode` | `api_rewrite.value2` | string | ✓ | 路由 apiCode |
| `input.tenantNum` | `STD.CurrentContext.getTenantNum()` | string | ✓ | 当前租户编码 |
| `input.requestBody` | Controller 原始请求体 | object/array | 视接口 | GET 请求可能为空对象 |
| `input.requestHeaders` | HTTP Headers | object | × | 含 token / content-type |
| `input.requestPathParams` | URL 路径参数 | object | × | 如 `/v1/{orgId}/xx/{id}` 的 `{id}` |
| `input.requestQueryParams` | URL 查询参数 | object | × | 解析后的 key-value |

**出参契约**（脚本 `return` 对象，**直接改写 Controller 入参**）：

| 字段 | 用途 | 校验点 |
|---|---|---|
| `return.requestBody` | 改写后的请求体（替换原值） | 字段名/类型必须与 Controller 入参 DTO 一致 |
| `return.skip` | 跳过主业务 | true → 主业务不执行（极少用） |
| `return.error` | 拦截报错 | 非空 → Controller 直接抛 `CommonException(return.error)` |
| `return.errorCode` | 多语言错误码 | 配合 `return.error`，需在 `srm-message` 注册 |

**可改写 vs 不可改写**：
- ✅ **可改写**：`requestBody`（改字段值/类型）、`requestQueryParams`
- ❌ **不可改写**：URL 路径、`requestHeaders`、方法签名参数（编译期已绑定）

**事务**：脚本数据库写入**不与主业务自动共事务**——脚本里的 `object.create/update` 走独立事务；前置脚本不能依赖"主业务尚未产生的数据"。

**异常**：`throw new SimpleException('error.code')` → 直接抛给 Controller → 走标准异常处理；**不传回**主业务。

### A.2 API 后置脚本（scriptCode）

**触发场景**：标准 Controller 入口，方法返回后调用一次。`marmot_api_rewrite` 中 `value3=scriptCode = <scriptCode>`。

**走查链**：
```
Controller#method
  → 主业务执行（DB 写入、状态流转）
  → Controller 返回 responseWrapper
  → MarmotApiPointInterceptor.afterExecute
  → api_rewrite（value3=scriptCode=<script>）
  → independent_script_get
  → process(input)
```

**入参契约**（`input` 对象结构）：

| 字段 | 来源 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| `input.apiCode` | `api_rewrite.value2` | string | ✓ | 同前置 |
| `input.tenantNum` | 当前租户 | string | ✓ | 同前置 |
| `input.requestBody` | Controller 入参快照 | object/array | 视接口 | 主业务已处理 |
| `input.responseBody` | Controller 原始返回值 | object/array | 视接口 | 统一响应包装 `ResponseData<T>` |
| `input.exception` | 主业务异常（若有） | Error/Object | × | 非空表示主业务已报错 |

**出参契约**（脚本 `return` 对象，**直接改写 Controller 响应**）：

| 字段 | 用途 | 校验点 |
|---|---|---|
| `return.responseBody` | 改写后的响应体（替换原值） | 字段名/类型必须与统一响应包装一致 |
| `return.responseBody.content` | 分页列表内容 | 注意层级 `content` vs `data` vs `rows` |
| `return.error` | 二次拦截 | 非空 → 替换原响应为错误响应 |

**可改写 vs 不可改写**：
- ✅ **可改写**：`responseBody.content`（列表项字段）、`responseBody.additionalAttributes`（扩展字段）
- ⚠️ **慎改写**：`responseBody.total`（分页总数）、HTTP 状态码（`httpStatus`）
- ❌ **不可改写**：已发出到客户端的 Header、Cookie

**事务可见性**：
- 主业务 `commit` 之后才进入后置脚本；**主业务已写入的数据可查**
- 但若后置脚本和主业务在同一请求，**不能假设跨服务可查**（分布式事务边界）

**异常**：后置脚本抛异常**不阻断响应**（用户已看到原响应），但会进 SLS ERROR 日志，**必须 try-catch 后写日志**或抛前确认已无业务影响。

### A.3 API 前置 vs 后置 校验差异速查

| 维度 | 前置 (A.1) | 后置 (A.2) |
|---|---|---|
| 触发 | Controller 方法前 | Controller 方法后 |
| 关联字段 | `value5=beforeScriptCode` | `value3=scriptCode` |
| input 含 responseBody | ❌ | ✅ |
| input 含 requestBody | ✅ | ✅（快照） |
| 可改写主业务入参 | ✅ | ❌（已生效） |
| 可改写响应 | ❌（无响应） | ✅ |
| 异常是否阻断 | ✅ 阻断主业务 | ❌ 不阻断响应 |
| 事务边界 | 独立事务 | 主业务已 commit |
| 典型用途 | 字段改写/参数补全/二次校验/拒绝 | 响应补字段/列表加工/异步通知 |

### A.4 校验 checklist（API 前后置）

```text
[前置]
- [ ] api_rewrite 中 value5=beforeScriptCode 与脚本 code 完全一致（大小写敏感）
- [ ] 脚本的 process(input) 引用 input.requestBody.* 字段名与 Controller DTO 字段名一致
- [ ] 若脚本修改 requestBody 字段，类型与 Controller DTO 字段类型一致（不能 string→object）
- [ ] 脚本里的 DB 写入已确认独立事务（不会污染主业务）
- [ ] 错误码（return.errorCode）已在 srm-message 注册
- [ ] 跨租户场景：确认 input.tenantNum 与 api_rewrite.value1 一致

[后置]
- [ ] api_rewrite 中 value3=scriptCode 与脚本 code 完全一致
- [ ] 脚本的 process(input) 引用 input.responseBody.* 路径与统一响应包装结构一致
- [ ] 分页场景：明确 content 层级（content / data / rows / list）
- [ ] 跨服务数据可见性：主业务 commit 后的数据，本服务可查，跨服务需独立验证
- [ ] 后置异常处理：try-catch + 写日志，不抛回 Controller
- [ ] 不修改 HTTP 状态码（除非 return.error 触发）
```

---

## 附录 B：与 zhenyun-ops / srm-script-platform / srm-requirement-delivery 协作关系

> 来源：整合自 `/Users/kaitong/nichuan-custom-skills/zhenyun-ops/SKILL.md`（全局路由中心）。
> 仓库 HEAD commit：`47636a3 feat: 新增调度脚本核查与 SQL 追踪能力，完善工单目标解析流程`
> 仓库位置：`/Users/kaitong/nichuan-custom-skills/`（只读参考，本 skill 不依赖）

### B.1 skill 矩阵

| Skill | 维度 | 与本 skill 关系 | 何时切换 |
|---|---|---|---|
| **marmotscript-js-check**（本 skill） | **静态检查 SOP** | - | 用户说"检查/审查/排查脚本"时优先 |
| `srm-script-platform` (v1.3.0) | 运行时平台态（查询/调试/保存/部署） | 互补：本 skill 不做远程 Debug，平台态时切过去 | 装了 `zhenyun-script-platform-mcp` 后用 |
| `srm-requirement-delivery` (v2.2.0) | 需求交付（按模式拆分产物） | 互补：本 skill 不做交付组织 | 用户说"开发/实现/交付需求"时切 |
| `zhenyun-ops` | 全局路由 | 正交：路由 vs SOP | 跨 Skill 任务时用其路由表 |
| `java-troubleshoot` | 故障排障（SLS+trace+源码+DB） | 互补：本 skill 专注脚本静态维度，不查 trace | 报错/traceId/线上问题切过去 |
| `srm-workbench-bug-triage` | 工作台 bug（待办/搜索/卡片） | 间接：Marmot 脚本可能影响工作台数据 | 工作台现象 + Marmot 脚本介入时 |
| `archery` | DB 只读/工单 | 互补：本 skill 检查脚本用 mysql-db-mcp 仅校验表/字段 | 修数据/查样本切 archery |
| `ssrc-sql-generator` / `spuc-sql-generator` | 寻源/订单 SQL | 间接 | 寻源/订单数据修复时 |
| `knowledge-governance` | 认知库管理 | 间接 | 检查报告沉淀时 |
| `gitlab-code` | 代码定位 | 间接：API 前后置校验需扫 serverName 代码 | 附录 A 校验中需扫代码时 |

### B.2 MCP 能力边界

`marmotscript-js-check` 当前不直接调用 MCP，依赖 `mysql-db-mcp` / `archery` 等只读工具做表/字段校验。如果未来需要 zhenyun-script-platform-mcp 提供的远程 Debug/Save/Deploy 能力，按以下方式扩展：

| 能力 | 主要工具 | 建议使用 skill |
|---|---|---|
| 脚本身份发现 | Pangu `search_adapter_scripts` / `search_standalone_scripts` | `srm-script-platform` / `gitlab-code` |
| 平台当前源码/版本 | Script Platform `adapter_get` / `independent_script_get` | `srm-script-platform` |
| 未保存源码 Debug | Script Platform `*_debug` | `srm-script-platform`（要求 DEV 环境 + 有效 Input） |
| 平台资源 CRUD | Script Platform `platform_resource_*` | `srm-script-platform`（两阶段人工确认） |
| Marmot 静态检查 | Pangu `check_marmot_script_static` | `srm-requirement-delivery` |
| 脚本 trace 时间线 | Pangu `query_script_trace` | `java-troubleshoot` |
| 表/字段验证 | `archery_describe_table` / `archery_list_columns` | `archery` |

### B.3 跨 skill 协作示例

**场景 1：用户报"工作流审批规则没拿到人"**
1. `java-troubleshoot`：按 traceId 拉 SLS 日志，确认是 `ERROR_SERVICE_NOT_FOUND` / `DATA_INVALID` / `asCollection` 转换失败
2. `marmotscript-js-check`（本 skill）：按附录 A.4 / 阶段三检查脚本 process(input) 返回值是否符合 serviceCategory=APPROVAL_CANDIDATE_RULE 契约
3. 如需修改 → 切 `srm-requirement-delivery` 走 Marmot 交付链路

**场景 2：用户报"API 返回字段不对"**
1. `marmotscript-js-check`：检查脚本是否被 `marmot_api_rewrite` 挂载（按附录 A 校验）
2. 如有挂载 → 按 A.4 后置 checklist 校验 return.responseBody 路径
3. 改脚本 → `srm-requirement-delivery`（若需平台级核验则走 `srm-script-platform` adapter_debug/independent_script_debug）

**场景 3：用户报"部署后脚本没生效"**
1. `marmotscript-js-check`：脚本本身无问题（已校验）
2. 切 `srm-script-platform` → `independent_script_get` 读平台当前态 / `platform_scheduled_script_inspect` 查调度状态
3. 切 `java-troubleshoot` → `query_script_trace` 拉脚本 trace 确认是否真被调用

### B.4 仓库同步策略

- 仓库位置：`/Users/kaitong/nichuan-custom-skills/`
- 同步方式：`git -C /Users/kaitong/nichuan-custom-skills pull` 拉最新
- 整合触发：当仓库 `marmot-delivery.md` / `delivery-gates.md` / `srm-script-platform/SKILL.md` 变更时，复审本附录
- 整合方法：手工 cherry-pick 相关章节到本附录（自动化风险高，需人工判断）

---

> **附录版本**：v1.1（附录 A/B 正文仍为 v1.0，2026-10-12 整合自 nichuan/custom-skills HEAD `47636a3`；同日主规范正文升 v1.1）
> **下一次复审触发**：仓库 `marmot-delivery.md` 或 `srm-script-platform/SKILL.md` 文件 mtime 变化时

