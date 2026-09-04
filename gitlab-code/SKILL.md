---
name: gitlab-code
description: 甄云代码与数据库脚本定位助手。用户要找类、方法、文件、二开逻辑、适配器脚本或外部接口实现时使用。普通代码只用本地 PG_ROOT/search_repo 检索；当前 GitLab 项目与代码搜索未开启，禁止尝试 gitlab_search_* 或在本地无结果后远端回退。二开、租户定制、ERP/WMS/OA 对接、回调、推送、同步、报文和字段映射优先检索适配器/独立脚本。仅在已知 project_id、ref、path 时使用 GitLab 精确读取能力。不排障、不生成 SQL、不修改业务代码。
---

# 代码与脚本定位

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
| 标准能力与定制逻辑混合 | 本地入口 + 数据库脚本 | 汇总实际调用链 |

本地 Java 没有命中，不代表功能没有实现；定制逻辑可能全部存放在脚本中。

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
报文、字段转换、接口地址、签名或鉴权等信号时，主动执行：

```text
search_adapter_scripts
  → get_adapter_script_info
  → search_adapter_script_source
  → get_adapter_script_source(start_line, end_line)
  → 确需全局分析时才 full=true
```

要求：

- 从请求提取租户、运行服务、业务关键词和接口名称，已知信息不重复询问。
- `search_adapter_scripts` 先查元信息，不直接读取所有脚本正文。
- 定位字段、函数、URL 或报文时，先搜索正文再读取局部行号。
- MCP 返回的 `source` 已在服务端解码；不要查询、展示或让 LLM 处理 Base64。
- 命中启用脚本时，以脚本实际逻辑为准，标准代码只作平台入口和默认行为对照。
- 现有事实只确认 `sada_adaptor_task_*` 适配器存储；若“独立脚本”未命中，不得编造其它表，应报告当前已覆盖的脚本来源。

## 输出

报告实际证据来源：

- 本地代码：绝对/仓库相对路径及行号。
- 精确 GitLab 文件：`path_with_namespace@ref:path:line`，并说明该位置来自已知路径而非搜索。
- 数据库脚本：租户、运行服务、`script_id`、`task_code`、版本及关键源码行号。
- 未命中：列出已检索的数据源和边界，不把“未找到”写成“不存在”。

全程只读，不输出凭据、完整 Base64 或无关的大段源码。
