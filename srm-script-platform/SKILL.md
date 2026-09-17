---
name: srm-script-platform
description: 查询、读取、修改、远程调试、保存或部署甄云 SADA/Marmot/GraalJS 脚本平台中的 Adapter 与 Independent Script 时使用。平台当前源码、版本、Fixture 和启用状态以 zhenyun-script-platform-mcp 为准；Pangu 只负责模糊发现、日志、数据库和静态检查。不用于标准 Java 改造、单纯 SQL 修复或只有日志/trace 的根因排查。
---

# SRM 脚本平台开发

本 Skill 负责 Script Platform 的开发生命周期和跨 MCP 路由。它不替代需求分析或故障排查
Skill；从其它流程进入时复用已经确认的租户、脚本编码、运行服务、Line、环境和 Input，不重复
发现。

## 唯一事实源

- `zhenyun-script-platform-mcp` 是平台当前源码、版本、Fixture、启用状态、远程 Debug、保存和
  部署的权威入口。
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
| 未保存 Adapter 源码调试 | `adapter_debug` |
| 未保存 Independent 源码调试 | `independent_script_debug` |
| 从已查询日志文本提取 Adapter Input | `adapter_extract_input` |
| 用户明确要求保存 Independent Script | `independent_script_save` |
| 用户明确要求部署 Adapter | `adapter_deploy` |

Pangu 搜索只提供候选身份，不作为 Debug/Save/Deploy 前的最终源码依据。搜索命中多个精确候选
时停止并让用户选择，不猜环境、服务或 Line。

## 工作模式

### 只查询

直接调用对应 `get`，返回当前源码、`source_hash`、版本、Fixture 状态和 Adapter 全部 Lines。
查询请求不调用 Debug，不改变启用状态，也不触发写工具。

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
才能调用写工具。普通“修改、开发、调试、验证、看看结果”不构成写授权。

- Independent Script：把最近一次 `get` 的 `object_version_number` 作为
  `expected_version` 调用 `independent_script_save`。
- Adapter：把最近一次 `get` 的 Header/Line 版本与明确 `line_id` 传给 `adapter_deploy`。
- `VERSION_CONFLICT` 时重新读取并报告差异，不自动覆盖。
- `SAVE_VERIFICATION_FAILED` 或 `RE_ENABLE_FAILED` 时保留工具返回的真实状态，明确标注
  `requires_manual_attention`，不把部分成功写成完全失败或完全成功。
- 写开关关闭或目标主机不在白名单时停止，不尝试绕过安全配置。

## 与其它 Skill 协作

- 新需求、本地交付目录和产物组织由 `srm-requirement-delivery` 负责；需要平台当前态、真实
  Debug 或用户授权的保存时采用本 Skill 的路由。
- 异常、traceId、接口失败或线上行为不明由 `java-troubleshoot` 负责；它读取平台当前源码，
  但不因排障请求自动 Debug 或部署。
- 只定位实现位置由 `gitlab-code` 负责；平台脚本正文仍以对应 `get` 为准。
- 日志查询和 DB 验证由 Pangu 完成，本 MCP 不增加 Loki/SLS/Archery 能力。

## 结果说明

最终区分并报告：平台读取版本、实际调试源码哈希、Fixture 来源、Debug 结果、是否已经持久化、
最终 Adapter 启用状态，以及仍需人工处理的失败恢复项。没有调用写工具时明确说明平台仍是旧
源码。
