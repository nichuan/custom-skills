# SRM 代码库拓扑（标准库 + 租户二开）

> 企业事实层。Agent 据此收敛代码搜索范围。当前 GitLab 项目/代码搜索未开启，普通检索必须使用本地 `PG_ROOT/search_repo`；只有 project/ref/path 已知时才使用 GitLab 精确读取能力。

## 1. 标准业务代码：单一 Group

- 标准逻辑统一在 `operation-srm` 这一个 Group 下。
- 命名规范：`operation-srm/srm-{模块}`，例如寻源标准库 `operation-srm/srm-source`。
- 任何"标准逻辑是怎么写的"问题，一律先在 `operation-srm/srm-{模块}` 中定位，不要去别的 namespace。

## 2. 租户二开代码（Git 仓库方式，较老）

- 形式：`operation-srm-{租户}` 下的 `srm-{模块}-{租户}`（以租户代号作为仓库后缀）。
- 例：奥克斯寻源二开 `operation-srm-aux/srm-source-aux`。
- 同构示例：`operation-srm-hytera/srm-source-hytera`、`operation-srm-ddmc/srm-source-ddmc`、`operation-srm-luxshareic/srm-source-lsrt`。
- **注意**：个别租户后缀与 group 后缀不一致，不要凭租户名硬拼。本地 PG_ROOT 未包含目标二开仓时，应报告覆盖范围，不能通过当前禁用的 GitLab 搜索猜测仓库。
- 二开是"有的租户有、有的租户无"：已知租户时，必须先探测该租户是否存在对应二开服务；存在则实际执行逻辑可能被二开覆盖/增强，必须一并排查。

## 3. 必须排除的噪声 namespace（命中即忽略，除非用户明确点名）

| namespace 模式 | 含义 | 处理 |
|---|---|---|
| `op-deliver-1.28` / `op-deliver-1.29` / `op-deliver-*` | 版本交付快照仓库 | 忽略，不作为排障依据 |
| `*-web` / 前端仓库 | 前端工程 | 后端排障忽略 |
| 个人 namespace、`test-*`、归档仓库 | 个人/试验仓库 | 忽略 |

## 4. 分支选择规则（用户未指定分支时）

| 仓库类型 | 使用分支 | 说明 |
|---|---|---|
| 标准库 `operation-srm/srm-{模块}` | 最新的 `{大}-{中}-{小}-hotfix` 正式分支 | 形如 `1-69-0-hotfix`；按版本号**数值**比较取最大 |
| 二开库 `operation-srm-{租户}/srm-{模块}-{租户}` | `release` | 二开服务统一以 `release` 分支为准 |

- 版本号比较必须数值比较（非字符串）：`1-100-0-hotfix` > `1-99-0-hotfix`。
- 仅在 project_id 已由用户或可靠证据明确提供时，用 `gitlab_list_branches(project_id, per_page)` 确认分支。
- 查二开库 `release` 分支时**不要带 `search`**（过滤会误判 release 不存在）。
- `truncated: true` 说明分支被截断，需调大 `max_branches` 或改用 `search`。
- 若 `recommended_ref` 为空或与预期不符，**先询问用户当前正式版本号**，不要默认回退到 `master`/`develop`。
- 诊断报告中必须写明实际使用的分支；回退分支需显式标注"未能确认最新 hotfix 分支，实际读取分支为 xxx"。
