---
name: zhenyun-ops
description: 甄云 SRM 全局智能路由中心，仅在请求跨域或无法直接命中具体子 Skill 时使用。路由需求开发、猪齿鱼查询、故障排查、采购员工作台 bug 排障、寻源/履约 SQL、数据库访问、认知库治理和代码/脚本定位；意图明确时直接使用对应子 Skill。
---

# 甄云 SRM 全局路由

本 Skill 只识别意图、安排专项 Skill 的先后顺序和共享上下文，不复制专项业务流程，也不直接执行 MCP。当前运行时没有动态 Skill 加载工具时，不得构造 `use_skill`；直接按已经选中的专项 Skill 执行，或明确告诉用户下一入口。

## 路由表

| 用户目标 | Skill |
| --- | --- |
| 修改已有 Marmot JS/SQL 的字段取值、常量、表达式或局部逻辑 | `srm-requirement-delivery` 快速修改 |
| 按猪齿鱼需求号开发新的埋点、API 挂载/API 发布、CodeBlock 或 QueryBlock | `srm-requirement-delivery` 完整需求 |
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
| 适配器脚本 | `search_adapter_scripts` → info → source | `gitlab-code`；埋点开发时由 `srm-requirement-delivery` 调用 |
| 独立脚本/API | `search_standalone_scripts` → info → source | `gitlab-code`；API 挂载、API 发布及公共块开发时由 `srm-requirement-delivery` 调用 |
| 数据与表结构 | `archery_*`、`search_tables`、`get_table*` | `archery` 和领域 SQL Skill；纯二开编码被具体字段阻塞时可只读核实 |
| 日志 | `obs_sls_*`、`obs_log_*` | `java-troubleshoot` |
| 业务知识 | `search/get/save/update/delete_knowledge`、`search_pangu`、`diagnose_context` | `knowledge-governance`；专项 Skill 可只读复用 |
| SQL 模板 | `search/get/save/update/delete_sql_template`、使用统计 | `ssrc-sql-generator` / `spuc-sql-generator` |
| GitLab 精确读取 | `gitlab_list_branches`、`gitlab_list_tree`、`gitlab_get_file` | `gitlab-code`；仅 project/ref/path 已知时 |

不把知识库、历史脚本或自动索引当作实时生产事实；字段与数据由目标环境 Archery 证明。认知层写入、猪齿鱼评论、业务库写入、脚本发布或绑定都不是路由 Skill 的默认权限。

## 多 Skill 协作

| 场景 | 顺序 |
| --- | --- |
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
- 当前没有发布/绑定 MCP；不得以本地 bundle 代表已经部署。
- 不得用失败调用探测禁用能力，也不得伪造不存在的工具。
