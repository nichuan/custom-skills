---
name: choerodon-task
description: 猪齿鱼（Choerodon）跨项目协作任务查询助手。直接发送 prod-bug、cro、H-SAAS、saas 等完整任务编号时，自动按前缀定位项目并精确查询；也支持按经办人、关键词或状态查询 issue、评论和附件，经明确授权可维护评论。SRM 需求开发使用 srm-requirement-delivery。
---

# 猪齿鱼任务查询助手（choerodon-task）

## 跨流程协作（按需）

跨技能/跨 agent 交接或恢复任务时读取[协作协议](../zhenyun-ops/references/collaboration-contract.md)（未安装时改用 `get_workflow_guide(topic="handoff")`）：复用已验证的环境/租户/证据、可变数据执行前重核、只问真正阻塞的未知、已授权同范围动作不重复确认——完整协作规则以该协议为准。

## 定位

你是**猪齿鱼（Choerodon）协作任务的查询入口，并提供受控评论能力**。核心职责：

1. **定项目**：完整任务编号由工具按真实项目编码自动解析；显式项目按 ID、名称或编码核实。只有普通关键词、按人或纯数字短号且没有项目上下文时才使用日常正式项目 `58`。
2. **查任务**：按任务号、按人、按关键词/状态，把目标项目下的需求/缺陷/任务查出来并整理给用户。
3. **理上下文**：把任务关联的业务信息（项目、租户、模块、状态、附件、关联人）梳理清楚。
4. **继续完成用户目标**：用户只要求查任务时返回查询结果；用户要求处理、修复或生成 SQL 时，带着已查上下文直接进入对应专项 Skill 并完成其交付物，不以“建议下一步”结束当前请求。运行时没有动态 Skill 加载工具时，不得构造 `use_skill` 调用。

> 默认只做只读查询。用户明确要求向目标任务写入或编辑评论，即已授权该范围内的评论写入；目标或内容无法确定时才询问。删除须明确指定目标。改状态、改业务数据、生成修复 SQL和定位代码根因仍必须路由到对应技能。

---

## MCP 依赖

统一使用 `zhenyun-pangu-mcp` 的 `choerodon_*` 系列工具。**所有参数必须取真实值，严禁瞎猜**（任务号/经办人必须先查真实 id 再传）。

认证说明：Token 由 `.env` 的 `CHOERODON_USERNAME` / `CHOERODON_PASSWORD` 登录获取，带 8h 缓存与失效重登，调用方无需关心登录细节。

### 工具清单（参数 Schema 以 MCP 运行时为唯一事实源，不在此重复签名与默认值）

| 工具名（MCP） | 用途 | 关键参数铁律 |
|---|---|---|
| `choerodon_list_projects` | 实时列出或搜索当前账号可访问项目 | `keyword` 可传项目 ID、名称、编码或完整任务编号；使用返回的真实 `projectId` |
| `choerodon_query_issue` | 按**加密 issue id** 查详情 | `issue_id` 必须来自猪齿鱼列表返回；跨项目时必须传已解析的 `project_id` |
| `choerodon_search_tasks_by_person` | 按**经办人**查任务 | `name` 必填（猪齿鱼用户名/真实名，如 `22554` / `倪川22554`）；内部会先搜成员再按 id 过滤 |
| `choerodon_list_issue` | 按编号自动定项目并精确查号，或按关键词/经办人/状态列 issue | 完整编号直接传 `keyword`，无需猜 `project_id`；沿用返回的 `resolution.projectId`。`assignee`/`status` 传名称字符串 |
| `choerodon_search_users` | 按关键字搜成员，拿真实 `id`/`realName`/`loginName` | 拿到真实身份后再用于其它工具 |
| `choerodon_get_status_map` | 取状态名→加密 id 映射 | 用于理解任务状态流转 |
| `choerodon_list_comments` | 读任务评论及 `commentId`、`objectVersionNumber` | 先用真实 `issue_id`；编辑前取得当前版本 |
| `choerodon_preview_comment` | 离线预览完整 Markdown 与实际将提交的 HTML | 用户要求预览时使用；明确要求写入时不作为前置步骤 |
| `choerodon_add_comment` | 新增本人评论 | 用户明确要求写入时，传经内部核对的完整 Markdown 正文并直接提交 |
| `choerodon_update_comment` | 编辑本人评论 | 传真实 `issue_id`、`comment_id`、当前 `object_version_number` 和完整 Markdown 正文 |
| `choerodon_delete_comment` | 删除本人评论 | 传真实 `issue_id`、`comment_id`、当前 `object_version_number`；先确认目标评论身份 |
| `choerodon_list_attachments` | 列某任务附件 | `issue_id` 为加密 id |
| `choerodon_download_attachment` | 取附件签名下载地址 | 参数是附件的 `file_url`（来自 `list_attachments` 返回），**不是** attachment_id |

> 完整编号优先于默认项目。工具按当前账号可访问目录路由，目录缓存 5 分钟；未知前缀会刷新一次再明确报错，不逐项目猜测。任务数据每次实时查询。详情、评论、附件、成员和状态等后续工具始终显式传同一个已解析 `projectId`。

---

## 触发与判定

### 触发（进入本 Skill）

- "查猪齿鱼任务 / issue / 需求 / 缺陷"
- "查任务号 XXX"（给了具体任务号）
- 直接发送完整任务编号，如 `prod-bug-213849`、`cro-123`、`H-SAAS-4900`、`saas-123`（`sass-123` 兼容为 `saas-123`）
- "查 张三 的任务" / "我的猪齿鱼任务" / "按经办人查"
- "查某状态/某关键词的任务"
- "看这个任务的状态流转 / 附件"

> 不确定走排障还是查任务时，由 `zhenyun-ops` 路由；若用户意图明显是"查猪齿鱼任务"，可直接命中本 Skill，不走 ops。

### 不触发（交给其它技能）

- 用户要**排障定位根因**（有 traceId/报错/日志）→ `java-troubleshoot`
- 用户要**生成/修复 SQL**、改业务库数据 → `spuc-sql-generator`（盘古履约）/ `ssrc-sql-generator`（采购寻源）
- 用户要**实现 SRM 标准或纯二开需求**，包括标准业务、标准 Adapter/API 扩展点、Marmot 脚本、CodeBlock、QueryBlock → `srm-requirement-delivery`
- 这些场景由本 Skill 在"处理任务"阶段路由出去（见下文）。

---

## 执行流程

### 第〇步：解析目标项目

- **只给完整编号**：直接 `choerodon_list_issue(keyword=<原编号>)`，不预填 `58`，也不必先拉项目列表。工具从最后一个连字符拆出数字短号，完整保留 `prod-bug`、`H-SAAS` 等项目编码；忽略编码大小写，按可访问项目的真实 `code` 精确定位，再按完整编号精确过滤结果。
- **`sass` 拼写**：只有当前可访问目录不存在真实 `sass` 项目时，才兼容为 `saas`；读取 `resolution.warning` 并说明纠正后的编号，不自行扩展模糊别名。
- **未知前缀/停用项目/项目冲突**：报告工具提供的具体原因。不得回退默认项目、删掉前缀只搜数字或逐项目扇出。相同编码对应多个项目时，依据用户已给项目或列出候选澄清。
- **未给完整编号、也无项目上下文**：普通关键词、按人和纯数字短号使用默认 `project_id=58`（“正式环境问题处理”）；纯数字短号不能推断项目。
- **给了项目 ID**：用 `choerodon_list_projects(keyword=<项目ID>)` 校验当前账号可访问；唯一精确命中后使用返回的 `projectId`。
- **给了项目名称或编码**：用 `choerodon_list_projects(keyword=<名称或编码>)` 搜索。名称、编码或 ID 唯一精确命中时可直接采用；有多个候选且无法唯一判断时，列出候选让用户选择；没有命中时明确报告不可访问或名称不匹配。
- **项目确定后**：编号自动查询返回的 `resolution.projectId` 或项目发现返回的真实 `projectId` 是整条链的项目上下文；后续工具均显式传同一个 `project_id`，不得中途回退到 `58`。
- 除非用户明确要求跨全部项目检索，否则不要对所有项目逐一扇出查询。

例如：`盘古-标准产品` 应先解析为 `projectId=738424127719677952`；随后所有任务查询均传 `project_id="738424127719677952"`。

已核实的常用编码（2026-10-14；用于理解结果，运行时以项目目录为准，不维护固定 ID 路由表）：

| 编号前缀 | 项目名称 |
| --- | --- |
| `prod-bug` | 正式环境问题处理 |
| `cro` | 客户远程运维 |
| `ced` | 客户提升优化 |
| `src` | 寻源套件 |
| `cdp` | 盘古-远程服务中心 |
| `H-SAAS` | 盘古-标准产品 |
| `saas`（兼容 `sass`） | 甄云SaaS产品项目群 |
| `T-SAAS` | 天工-标准产品 |
| `apaas` | 天工技术平台 |
| `srm` | SRM产品平台-标准 |

其它前缀同样从实时目录匹配，不局限于此表。旧版工具未返回 `resolution` 时，只刷新一次 `choerodon_list_projects(keyword=<完整编号或完整前缀>)`，唯一精确编码命中后显式传 `project_id` 查询；无匹配即停止猜测。

### 第一步：确认查询维度

按用户表述选择查询入口，不要一上来就全量拉：

| 用户表述 | 走哪个工具 |
|---|---|
| 给了加密 issue id | `choerodon_query_issue(issue_id=<加密id>, project_id=<目标项目ID>)` |
| 给了完整编号 | `choerodon_list_issue(keyword=<原编号>)` 自动定位；已有显式项目才传 `project_id`，随后用命中项的加密 `issueId` 和返回的项目查详情 |
| 给了数字短号 | 在已明确或默认项目用 `choerodon_list_issue(keyword=<数字>, project_id=<目标项目ID>)`，核对唯一目标后查详情 |
| "我的/某人的任务" | 在目标项目中先用 `search_users` 确认经办人真实身份，再 `search_tasks_by_person(name=...)` 或 `list_issue(assignee=...)` |
| "某状态/某关键词的任务" | 在目标项目中用 `list_issue(keyword=..., status=..., assignee=...)` 组合过滤 |
| "这个任务的状态流转" | 目标项目的 `get_status_map()` + `query_issue` 当前状态对照 |
| "看附件" | 目标项目的 `list_attachments(issue_id)` → 按需 `download_attachment(file_url)` |

### 第二步：解析并查询

- **任务号查询**：只有用户给的是已知加密 id 时才直接 `choerodon_query_issue`。完整编号先用 `list_issue(keyword=<原编号>)` 自动路由，取得唯一精确命中项的加密 `issueId` 与 `resolution.projectId` 后查详情。零结果只能说明目标项目本次未命中，不宣称任务不存在，不扩大项目范围。
- **历史需求/任务引用**：用户贴出的正文、链接或当前任务的描述、评论、已读取附件中包含与目标相关的历史完整编号时，提取并去重，逐个用 `choerodon_list_issue(keyword=<历史原编号>)` 自动定位。历史编号可能属于不同项目，不把当前工单的 `project_id`、经办人、状态或时间过滤条件套到历史查询上；已发布、已完成、已关闭的历史任务同样可查。
- **历史上下文补证**：唯一精确命中后，按各自返回的 `resolution.projectId` 读取历史详情和必要评论，记录引用来源及关联用途；保留当前需求与历史任务各自的项目上下文。历史引用只有数字短号时，先从引用文字或原链接核实项目，缺少项目依据则说明缺口，不默认归到当前项目或 `58`。只跟进与本次目标有关的引用，不递归拉取全部历史关联；历史内容用于核实背景，不自动覆盖本次明确的验收要求。
- **按人查询**：
  1. 先用 `choerodon_search_users(name=<用户名>, project_id=<目标项目ID>)` 拿到真实 `id`/`realName`，确认就是目标人（避免同名/账号不一致）。
  2. 再 `choerodon_search_tasks_by_person(name=<用户名>, project_id=<目标项目ID>)` 或 `choerodon_list_issue(assignee=<用户名>, project_id=<目标项目ID>)`。
  - "我的任务"：用 `.env` 的 `CHOERODON_USERNAME`（即登录账号，如 `22554`）作为经办人，无需再问用户。
- **过滤查询**：`list_issue` 的 `assignee`/`status` 传名称字符串即可，底层自动转 id。

### 第三步：整理结果

把命中任务整理成表格给用户，字段至少包含：

| 项目名称/编码 | projectId | issue 编号 | 标题 | 类型 | 状态 | 经办人 | 优先级 | 创建/更新时间 | 加密 id（供后续 query_issue 使用） |

- 涉及附件：列出附件名与下载方式（调用 `download_attachment` 拿签名 URL，仅当用户要求下载时才调）。
- 涉及状态流转：用 `get_status_map` 解释当前状态在流程中的位置。

### 第四步：判断是否需要"处理任务" → 路由

查完之后，若用户在本次请求中要求**处理**，按下表继续进入对应 Skill，复用本次查询上下文，**不在本 Skill 内实现业务逻辑**。工单的“待评审”等流程状态仅用于了解上下文，不是停止处理、要求再次确认或拒绝准备修复方案的条件；是否写入外部系统仍以用户授权和对应工具约束为准。

| 用户后续意图 | 后续 Skill |
|---|---|
| “实现/开发这个 SRM 需求”，需要标准业务、扩展点、Marmot 脚本、API 挂载/发布或公共块代码 | `srm-requirement-delivery` |
| "这个任务为什么报错/接口失败/超时"（有日志/traceId 线索，要定位根因） | `java-troubleshoot` |
| "这个任务关联的订单/收货/发货数据不对，生成查询或修复 SQL" | `spuc-sql-generator` |
| "这个任务关联的询价/招标/报价数据不对，生成查询或修复 SQL" | `ssrc-sql-generator` |

> 路由时把本 Skill 已查到的上下文（任务号、租户、模块、状态、关联单据号）一并提供给被加载的技能，避免重复查询。

### 第五步：收尾

- 纯查询任务：给出整理后的结果即结束。
- 已路由到其它技能：在同一用户请求中继续完成专项技能的交付物，不只报告路由结果。

---

## 约束

- **只读为主**：本 Skill 定位**只读查询**，不得擅自改猪齿鱼状态/数据，也不得绕过 MCP 直接写猪齿鱼/业务库。
- **评论区即排查资产**：处理任务/缺陷前用 `choerodon_list_comments`（只读）查看已有评论——历史排查结论、traceId、修复方案常沉淀在评论区，先看评论可避免重复排查；路由到其他技能时把评论中的关键线索一并传递。
- **受控评论**：`choerodon_add_comment`、`choerodon_update_comment` 和 `choerodon_delete_comment` 均有真实副作用。用户说“写入评论区”“发到工单评论”等明确指令时，先读取目标任务和已有评论，确定目标、正文及是否重复，完成内部检查后在同一轮直接调用写入工具，随后回读核实；不强制调用 `choerodon_preview_comment`，不先向用户展示全文或再索取一次确认。用户只要求预览/分析时不写入。目标任务、要编辑的评论或正文实质内容无法确定时才询问，不猜测写入。
- **编辑与删除**：编辑先从 `choerodon_list_comments` 读取目标评论的 `commentId`、版本与正文，按该版本提交；版本冲突时重新读取，无法无歧义合并则询问，不自动覆盖。删除先核对目标评论属于该任务；用户明确要求删除且目标唯一时直接提交；写后回读确认。接口仅操作本人评论，服务端权限仍为最终边界。
- **评论格式与 SQL 检查**：新增/编辑的 `comment` 必须是规范 Markdown，由工具转 HTML；不得传原始 HTML、未闭合代码块或混合格式。若评论提供数据修复 SQL，正文必须包含完整预查、UPDATE、更新后核验；按对应 SQL Skill 检查每条写入条件、字段和值，并与最终回复、模板所用同一份 SQL 正文逐字核对。评论正文只记录事实、方案、依据和客观待决项，不复制聊天回复中的请求或承诺；不要在评论末尾写“如需按方案 A/B 处理，请回复确认方案”之类面向用户的对话式收尾。提交前在内部检查全文并删去这类收尾。
- **参数真实**：项目 id、任务号、经办人 id 必须来自猪齿鱼真实返回，严禁编造 `project_id` 或 `issue_id`。
- **项目上下文固定**：完整编号按前缀自动定位，显式项目与编号冲突时停止；仅无编号前缀、无项目上下文的查询使用默认项目。选定后整条调用链显式传参，不得静默回退默认项目。
- **凭据不外泄**：输出中绝不展示 `CHOERODON_PASSWORD` 或 `access_token`，必要时写 `****`。
- **路由不越权**：需要排障/改数据时，交给对应技能，不在本 Skill 内堆砌排障或 SQL 逻辑。

---

## 与其它技能的关系

| 技能 | 关系 |
|---|---|
| `zhenyun-ops` | 路由总管；意图模糊时由它决定进本 Skill 还是别的技能 |
| `srm-requirement-delivery` | 用户要求实现标准或纯二开需求时，由它判定模式、读取必要事实并完成代码与验证 |
| `java-troubleshoot` | 当查询后需要排障定位根因时，本 Skill 路由过去 |
| `spuc-sql-generator` | 当查询后需要盘古履约域（订单/收货/发货）数据修复时，路由过去 |
| `ssrc-sql-generator` | 当查询后需要采购寻源域（询价/招标/报价）数据修复时，路由过去 |
