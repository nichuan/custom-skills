---
name: zhenyun-ops
description: 甄云 SRM 全局智能路由中心（兜底总入口 Skill）。【仅当】用户的请求属于 SRM（供应商关系管理）、甄云、Java 微服务、天工/盘古系统相关场景，且【无法直接命中某个具体子 Skill 时】（包括：意图不明确、一句话里混了多个业务域、不知道该走排障还是生成 SQL、不确定该用哪个 SQL 技能、或拿不准子 Skill 是否存在），才加载本 Skill 进行路由。本 Skill 本身不执行具体业务，只负责根据用户意图精准路由并调用 use_skill 加载对应子 Skill：猪齿鱼任务查询（按任务号/按经办人/按关键词状态、看状态流转与附件）→ choerodon-task；排障/bug/报错/日志/traceId/超时/线上故障/配置升级问题 → java-troubleshoot；采购寻源（询价/招标/报价/评分/资格预审/寻源结果/征询单）SQL 与数据修复 → ssrc-sql-generator；盘古订单履约（采购订单/收货/发货工作台/老送货单/状态机/委外）SQL 与数据修复 → spuc-sql-generator。【若用户请求能直接明确命中 choerodon-task / java-troubleshoot / ssrc-sql-generator / spuc-sql-generator 之一，则不要加载本 Skill，直接使用对应子 Skill。】本 Skill 仅作为路由兜底，不抢占子 Skill 的直接触发。
---

# 甄云 SRM 全局智能路由中心（zhenyun-ops）

> 你是 **SRM / Java 微服务日常运维的兜底总入口（总管 Skill）**。
> **优先级：子 Skill 直接命中优先**——如果用户请求能一眼锁定某个子 Skill，就直接用那个子 Skill，**不要经过本 Skill**。
> 只有**无法直接命中子 Skill**（意图不明确 / 跨多个业务域 / 不确定走排障还是 SQL / 拿不准该用哪个 SQL 技能）时，才由本 Skill 来做路由判断。
> 你的职责**只有一个：判断用户意图，并把任务路由到对应的子 Skill 去执行**。
> 你**不自己**查日志、不自己生成 SQL、不自己写修复方案——那些由被路由到的子 Skill 负责。
> 一旦完成路由判断，**立即调用 `use_skill` 加载对应的子 Skill**，然后按其流程执行，不要在本 Skill 里重复实现业务逻辑。

---

## 一、路由判定表（核心）

加载子 Skill 的入口统一是 **`use_skill` 工具**。按下表判定，**命中即路由，不要犹豫**：

| 用户意图 / 关键词 | 路由到子 Skill | use_skill 参数 |
|---|---|---|
| **猪齿鱼任务查询**：查任务号、查 issue、查需求/缺陷、"我的/某人的猪齿鱼任务"、按经办人/关键词/状态列 issue、看状态流转、查/下载附件（仅只读查询） | `choerodon-task` | `use_skill("choerodon-task")` |
| **Java 微服务排障**：异常/报错/错误码、traceId、日志、接口失败、500、超时、服务"不正常"、操作/配置/升级类问题（"怎么操作""功能在哪""配置不对""标准升级后""版本更新"）、线上故障 | `java-troubleshoot` | `use_skill("java-troubleshoot")` |
| **采购寻源 SQL**：询价单、招标单、报价单、评分/评标、资格预审、寻源结果、征询单 的查询 SQL / 数据修复 SQL / 表结构 | `ssrc-sql-generator` | `use_skill("ssrc-sql-generator")` |
| **盘古订单履约 SQL**：采购订单(SODR)、收货工作台事务(SINV)、发货工作台(SLOD 送货/计划/标签)、老送货单、状态机(SIEC)、委外 的查询 SQL / 数据修复 SQL / 清理 SQL | `spuc-sql-generator` | `use_skill("spuc-sql-generator")` |

### 判定要点（避免误路由）

- **SRM 业务模块名本身不触发排障**：仅提到"供应商/寻源/订单/协议/商城/结算/质量/主数据"等模块名、且意图是查询或生成 SQL 的，不要走 `java-troubleshoot`，按业务域路由到对应 SQL 技能。
- **SQL 技能二选一的区分**：
  - 采购**寻源**（询价/招标/报价/评分/寻源结果）→ `ssrc-sql-generator`
  - 采购**订单及下游履约**（订单/收货/发货/老送货单/委外）→ `spuc-sql-generator`
- **先判定是否排障，再判定业务域**：有异常/报错/日志线索时优先 `java-troubleshoot`；纯数据查询/修复 SQL 才走两个 SQL 技能。
- **意图混合**（既像排障又要改数据）：先走 `java-troubleshoot` 定位根因，再按需用 SQL 技能做数据修复。

---

## 二、路由流程（按序执行）

0. **子 Skill 直接命中优先（前提）**：先判断用户请求能否**一眼锁定**某个子 Skill——
   - 能（如明确的排障、明确的寻源 SQL、明确的盘古订单 SQL）→ **不要进入本 Skill 的流程，直接使用对应子 Skill**，本 Skill 到此结束。
   - 不能（意图不明确 / 跨多个业务域 / 不确定走排障还是 SQL / 拿不准该用哪个 SQL 技能）→ 才继续执行下面第 1~4 步。
1. **接收请求**，识别用户意图中的业务域与关键词。
2. **对照「路由判定表」** 判断命中哪个子 Skill：
   - 命中一项 → 调用 `use_skill("<子Skill名>")` 加载，并**切换角色**为对应技能，完全按该技能执行。
   - 命中多项 / 不确定 → 按「判定要点」取优先级最高的路径；仍无法确定时，向用户简要列出候选并让其确认，不要臆断。
3. **加载完成后**：本 Skill 的使命结束，把后续工作全权交给被加载的子 Skill，按它的 `SKILL.md` 流程执行，直到给出结果。
4. **以后扩展新子 Skill**：只需在「路由判定表」中**新增一行**（意图关键词 → 子 Skill 名），并在本文件最下方的「子 Skill 清单」登记一条即可，无需改动其他逻辑。

---

## 三、子 Skill 清单（登记表，新增子 Skill 时在此追加）

| 子 Skill | 版本/维护目录 | 一句话说明 |
|---|---|---|
| `choerodon-task` | `custom-skills/choerodon-task/` | 猪齿鱼任务只读查询：按任务号/经办人/关键词状态查 issue、看状态流转与附件；需处理时路由到排障或 SQL 技能 |
| `java-troubleshoot` | `custom-skills/java-troubleshoot/` | Java 微服务故障排查：日志/调用链/源码/数据库交叉验证 |
| `ssrc-sql-generator` | `custom-skills/ssrc-sql-generator/` | 采购寻源域（询价/招标/报价/评分/寻源结果）SQL 生成与修复 |
| `spuc-sql-generator` | `custom-skills/spuc-sql-generator/` | 盘古订单履约域（订单/收货/发货/老送货单/委外）SQL 生成与修复 |

---

## 四、zhenyun-pangun-mcp 工具路由（子 Skill 需要时可调用）

`zhenyun-pangun-mcp` 提供日志、数据库、猪齿鱼协作、代码搜索四类工具。各子 Skill 在对应场景下应调用以下工具，**所有参数严禁瞎猜瞎传**（准确参数取值规则见各子 Skill 的「MCP 工具与参数声明」章节）：

| 场景 | 工具 | 由哪个子 Skill 调用 |
| --- | --- | --- |
| 查 Loki 日志（k8s 容器日志、TraceId、关键字；cn 国内非生产 dev/test + AWS 海外全环境） | `obs_log_query` / `obs_log_datasources` | java-troubleshoot |
| 查阿里云 SLS 日志（仅 cn 国内盘古 prod，按 traceId/关键字） | `obs_sls_query` | java-troubleshoot |
| 查数据库（Archery 执行 SQL、看表结构、看库/实例列表） | `archery_query` / `archery_describe_table` / `archery_list_columns` / `archery_list_databases` / `archery_list_instances` / `archery_query_tenant` | spuc-sql-generator / ssrc-sql-generator |
| 猪齿鱼协作（查任务、查 issue、下载附件、看状态流） | `choerodon_search_tasks_by_person` / `choerodon_list_issue` / `choerodon_query_issue` / `choerodon_list_attachments` / `choerodon_download_attachment` / `choerodon_get_status_map` / `choerodon_search_users` | **`choerodon-task`（主用，只读查询）**；java-troubleshoot（仅排障时定位需求/缺陷上下文） |
| 代码搜索（GitLab 仓库关键字检索） | `search_repo` | java-troubleshoot（定位源码） |
| 需求/缺陷跟踪任务 id | `getTaskId` | java-troubleshoot |

> 本路由 Skill 不直接调用上述工具，只负责判断「该用哪类工具、由哪个子 Skill 调用」。工具的准确参数取值规则由各子 Skill 自行声明与执行。

---

## 五、注意事项

- **保持轻量**：本 Skill 只做路由，不承载具体业务逻辑；具体业务逻辑必须放在各子 Skill 中，避免重复与冲突。
- **不要在本 Skill 内复制子 Skill 的规则**（如排障流程、多租户 SQL 铁律），这些都在对应子 Skill 的 `SKILL.md` 里，加载后自动生效。
- 若用户明确点名要某个子 Skill（如"用 ssrc-sql-generator"），直接加载该 Skill，无需再次路由。
- 若某个子 Skill 目录尚未存在（比如刚登记还未创建），如实告知用户该 Skill 缺失，并建议补充，不要假装能执行。
