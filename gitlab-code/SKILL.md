---
name: gitlab-code
description: 甄云代码与数据库脚本定位助手。用户要找类、方法、文件、二开逻辑、适配器脚本或外部接口实现时使用。二开、租户定制和外部对接先定位适配器/独立脚本，只有契约核实或用户明确要求时才定向查标准代码；普通代码只用本地 PG_ROOT/search_repo。GitLab 搜索当前禁用，仅允许已知 project_id/ref/path 的精确读取。不排障、不生成 SQL、不修改业务代码。
---

# 代码与脚本定位

## 跨流程协作（按需）

单项任务沿用本技能最短路径。仅在跨技能/跨 agent 交接或恢复任务时读取[协作协议](../zhenyun-ops/references/collaboration-contract.md)；若该文件未安装，使用 `get_workflow_guide(topic="handoff")`，无需为此额外安装技能。复用已有环境、租户、证据引用与验证结果；可变数据执行前重核，知识库命中不等于实时事实。用户已要求后续实现/修复时继续完成，只询问真正阻塞的未知信息。知识沉淀先准备可审阅内容，已明确授权的同范围动作不重复确认。

## 边界

本 Skill 负责回答实现位于哪个本地文件或数据库脚本，并读取必要上下文。

- 故障根因分析交给 `java-troubleshoot`。
- 数据查询或修复 SQL 交给对应 SQL Skill。
- 工具参数以 MCP Schema 为准；本文件只定义选择规则。

## 先判断实现载体

| 请求特征 | 首选证据源 | 补充证据源 |
|---|---|---|
| Java 类、方法、DTO、配置、异常文本 | 本地 `search_repo` | 已知路径时精确读取 GitLab 文件 |
| 二开、客户定制、租户专属逻辑 | 数据库适配器/独立脚本 | 本地代码用于确认平台入口 |
| ERP/WMS/OA/SAP 等外部系统对接 | 数据库脚本 | 本地代码用于确认调用框架 |
| 回调、Webhook、推送、同步、报文、字段映射、签名 | 数据库脚本 | 日志或本地入口代码 |
| 标准能力与定制逻辑混合 | 先定位实际执行的数据库脚本 | 仅在契约核实需要时定向读取本地入口 |

本地 Java 没有命中，不代表功能没有实现；定制逻辑可能全部存放在脚本中。

若本 Skill 是由故障排查转入：只有执行链已确认没有适配器或 API 前/后置挂载调用，才把问题当标准 Bug 并默认检索本地标准仓库。二开 Bug 的标准代码检索必须放在脚本之后，且仅用于核实脚本入参、返回结构、平台入口或默认行为，或响应用户的明确检索要求。实现载体仍为未知时，应返回 `java-troubleshoot` 补证据或追问，不得宽泛扫描本地仓库。

## GitLab 能力硬边界

当前环境没有可用的 GitLab 项目搜索和代码搜索能力：

- 禁止调用 `gitlab_search_projects`、`gitlab_search_code`。
- 禁止用一次失败调用探测能力。
- 本地检索无结果时不得自动回退 GitLab 搜索。
- 不得通过遍历大量 GitLab 项目或目录变相实现全局搜索。
- 用户明确要求远端搜索时，直接说明当前能力不可用并给出已检索的本地范围。

GitLab 只保留精确读取：当 `project_id`、`ref`、`path` 已由用户或可靠证据明确提供时，
可使用 `gitlab_list_branches`、`gitlab_list_tree`、`gitlab_get_file` 核实指定内容。

## 普通代码检索

1. 使用 `search_repo` 在 `.env` 的 `PG_ROOT` 搜索文件名或内容。
2. 根据服务、模块和包路径缩小范围，忽略 `op-deliver-*`、构建产物和快照仓库。
3. 命中后读取足够上下文，不能只凭单行片段下结论。
4. 无结果时报告关键词、PG_ROOT 和检索范围；不要转向不可用的 GitLab 搜索。

如果 `PG_ROOT` 不存在或未包含目标仓库，应明确指出本地源码不完整。

## 二开与外部对接脚本

出现二开、定制、租户专属、适配器、独立脚本、外部接口、回调、推送、同步、
报文、字段转换、接口地址、签名或鉴权等信号时，先判断脚本类型，再执行对应只读链路。

适配器、标准 API 前后置、埋点脚本：

```text
search_adapter_scripts
  → get_adapter_script_info
  → search_adapter_script_source
  → get_adapter_script_source(start_line, end_line)
  → 确需全局分析时才 full=true
```

独立 API 或其它独立二开脚本：

```text
search_standalone_scripts
  → get_standalone_script_info
  → search_standalone_script_source
  → get_standalone_script_source(start_line, end_line)
  → 确需全局分析时才 full=true
```

要求：

- 从请求提取租户、运行服务、业务关键词和接口名称，已知信息不重复询问。
- `search_adapter_scripts` / `search_standalone_scripts` 先查元信息，不直接读取所有脚本正文。
- 定位字段、函数、URL 或报文时，先搜索正文再读取局部行号。
- 排障为获取日志关键字时，只从脚本源码提取真实、稳定的日志字面量；不猜测异常文案或近义词。
- MCP 返回的 `source` 已在服务端解码；不要查询、展示或让 LLM 处理 Base64。
- 命中启用脚本时，以脚本实际逻辑为准；确需核实契约或平台行为时才定向查标准代码。
- 适配器结果来自 `sada_adaptor_task_*`；独立脚本结果来自 MCP 已实现的 standalone-script 数据源。两类结果必须按工具返回标识，不得混写或自行猜表。

## 输出

报告实际证据来源：

- 本地代码：绝对/仓库相对路径及行号。
- 精确 GitLab 文件：`path_with_namespace@ref:path:line`，并说明该位置来自已知路径而非搜索。
- 数据库脚本：租户、运行服务、`script_id`、`task_code`、版本及关键源码行号。
- 未命中：列出已检索的数据源和边界，不把“未找到”写成“不存在”。

全程只读，不输出凭据、完整 Base64 或无关的大段源码。
