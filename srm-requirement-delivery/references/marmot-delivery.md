# Marmot 产物实施链路

适用于新增脚本、契约级修改、平台绑定或混合需求中的脚本部分。平台脚本、平台配置和本地交付文件是不同对象，必须分别识别和验证。

## 1. 先建立产物清单

每个产物单独记录角色、身份、依赖和交付状态：

| 产物 | 精确身份 | 必要前置 |
| --- | --- | --- |
| Adapter Line | `tenant + taskCode + runningService + lineId` | 标准 Adapter 埋点契约；平台事件编码存在 |
| API 前置脚本 | `tenant + scriptCode + quickType=API_PRE` | 标准 `apiCode` 存在；请求上下文契约已确认 |
| API 后置脚本 | `tenant + scriptCode + quickType=API_POST` | 标准 `apiCode` 存在；响应结构已确认 |
| API 发布脚本 | `tenant + scriptCode + quickType=API_PUBLISH` | 发布路由、方法、权限/租户和输入输出契约已确认 |
| API 改写绑定 | `tenant + apiCode + 阶段/记录版本` | 目标独立脚本身份已确认 |
| API 发布资源 | `tenant + 发布编码/记录版本` | 发布脚本和对外契约已确认 |
| CodeBlock | `tenant + blockCode` | 调用方和导出/调用约定已确认 |
| QueryBlock | `tenant + queryBlockCode` | 参数、SQL 意图和调用方已确认 |

脚本编码不等于 `apiCode`；脚本源码不等于 API 改写绑定或 API 发布资源。`api_rewrite` / `api_publish` 必须作为独立平台产物记录，不能因脚本存在就宣称已经挂载或发布。

## 2. 读取平台当前态

### 已有产物

1. 已知 Adapter 精确身份时调用 `adapter_get`；多 Line 必须选择唯一 `line_id`。已知独立脚本时调用 `independent_script_get`。
2. 身份不完整时，Adapter 只用 Pangu `search_adapter_scripts`，Independent 只用 `search_standalone_scripts` 做候选发现；确认身份后回到精确 `get`。
3. API 前置/后置同时读取目标 API 点和现有 `api_rewrite`：用 `platform_api_point_list`、`platform_resource_search`/`platform_resource_get` 和需要时的 `platform_relations_get` 核实 `apiCode`、阶段、脚本引用和版本。
4. API 发布同时读取 `api_publish` 资源和关系；不能只读取脚本正文。
5. 本地与平台均有非模板逻辑且哈希不同，保留双方、列出差异并停止覆盖。平台源码、版本、Fixture 和启用状态以精确 `get` 为准。

### 新产物尚不存在

平台没有目标记录时，不把“未找到”误报为模板，也不要求先有平台空模板才能写本地代码：

1. 用标准埋点/API 契约、平台 `platform_definition_get` 的字段定义，以及最多两个同类型已核实样例确定入口和必填元数据。
2. 在本地创建最小产物和门禁记录，平台 ID、版本和绑定状态标为 `N/A（尚未创建）`。
3. 只有用户明确要求创建平台对象时才生成写计划。Independent 用 `independent_script_create`；Adapter 先核实 `adapter_event` 注册表，再用 `adapter_create`，创建后必须重新 `get`，选择真实 Line 后才能编辑或部署源码。
4. Independent 的 `permission`、`module`、`quickType` 与描述是创建契约，不得猜。`quickType` 可能连带平台资源，创建后要回读关系，不能假设绑定/发布必然成功。

## 3. 完整实现闭环

1. 在 `request.md` 写目标、约束、验收点和产物清单；在 `artifacts.json` 写精确身份和当前态。
2. 按[设计门禁模板](delivery-gates.md)确认触发、输入输出、字段来源、数据/外部服务、事务、幂等、日志、异常和平台关系。只填适用项；阻止正确编码的 `TBD` 先核实。
3. 把平台已有正文或新产物最小骨架写入约定本地路径。空模板也保留其注释、入口和配置线索。
4. 只实现需求要求的逻辑；历史脚本坚持最小改动，不重排结构、统一风格或清理无关代码。
5. 做本地语法、运行时兼容和业务规则静态检查，更新 `artifacts.json` 的本地源码哈希和检查哈希。
6. 用户要求真实运行且有有效 DEV Input 时，用未保存源码 Debug；根据结果做最小修正。没有有效 Input 时标记 `NO_VALID_FIXTURE`，不编造复杂 DTO 或 HTTP Context。
7. 用户明确要求保存、部署、创建、绑定或发布时才进入两阶段平台写入；写后回读源码、关系、版本和启用状态。

## 4. Adapter 脚本

### 输入与返回契约

- 从标准埋点调用点确认输入对象、租户来源、触发时机、调用次数、事务、脚本缺失行为、异常传播和标准侧是否消费返回值。
- Fixture 优先级：用户显式 `raw_input` → `adapter_get` 返回的 `AVAILABLE` Fixture → 从真实 DEV 日志取得文本并用 `adapter_extract_input` 提取 → 无有效值则不 Debug。
- 长整型 ID 保持已确认类型。数字型 ID 判空不用 `_.isEmpty`；字符串、集合和对象按真实类型处理。
- 若标准侧忽略脚本返回值，不设计依赖返回回写的逻辑；若标准侧消费返回值，返回对象必须满足精确类型和空值契约。

### 实施和验证

1. 确认 Header 与目标 Line 版本、启用状态和 `scriptVersion`；多 Line 不默认第一条。
2. 只修改目标 Line；同一 `taskCode` 交付多个 Line 时使用带 `line-id` 的本地路径，避免覆盖。
3. 核对重复触发、批量范围、数据库写入过滤、异常是否回滚主业务以及外部调用次数。
4. 执行 `node --check`、入口检查和 `check_marmot_script_static`；用户要求时执行 `adapter_debug`。
5. 部署只用 `adapter_deploy`，携带最近一次 Header/Line 版本和明确 `line_id`。不使用通用资源 CRUD 绕过停用、完整保存、回读校验和状态恢复。

## 5. API 前置独立脚本

1. 核实标准 `@MarmotApiPoint` 的 `apiCode`、完整 HTTP 路由、Controller 参数绑定和平台实际传入的 HTTP Context 结构。
2. 明确允许读取/改写的请求字段、改写后的类型、缺失/空值处理、校验顺序和拒绝策略。前置脚本不得读取或构造尚不存在的标准响应。
3. 明确独立事务：脚本数据库写入不与后续主业务自动共用事务；不得依赖读取主业务尚未产生的数据。
4. 核实 `api_rewrite` 绑定把正确 `apiCode + 前置阶段` 指向目标 `scriptCode`；当前平台关系字段通常为 `beforeScriptCode`，写入前仍以 `platform_definition_get` 的当前定义为准。源码与绑定分别验证。
5. 执行本地检查；用户要求且有有效 HTTP Context 时用 `independent_script_debug`。保存脚本与创建/更新绑定分别生成写计划并分别回读。

## 6. API 后置独立脚本

1. 核实标准 `apiCode`、Controller 原始返回类型、统一响应包装、分页/集合层级和平台传入的响应 Context 路径。
2. 明确允许改写的响应字段、类型、空响应、标准错误响应和异常策略。后置脚本不得假设可以重新改变已经完成的 Controller 入参或主业务副作用。
3. 若需要查询主业务刚写入的数据，必须按独立事务与提交时序核实可见性；不能照搬 Adapter 同事务假设。
4. 核实 `api_rewrite` 绑定把正确 `apiCode + 后置阶段` 指向目标 `scriptCode`；当前平台关系字段通常为 `scriptCode`，写入前仍以 `platform_definition_get` 的当前定义为准。源码与绑定分别验证、保存和回读。

## 7. API 发布独立脚本

1. 明确发布路由、HTTP 方法、脚本 `quickType=API_PUBLISH`、权限、租户上下文、请求参数、响应包装和副作用；路由与脚本编码不是同一身份。
2. 核实匿名/登录态、租户隔离、参数校验、幂等、错误码、日志脱敏以及外部/数据库写入范围。
3. 读取或设计对应 `api_publish` 资源，记录它与 `scriptCode` 的关系和版本。只实现脚本不能宣称 API 已发布。
4. 对正常、空输入、非法输入、无权限、重复调用和下游失败做适用验证。远程 Debug 不等于真实网关路由、鉴权或发布生效验证。
5. 用户明确要求发布时，脚本保存和 `api_publish` 创建/更新均遵循两阶段确认；完成后回读关系，并把无法在线验证的网关行为列为未验证。

## 8. CodeBlock 与 QueryBlock

- CodeBlock 明确调用方、参数、返回和异常约定；查 `platform_relations_get` 确认引用，不能把修改当作只影响单一脚本。
- QueryBlock 明确参数、查询/写入意图、租户过滤、结果列与空结果。需要真实表结构时只读核实；禁止用不受控 SQL 替代平台资源流程。
- 用户要求创建或更新资源时，先读 `platform_definition_get` 和当前版本，再通过对应平台资源工具生成两阶段写计划，写后回读内容与引用关系。

## 9. 验证细则

- JavaScript 只有一个平台要求的同步全局 `function process(input)` 入口；不使用 ESM/CommonJS 导出或 Node/浏览器专属全局，除非目标平台契约明确支持。
- `check_marmot_script_static.rules_json` 只放当前需求已确认规则；`error` 必须修正，`warning` 必须修正或解释。静态检查不等价于 GraalJS、数据库、权限、事务和远程服务验证。
- `artifacts.json` 的源码哈希必须对应最终已检查文件；后续修改使哈希变化时重新检查。
- Fixture 只覆盖本地可表达的关键分支。不得用 Node 模拟冒充 GraalJS Debug，也不得把 Debug 冒充平台绑定、网关路由或生产行为验证。
- 最终逐项报告脚本源码、平台脚本记录、绑定/发布资源各自是“仅本地”“平台已存在未改”“已生成待确认计划”还是“已写入并回读”。
