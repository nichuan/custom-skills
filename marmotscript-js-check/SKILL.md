---
name: marmotscript-js-check
description: 只读审查 SRM Marmot/GraalJS 的 Adapter、Independent Script、CodeBlock 及其 QueryBlock 依赖，核对语法、目标运行时 API、调用场景的入参返回契约、租户隔离和数据副作用。用户要求检查、review 脚本或核对调用契约时使用；纯平台配置查询走 srm-script-platform，故障根因先走 java-troubleshoot，开发修改走 srm-requirement-delivery。
---

# MarmotScript 脚本审查

本 Skill 提供脚本审查判断与检查清单，不重新编排需求交付、平台操作或生产排障。复用前序已确认的环境、租户、脚本身份、源码、版本、输入与证据；只补会改变结论的缺口。

## 入口与范围

| 请求 | 处理 |
| --- | --- |
| review 给定本地脚本、片段或 diff | 直接审查；缺平台证据时限定结论为本地，不为流程完整查询生产系统 |
| 核对脚本入参、返回、依赖或实际调用场景 | 审查相关契约；需要当前配置时复用 [srm-script-platform](../srm-script-platform/SKILL.md) 的精确读取 |
| 只查挂载、启用状态、部署或配置 | 交给 srm-script-platform，不自动做代码审查 |
| 报错、traceId、prod-bug、线上不生效 | [java-troubleshoot](../java-troubleshoot/SKILL.md) 先建立执行证据；定位到脚本后用本 Skill 做定向核对，静态问题不自动成为本次根因 |
| 要实现或修复脚本 | [srm-requirement-delivery](../srm-requirement-delivery/SKILL.md) 决定修改与交付范围，本 Skill 复用其身份和最终源码进行验证 |

默认只读审查。发现同类问题可说明影响范围；不因审查自动全目录改写、迁移旧 API、调试、部署或写评论。用户已授权修复时沿用交付流程的最小修改边界。

## 审查依据

- 本地文件是本地产物；文件名里的 `tenant|ADAPTOR/SCRIPT_LIB|code` 只帮助定位候选，不证明实际租户、脚本类型、部署、生效或执行。
- 平台当前源码、Fixture、版本、Header/Lines、状态、定义与关系以 Script Platform MCP 的精确读取为准；本地与平台不同则分别记录哈希和用途，不静默选一方作为生产实现。
- Adapter 精确身份为租户、taskCode、runningService，涉及单条实现时还需明确 Line；Independent 为租户和 code，实际 quickType 来自平台记录，API 前/后置来自关系。
- 平台工具的目标环境先由当前配置确认。DEV 当前态不能证明 PROD 发生时的源码、部署或绑定；历史结论需要相应版本/部署记录或当时请求证据。
- 模块签名依次核对目标版本的 JS 导出包装、Java helper 全部相关重载及返回处理，类型声明作为辅助。需要标准代码时经 `search_repo` 定向定位；没有目标版本证据就标未验证，不沿用别人的机器路径、固定分支或历史签名表。
- 租户编码 `tenantNum` 与数字 `tenantId` 不互换。业务表只查已确认租户；只有目标配置有共享语义且访问范围已确认时才包含 0 租户。表名、分表后缀、schema 和 `valueN/longvalueN` 映射必须来自当前定义或真实结构，不由文件名拼接。
- 平台脚本与资源正文经平台工具读取，不通过 Archery 直接解码脚本存储。只有表/字段/真实值是判断必要证据时，复用 [archery](../archery/SKILL.md) 做定向只读核实。表查询为空或一次 1146 不证明逻辑对象不存在。

## 执行检查

按问题选择适用项，不固定跑八阶段或全量查表。

1. **确认审查对象**：记录源码来源、范围（完整源码/片段/diff）、类型、环境、租户、精确身份和 SHA-256。审查 diff 时读取理解改变所需的调用上下文。
2. **语法与运行时**：完整 JavaScript 用 `node --check`，只证明解析通过，不执行脚本。Adapter/Independent 核对同步全局 `function process(input)`；CodeBlock 按实际调用/导出契约，QueryBlock 按参数、SQL 意图与结果核对。拒绝目标平台不支持的 Node/浏览器 API、异步入口和导出方式。
3. **静态工具**：Adapter/Independent 调用 Pangu `check_marmot_script_static`，`rules_json` 仅传已确认且适用的规则；字段、常量、日志与批量范围规则见[交付门禁](../srm-requirement-delivery/references/delivery-gates.md)。新增 `allowed_runtime_modules` 只列目标运行时已核实的精确 Marmot 模块路径，不能为消除报错任意放行。工具不可用或用户限制工具执行时继续人工审查，明确记录静态门禁未运行；本地审查不扩大为在线取证。
4. **解释工具结果**：检查 `ok`、`status`、`findings` 和源码哈希；`ok=true` 只表示工具调用成功，不代表审查通过。工具是词法启发式，不证明 API、部署、权限或执行结果。CodeBlock 无 `process` 等契约差异不套通用入口门禁；注释/字符串等误报用具体源码和目标契约说明，不静默丢弃。确认的 `error` 修正前不通过，`warning` 按真实影响修正或解释，证据不足的项目保留未验证。
5. **场景与数据逻辑**：仅加载[场景检查](references/spec.md)中适用部分，核对空输入、类型、返回包装、异常传播、查询范围、分页、并发、幂等及事务/外部副作用。批量规模、资源限制和时区取实际业务与目标运行时值，不套历史固定阈值。
6. **类型诊断**：项目本来启用 `checkJs`/TS 且工具可用时才运行其现有检查。模块缺声明与字段/调用错误分别验证；诊断码本身不定因。优先补正确声明、局部 JSDoc 与窄类型，不给整个模块加 `any`、`@ts-ignore` 或关闭检查来冒充修复。声明缺失或运行时无法验证时说明边界。

已核实支持的 `@M/v1/*`、旧版 `STD/BIZ` 与平台封装按目标契约检查；不强制存量脚本切换 require、logger2、头部模板或所谓 v3.3 规范。代码风格只有明确项目约定时才作为建议，不能代替业务问题。

## 平台依赖与调用关系（有需要才取证）

| 问题 | 当前工具入口 |
| --- | --- |
| 已知 Adapter/Independent 的当前源码与状态 | `adapter_get` / `independent_script_get`；身份不完整时复用平台 Skill 的发现路由 |
| 引用的 CodeBlock、QueryBlock、API、导入、消费或调度配置 | `platform_resource_search` 缩小范围后 `platform_resource_get`；编码、租户、记录与版本一起核实 |
| 不清楚可读资源或字段 | `platform_capabilities_list`，对支持的资源按需 `platform_definition_get` |
| 同一编码被哪些平台资源引用 | `platform_relations_get`；只有租户编码与真实数字 ID 都已确认才调用，并传 `scheduler_tenant_id`，避免调度关系退化为无租户扫描 |
| 已知同租户调度脚本与任务 | `platform_scheduled_script_inspect`，仍不证明真实调度执行成功 |
| API 挂载点是否注册 | `platform_api_point_list`，再核对指定关系和标准方法契约 |

关系工具是有界候选扫描，必须保留 `scan_scope`、warnings 和截断信息；它不覆盖所有工作流、跨脚本或间接调用。未命中只能写“本次范围未发现引用”，不能判定永不执行或 P1。数字租户 ID 缺失时不调用会全局扫描的关系工具；改查已知精确关系，其他关系标未验证。发现多个实际入口时分别审查其契约；仅在用户要求完整依赖审查或证据显示多入口时扩大范围。

本地存在依赖只能说明本地可见。目标平台精确对象、启用与关系证明当前配置；执行日志才证明被调用。三种证据分别报告。

## 交付审查结论

优先报告可复现、会改变行为的问题：位置、触发条件、实际影响、证据、最小建议与尚缺的验证。区分代码错误、配置错误、工具/声明环境问题和风格建议。

- 使用当前体系的 P0–P3 优先级时按数据/权限风险、影响范围、发生概率和紧迫性定级；不能把任意语法错误固定定为 P0，也不能把未验证配置作为已确认缺陷。
- 分别报告语法、静态工具、人工契约、类型检查与运行验证结果；没有运行验证就标未验证，不把静态通过写成运行成功。最终改动的哈希变化后重新做相关检查。
- 审查没有发现确定问题时可直接说明，并列出材料限制。普通审查在对话中交付；只有用户要求或项目明确约定时落盘到指定目录，不强制创建 `.codebuddy/memory` 报告。
- 本 Skill 不授权 Debug、保存、部署、绑定、执行任务或评论写入；需要这些动作时回到对应专项流程。
