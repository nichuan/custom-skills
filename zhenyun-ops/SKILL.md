---
name: zhenyun-ops
description: 甄云 SRM 全局智能路由中心，仅在请求跨域或无法直接命中具体子 Skill 时使用。路由需求开发、脚本平台查询/调试/保存、猪齿鱼查询、故障排查、工作台排障、SQL、数据库、认知库和代码定位；意图明确时直接使用对应子 Skill。
---

# 甄云 SRM 全局路由

## 跨流程协作（按需）

单项任务沿用本技能最短路径。仅在跨技能/跨 agent 交接或恢复任务时读取[协作协议](references/collaboration-contract.md)；若该文件未安装，使用 `get_workflow_guide(topic="handoff")`，无需为此额外安装技能。复用已有环境、租户、证据引用与验证结果；可变数据执行前重核，知识库命中不等于实时事实。用户已要求后续实现/修复时继续完成，只询问真正阻塞的未知信息。知识沉淀先准备可审阅内容，已明确授权的同范围动作不重复确认。

本 Skill 只识别意图、安排专项 Skill 的先后顺序和共享上下文，不复制专项业务流程；仅可调用本地只读 `get_workflow_guide` 获取协作协议，不直接执行其它业务 MCP。当前运行时没有动态 Skill 加载工具时，不得构造 `use_skill`；直接按已经选中的专项 Skill 执行，或明确告诉用户下一入口。

意图已明确时不要加载或复述本路由流程。跨域任务只按真实数据依赖串行；互不依赖且各自需要多轮取证的调查可委派子代理，否则优先同轮并行工具调用。每个专项 Skill 复用前序已验证的环境、租户、任务、脚本、表和源码信息，不重新发现。

## 路由表

| 用户目标 | Skill |
| --- | --- |
| 查询、读取、远程调试、保存或部署 Script Platform 的 Adapter / Independent Script | `srm-script-platform` |
| 修改需求目录中已有 Marmot JS/SQL 的字段取值、常量、表达式或局部逻辑 | `srm-requirement-delivery` 快速修改；需要平台当前态或远程 Debug 时采用 `srm-script-platform` 路由 |
| 按猪齿鱼需求号开发新的埋点、API 挂载/API 发布、CodeBlock 或 QueryBlock | `srm-requirement-delivery` 完整需求 |
| 标准 Java / 混合需求的分析与实现 | 按目标仓库开发约定实现；`gitlab-code` 只定位，Marmot 子产物才用 `srm-requirement-delivery` |
| 只查询猪齿鱼任务、评论、状态或附件 | `choerodon-task` |
| 异常、错误码、traceId、日志、接口失败、超时或线上问题 | `java-troubleshoot` |
| 询价、招标、报价、评分、资格预审、寻源结果相关 SQL | `ssrc-sql-generator` |
| 订单、收货、发货、送货单、状态机、委外相关 SQL | `spuc-sql-generator` |
| 采购员工作台/角色工作台待办缺失或计数不对、整改模块单据/待办异常、卡片字段展示异常、超级搜索查不到单据、单据动态/关注异常、ES 权限或消费不一致 | `srm-workbench-bug-triage` |
| 查实例/库/表结构/样本，或确认 Archery 环境映射 | `archery` |
| 查询、沉淀、修正、归档或删除盘古认知库知识 | `knowledge-governance` |
| 只找类、DTO、方法、文件、适配器或独立脚本实现 | `gitlab-code` |

## 判定规则

- “查需求”和“开发纯二开需求”不同：前者走 `choerodon-task`，后者由 `srm-requirement-delivery` 实现。已有脚本的明确局部修改优先走快速修改；需求号、租户或环境只是附带标识时，不读取猪齿鱼、平台或数据库。只有新需求实现或用户明确要求重新取证时，才读取任务和平台模板。需要标准 Java 改造时不进入该 Skill。
- “查脚本/调试脚本/保存或部署脚本”直接走 `srm-script-platform`。平台当前源码、版本、Fixture 和启用状态以 Script Platform MCP 为准；Pangu 脚本搜索只在精确身份缺失时发现候选。
- 有异常、报错或日志线索时先排障；纯查询或修复 SQL 才进入 SQL Skill。
- 普通 Bug 不能直接假定为标准 Bug：只有执行链覆盖故障区段且没有适配器或 API 前/后置挂载调用，才默认检索标准仓库。载体未知时由 `java-troubleshoot` 先按 traceId、明确日志关键字或脚本定位信息取证；信息均不足则追问，不宽泛搜索日志或代码。
- 独立脚本、适配器、API 挂载、租户定制及外部接口对接 Bug 走 `java-troubleshoot` 的脚本优先路径：日志固定限定 `srm-script-container`；无可靠日志关键字时先取脚本并使用源码中的真实日志字面量；标准仓库只在核实脚本契约/平台行为确有必要或用户明确要求时最后定向检索。
- 采购寻源走 `ssrc-sql-generator`；采购订单及下游履约走 `spuc-sql-generator`。
- 工作台现象（待办/计数、整改模块、卡片字段、超级搜索、单据动态/关注、ES 权限/消费）优先走 `srm-workbench-bug-triage`；仅当现象是工作台服务自身的异常堆栈/traceId/日志报错时，才用 `java-troubleshoot`。
- 明确要求维护 `knowledge_docs` 或查询已沉淀知识时走 `knowledge-governance`；SQL 模板和表目录仍由对应 SQL Skill 管理。
- 普通 Java 实现查本地 `PG_ROOT`；二开、租户定制和外部对接按执行链、task_code 与场景信号选择适配器或独立脚本，第一候选未命中或信号冲突时再扩大。当前 GitLab 搜索禁用，不作为本地无结果时的回退。
- 意图仍不唯一时，列出具体分歧及其对交付物的影响，再向用户确认；不凭模块名猜。

## 子 Skill 清单

| Skill | 职责 |
| --- | --- |
| `srm-script-platform` | Script Platform 的权威当前态读取、未保存源码 DEV 调试及显式授权后的安全保存/部署 |
| `srm-requirement-delivery` | 最小修改已有 Marmot 脚本，或按需求号拉取并实现新的纯二开产物 |
| `choerodon-task` | 猪齿鱼任务、评论、状态和附件查询；仅在用户明确确认后新增评论 |
| `java-troubleshoot` | Java 微服务日志、调用链、源码和数据的故障定位 |
| `ssrc-sql-generator` | 采购寻源域查询/修复 SQL |
| `spuc-sql-generator` | 订单履约域查询/修复 SQL |
| `srm-workbench-bug-triage` | 采购员工作台（角色工作台）bug 排障：待办/关注/超级搜索/卡片/整改，内置两段式 ES 查询、权限维度模型与库路由 |
| `archery` | 实例、库、表结构及数据的统一只读访问 |
| `knowledge-governance` | 盘古认知库的检索、沉淀、修正、归档与受控删除 |
| `gitlab-code` | 本地源码、适配器脚本、独立脚本和已知 GitLab 路径的只读定位 |

## MCP 能力边界

所有专项 Skill 复用 `zhenyun-pangu-mcp`，参数必须来自用户输入、配置或真实返回。

| 能力 | 主要工具 | Owner |
| --- | --- | --- |
| 猪齿鱼 | `choerodon_query_issue`、`choerodon_list_issue`、`choerodon_list_comments`、附件与状态工具 | `choerodon-task`；纯二开开发由 `srm-requirement-delivery` 调用 |
| 本地代码 | `search_repo`，显式使用足够深度 | `gitlab-code`；纯二开契约阻塞时由 `srm-requirement-delivery` 定向调用 |
| 脚本身份发现 | Pangu `search_adapter_scripts` / `search_standalone_scripts` | `srm-script-platform`、`gitlab-code`、`java-troubleshoot` 按缺失身份调用 |
| 平台当前源码/版本/状态 | Script Platform `adapter_get` / `independent_script_get` | `srm-script-platform`；其它 Skill 复用其路由 |
| 未保存源码 Debug 与受控保存 | Script Platform `*_debug` / `*_save` / `adapter_deploy` | `srm-script-platform`；写操作须用户明确要求 |
| 数据与表结构 | `archery_*`、`search_tables`、`get_table*` | `archery` 和领域 SQL Skill；纯二开编码被具体字段阻塞时可只读核实 |
| 日志 | `obs_sls_*`、`obs_log_*` | `java-troubleshoot` |
| 业务知识 | `search/get/save/update/delete_knowledge`、`search_pangu`、`diagnose_context` | `knowledge-governance`；专项 Skill 可只读复用 |
| SQL 模板 | `search/get/save/update/delete_sql_template`、使用统计 | `ssrc-sql-generator` / `spuc-sql-generator` |
| GitLab 精确读取 | `gitlab_list_branches`、`gitlab_list_tree`、`gitlab_get_file` | `gitlab-code`；仅 project/ref/path 已知时 |

不把知识库、历史脚本或自动索引当作实时生产事实；字段与数据由目标环境 Archery 证明。认知层写入、猪齿鱼评论、业务库写入、脚本发布或绑定都不是路由 Skill 的默认权限。

## 多 Skill 协作

| 场景 | 顺序 |
| --- | --- |
| 平台脚本查询或调试 | `srm-script-platform`；身份不完整才用 Pangu 发现，再回到 Script Platform 当前态 |
| 已有纯二开脚本小改 | `srm-requirement-delivery` 只读目标文件、最小修改并定向检查 |
| 新纯二开需求开发 | `srm-requirement-delivery` 读取需求与平台模板、实现并快速检查 |
| 任务上下文 + 故障 | 猪齿鱼只读上下文 → `java-troubleshoot` |
| 故障 + 数据修复 | `java-troubleshoot` 先定位根因 → 对应 SQL Skill 生成修复 SQL |
| 工作台待办/单据异常 + 要改数据 | `srm-workbench-bug-triage` 先定位根因 → `ssrc/spuc-sql-generator` 生成修复 SQL，交用户执行 |
| 二开实现位置 | `gitlab-code` 先定位实际脚本；确需核实契约时再定向读取本地平台入口 |

跨 Skill 传递任务号、租户、环境、模块、单据、源码引用和已验证限制，避免重复查询。最终结论必须区分事实、推断、未验证项和需要用户授权的写操作。

## 约束

- 能直接命中专项 Skill 时不要加载本 Skill。
- 不在本 Skill 内复制排障、SQL 或纯二开开发规则。
- 平台写工具已经可用，但只有用户明确要求保存/发布/部署/更新 DEV 时才能调用；本地文件或 Debug 通过不代表已经部署。
- 不得用失败调用探测禁用能力，也不得伪造不存在的工具。
