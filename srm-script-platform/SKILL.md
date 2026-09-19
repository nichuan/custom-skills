---
name: srm-script-platform
description: 查询、读取甄云 SADA/Marmot/GraalJS 脚本与平台配置的平台当前态，或远程调试、保存、部署平台脚本及管理 API、消费端、调度、常量、OutBound、CodeBlock、QueryBlock 等资源时使用。本地脚本文件的最小改动走 srm-requirement-delivery。平台当前态以 zhenyun-script-platform-mcp 为准；Pangu 只负责模糊发现、日志、数据库和静态检查。不用于标准 Java 改造、单纯 SQL 修复或只有日志/trace 的根因排查。
---

# SRM 脚本平台开发

本 Skill 负责 Script Platform 的脚本开发生命周期、平台配置资源和跨 MCP 路由。它不替代需求
分析或故障排查 Skill；从其它流程进入时复用已经确认的租户、脚本编码、运行服务、Line、环境
和 Input，不重复发现。

## 唯一事实源

- `zhenyun-script-platform-mcp` 是平台当前源码、版本、Fixture、启用状态、资源定义、挂载关系、
  远程 Debug、保存和部署的权威入口。
- `zhenyun-pangu-mcp` 的脚本工具只用于编码、租户或 `running_service` 不完整时的模糊发现；
  找到精确身份后必须回到 Script Platform MCP 读取当前对象。
- Pangu 继续负责日志、数据库、trace、标准源码、猪齿鱼和静态检查。不要用 Archery 直接读取
  Base64 脚本正文。

## 工具路由

| 目标 | 工具 |
| --- | --- |
| 已知 `tenant + task_code + running_service` 的 Adapter | `adapter_get` |
| 已知 `tenant + code` 的 Independent Script | `independent_script_get` |
| Adapter 身份不完整 | Pangu `search_adapter_scripts`，再 `adapter_get` |
| Independent 编码不完整 | Pangu `search_standalone_scripts`，再 `independent_script_get` |
| 对 Marmot JS 做静态门禁检查 | Pangu `check_marmot_script_static`（需求规则经 `rules_json` 传入） |
| 未保存 Adapter 源码调试 | `adapter_debug` |
| 未保存 Independent 源码调试 | `independent_script_debug` |
| 从已查询日志文本提取 Adapter Input | `adapter_extract_input` |
| 用户明确要求保存 Independent Script | `independent_script_save` |
| 用户明确要求新建 Independent Script | `independent_script_create`（写操作，两阶段确认；创建后回读验证） |
| 用户明确要求部署 Adapter | `adapter_deploy` |
| 查看目标环境、脱敏认证元数据和写入边界 | `platform_context_get` |
| 不确定当前 MCP 覆盖范围或 `resource_type` | `platform_capabilities_list` |
| 搜索/精确读取平台配置资源 | `platform_resource_search` / `platform_resource_get` |
| 查看字段定义、动作元数据 | `platform_definition_get` |
| 查脚本、CodeBlock、API 改写之间的引用关系 | `platform_relations_get` |
| 查 API 前后置挂载点 | `platform_api_point_list` |
| 用户明确要求新增/修改/删除平台配置 | `platform_resource_create` / `platform_resource_save` / `platform_resource_delete` |
| 用户明确要求执行已登记表动作 | `platform_table_action` |
| 用户明确要求创建/改元数据/启停/删除 Adapter | `adapter_create` / `adapter_update` / `adapter_toggle` / `adapter_delete` |

Pangu 搜索只提供候选身份，不作为 Debug/Save/Deploy 前的最终源码依据。搜索命中多个精确候选
时停止并让用户选择，不猜环境、服务或 Line。

适配器与独立脚本的模糊发现走 Pangu `search_adapter_scripts` / `search_standalone_scripts`；
`platform_resource_search(resource_type="adapter_task"/"independent_script")` 用于按已知租户、
编码或关键词精确列取，以及平台配置资源调查。两条路都能命中同一脚本对象时，一律以 Script
Platform `get` 的返回为当前态依据，不把任一搜索结果当源码。

通用资源只使用 `platform_capabilities_list` 返回的封闭 `resource_type`。当前覆盖 Adapter 与独立
脚本全览、Topic 消费端、API 发布、API 改写与挂载、功能数据导入、调度、常量、OutBound 白名单、
CodeBlock、QueryBlock、脚本日志和 Adapter 事件注册表。不要构造任意 URL、表名或 actionId。

## 工作模式

### 只查询

直接调用对应 `get`，返回当前源码、`source_hash`、版本、Fixture 状态和 Adapter 全部 Lines。
查询请求不调用 Debug，不改变启用状态，也不触发写工具。

平台资源调查先用 `platform_resource_search` 缩小范围，再用 `platform_resource_get` 读取唯一记录；
不清楚字段时先看能力清单的 `definition` 标记，再对可用资源读 `platform_definition_get`，查依赖时
用 `platform_relations_get`。只有需要校验当前凭据是否可访问远端时才给
`platform_context_get(validate_remote=true)`；返回值只能使用脱敏元数据，
不得索取、展示或转述 Token/Cookie。

### 修改与远程调试

1. 用对应 `get` 读取当前源码和版本；多 Line Adapter 保留用户指定的 `line_id`，不能默认选
   第一条。
2. 只修改用户要求的逻辑。已有实现默认最小改动，保留入口、结构、风格和兼容分支。
3. Input 按下面顺序选择：
   - 用户显式提供的 `raw_input`；
   - `get` 返回且状态为 `AVAILABLE` 的保存 Fixture；
   - Pangu 查询到的真实 DEV 日志文本，再用 `adapter_extract_input` 提取；
   - 均无有效值时停止为 `NO_VALID_FIXTURE`，不得编造复杂 DTO。
4. 调用对应 Debug。Debug 使用当前未保存源码，不先 Save，不 disable/enable Adapter。
5. 根据 `result` 和 `logs` 做必要的最小修改并重复 Debug，直到满足用户要求或出现真实阻塞。

Debug 不持久化脚本，但脚本自身可能调用 DEV 服务或数据库。只在 DEV、输入范围明确且用户要求
运行/调试时执行；不能把“未保存”解释为“没有业务副作用”。

### 保存或部署

只有用户当前请求明确包含“保存、发布、部署、更新到 DEV、正式更新脚本”等持久化意图时，
才能调用写工具生成确认计划。普通“修改、开发、调试、验证、看看结果”不构成写授权。

所有写工具都必须严格执行两阶段人工确认，不能因为用户最初已经说“保存”而跳过第二阶段：

1. 先读取最新对象和版本，再以最终参数调用写工具，但不传 `confirmation_token`。此调用只能返回
   `requires_confirmation=true` 的签名计划，不会写平台。
2. 向用户完整展示目标、版本、动作/变更摘要、`request_sha256` 和有效期，然后结束当前轮。不得在
   同一轮替用户确认，也不得把第一次返回的 token 立即自动回传。
3. 只有用户在后续消息中明确确认这份未变化的计划，才用完全相同的业务参数加返回的
   `confirmation_token` 再调用一次。用户改变范围或参数时，丢弃旧 token 并重新生成计划。
4. token 与工具名和完整参数绑定、短时有效且只能使用一次；过期、参数漂移或失败后重试都必须
   重新生成计划并再次确认。不要展示 token 内容之外的任何认证秘密。

- Independent Script：把最近一次 `get` 的 `object_version_number` 作为
  `expected_version` 调用 `independent_script_save`。
- Adapter：把最近一次 `get` 的 Header/Line 版本与明确 `line_id` 传给 `adapter_deploy`。
- `VERSION_CONFLICT` 时重新读取并报告差异，不自动覆盖。
- `SAVE_VERIFICATION_FAILED` 或 `RE_ENABLE_FAILED` 时保留工具返回的真实状态，明确标注
  `requires_manual_attention`，不把部分成功写成完全失败或完全成功。
- `platform_context_get` 报告自动认证状态和两阶段写策略；不得索取或展示账号密码、访问 Token。

### 平台资源写入与动作

普通“查一下、分析、给方案、确认配置”只授权读取。只有用户明确要求创建、修改、删除、启停、
执行动作或更新 DEV 时，才能按上述两阶段协议调用对应写工具：

- 脚本源码继续使用 `independent_script_save` 或 `adapter_deploy`；不要用通用资源 CRUD 绕过源码
  编解码、完整对象保存、停用恢复和回读校验。
- 通用 `save/delete`、`platform_table_action`、`adapter_update/toggle/delete` 必须使用刚刚读取的
  `objectVersionNumber` 作为 `expected_version`；冲突后重新读取并报告，不自动覆盖。
- `adapter_create` 必须使用平台事件注册表中真实存在的事件任务编码；工具本身不接收 Line，平台会按注册表预填首条 Line 并创建为禁用状态，创建后先 reload 回读再编辑源码并验证。
- 调度启停/立即执行和 OutBound 连通性测试可能产生真实业务副作用，必须把具体目标和动作写清楚；
  不因工具名含“test”就自动执行。
- 常量 `value` 等秘密字段会被屏蔽，也禁止通过模型上下文创建或修改；这类值必须走平台外的受控
  凭据流程。
- `scheduler` 使用数字 `tenantId`，多数其它资源使用租户编码 `tenantNum`。不互相猜测或转换。
- 删除前先读取精确目标并向用户复述唯一标识和当前状态；Adapter 必须先处于停用状态。
- HZERO 导入执行和 API 在线测试不在当前安全能力内；不要用相近动作替代。

## 与其它 Skill 协作

- 新需求、本地交付目录和产物组织由 `srm-requirement-delivery` 负责；需要平台当前态、真实
  Debug 或用户授权的保存时采用本 Skill 的路由。
- 异常、traceId、接口失败或线上行为不明由 `java-troubleshoot` 负责；它读取平台当前源码，
  但不因排障请求自动 Debug 或部署。
- 只定位实现位置由 `gitlab-code` 负责；平台脚本正文仍以对应 `get` 为准。
- 日志查询和 DB 验证由 Pangu 完成，本 MCP 不增加 Loki/SLS/Archery 能力。

## 结果说明

最终区分并报告：平台读取版本、实际调试源码哈希、Fixture 来源、Debug 结果、是否已经持久化、
资源或动作的回读验证、最终 Adapter 启用状态，以及仍需人工处理的失败恢复项。没有调用写工具
时明确说明平台状态未改变。
