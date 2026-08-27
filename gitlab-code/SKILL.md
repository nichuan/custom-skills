---
name: gitlab-code
description: GitLab 代码检索助手。仅在用户要「找代码 / 读源码 / 定位某个类/方法/文件属于哪个仓库分支 / 从 GitLab 读取完整文件」时使用。明确 GitLab 应该怎么找：先看 .env 的 PG_ROOT（本地优先）与 GITLAB_SEARCH_ROOT_GROUP（搜索范围），用 group 限定而非关键词瞎搜，忽略 op-deliver-* 快照仓库，锁定标准库/二开库与正确分支后用 gitlab_get_file 读全文。不生成 SQL、不排障、不改业务代码。
---

# GitLab 代码检索助手

## 职责边界

本 Skill 只负责**「在 GitLab / 本地源码中定位并读取代码」**。它回答的是：
- 某个类 / DTO / 接口 / 方法在**哪个仓库、哪个分支、哪个路径**？
- 如何**读取该文件的完整内容**？

它**不做**：故障根因分析（交给 `java-troubleshoot`）、SQL 生成（交给 `ssrc`/`spuc-sql-generator`）、任务查询（交给 `choerodon-task`）。

本 Skill 只描述"怎么做"，工具的**真实参数 Schema 以 MCP 为唯一事实源**，严禁在本文件猜测/重复定义。

---

## 核心铁律（踩坑总结，必须严格遵守）

> 本次建设背景：之前反复用 `gitlab_search_projects` 关键词搜索，返回全站结果后**自作主张选了 `op-deliver-1.29/srm-source`**，无视 `.env` 的 `GITLAB_SEARCH_ROOT_GROUP=operation-srm`，导致查错库、查不到目标类。以下规则用于杜绝此类错误。

### 铁律 1：先看 .env，不要凭空猜路径

MCP 从 `.env` 读取两个关键配置（路径以 `.env` 实际值为准）：

| 配置项 | 含义 | 用途 |
|--------|------|------|
| `PG_ROOT` | 本地源码根目录（如 `/Users/chuanni/workspace/project/srm/standard`） | **本地检索优先**，用 `search_repo` 直接搜本地已拉取的完整源码树 |
| `GITLAB_SEARCH_ROOT_GROUP` | GitLab 搜索范围限定的 group（如 `operation-srm`） | **GitLab 检索的范围边界**，标准库/二开库都在此 group 下 |

> **本地优先原则**：只要 `.env` 的 `PG_ROOT` 已拉取了目标仓库的源码，`search_repo(keyword, mode="content"/"filename")` 是最快最稳的路径，不必走 GitLab。本次 `AiApproveDTO` 正是用 `search_repo` 在 `PG_ROOT/srm-source/.../org/srm/source/share/api/dto/` 下成功命中。

### 铁律 2：`gitlab_search_projects` 不可信，必须按 group 限定

`gitlab_search_projects`（底层 `list_projects`）**只用关键词做全站文本搜索，不消费 `GITLAB_SEARCH_ROOT_GROUP`**，返回结果含全站无关仓库（如 `op-deliver-1.29/srm-source`、`op-deliver-1.28/srm-source` 等快照库）。

**因此**：
- ❌ 不要用 `gitlab_search_projects` 的"第一个结果"当目标库（这正是之前选错 `op-deliver-1.29` 的根因）。
- ✅ 目标库必须从 `GITLAB_SEARCH_ROOT_GROUP` 对应的 group 中确定，且 project_id 用 `group/project` 形式（如 `operation-srm/srm-source`）。
- 若确需列举 group 下项目，用 `gitlab_list_tree` / 已知命名规律推断，**不要依赖 `gitlab_search_projects` 的全站返回**。

### 铁律 3：仓库命名与范围规则（来自 java-troubleshoot 既有知识，重复强调）

| 类型 | project_id 形式 | 示例 | 备注 |
|------|----------------|------|------|
| **标准库** | `operation-srm/srm-{模块}` | `operation-srm/srm-source` | 主源码，包路径 `org.srm.{模块}...` |
| **二开库** | `operation-srm-{租户}/srm-{模块}-{租户}` | `operation-srm-bluesail/srm-source-bluesail` | 客户定制，包路径带租户后缀 |
| **快照库** | `op-deliver-*/srm-*` | `op-deliver-1.29/srm-source` | ⚠️ **一律忽略**，不是检索目标 |

> 注意：`operation-srm/srm-source`（标准库）若在 GitLab 上 404，说明该路径写法/可见性有问题，应回退到 `PG_ROOT` 本地检索，或请用户确认正确的 group/project 命名，**禁止擅自切换到 `op-deliver-*` 快照库**。

### 铁律 4：分支规则（仓库名/分支名以 MCP 实时返回为准，不硬编码）

- 标准库：用最新 `x-y-z-hotfix` 分支（`gitlab_list_branches` 取 `recommended_ref`）；`master` 往往无 `share` 等完整源码包。
- 二开库：用 `release` 分支。
- 读取前**先用 `gitlab_list_branches` 确认真实分支名**，不要用想当然的 `master`（之前在 `op-deliver-1.29/srm-source` 的 `master` 下找不到 `share` 包，正是分支选错）。

### 铁律 5：GitLab 代码搜索接口当前不可用，走"列举 + 读取"

当前自托管 GitLab（14.1.0）**未开启全局代码搜索索引**，且 `repository/search` 接口亦 404。因此：

- ❌ `gitlab_search_code` 当前会失败（已内置降级仍失败），**不要反复调用**。
- ✅ 正确路径：`gitlab_list_tree(project_id, path, ref, recursive)` 逐层定位目录 → `gitlab_get_file(project_id, path, ref)` 读取完整文件。
- 已知类名/包路径时，可直接拼 `gitlab_get_file` 的标准路径（如 `src/main/java/org/srm/source/share/api/dto/AiApproveDTO.java`），失败再退回 `list_tree` 探查。

---

## 检索 SOP（按序执行）

```text
用户要找代码（类名 / 方法 / 文件路径 / "某功能在哪个类"）
   ↓
① 确认 .env 配置（PG_ROOT / GITLAB_SEARCH_ROOT_GROUP）
   ↓
② 本地优先：search_repo(keyword, mode=content/filename)
   ├─ 命中 → 直接给路径 + 用 read_file / gitlab_get_file 读全文
   └─ 未命中或需 GitLab 特定分支 → 进入 ③
   ↓
③ GitLab 检索（严格在 GITLAB_SEARCH_ROOT_GROUP 内）
   ├─ 先 gitlab_list_branches 确认分支（标准库 hotfix / 二开库 release）
   ├─ gitlab_list_tree 逐层定位目录（project_id 用 group/project 形式）
   └─ gitlab_get_file 读取完整文件
   ↓
④ 输出：完整 path_with_namespace@branch:file:line + 标准/二开来源
```

### 决策要点

1. **本地已拉取 → 必走 `search_repo`**，这是最快路径，不要绕去 GitLab。
2. **GitLab 目标库必须由 `GITLAB_SEARCH_ROOT_GROUP` 推导**，绝不接受 `gitlab_search_projects` 的全站快照库结果。
3. **分支先用 `gitlab_list_branches` 探明**，避免 `master` 下源码不全导致"找不到"。
4. **`gitlab_search_code` 当前平台不可用**，别浪费调用，直接 `list_tree + get_file`。

---

## 工具失败策略（禁止"失败→相同参数→再调"）

| 返回 | 含义 | 处理 |
|------|------|------|
| 401 | 凭据缺失 | 提示检查 `.env` 的 `GITLAB_TOKEN`，不让用户贴 Token |
| 403 | 权限不足 | 提示申请项目权限；可见性问题时回退本地 `search_repo` |
| 404（project 不存在） | project_id 写错或不在该 group | 用 `group/project` 正确形式；确认 `GITLAB_SEARCH_ROOT_GROUP` 下真实命名 |
| 404（file 不存在） | 路径/分支错 | 先 `gitlab_list_branches` 确认真实分支，再 `gitlab_list_tree` 探查真实路径 |
| empty / 0 命中（search_repo） | 本地未拉取该仓 | 回退 GitLab `list_tree + get_file` |
| `gitlab_search_code` 报错 | 平台未开搜索 | 走 `list_tree + get_file`，不再调 search_code |

---

## 输出规范

读取/定位到代码后，输出：

```
## 代码定位结果
- 来源：标准库 / 二开库（租户 XXX）
- 仓库：path_with_namespace
- 分支：<branch>
- 路径：src/.../ClassName.java
- 定位方式：本地 search_repo / GitLab list_tree+get_file

## 关键内容
[类结构 / 字段 / 方法摘要，需引用时标注 file:line]
```

- 报告中必须标注完整 `path_with_namespace@branch:file:line` 并标明标准/二开来源。
- 若同时有本地 `PG_ROOT` 版本与 GitLab 版本，说明两者分支差异，提示以哪份为准（通常本地 `standard` 为开发基准）。

---

## 安全检查

- 凭据只由 MCP 从环境变量读取；任何输出不得展示 Token / AccessKey / 密码，必要时写为 `****`。
- 只读检索，不修改业务代码、不执行写操作。
- 不把生产数据库连接信息写入本 Skill/报告。
