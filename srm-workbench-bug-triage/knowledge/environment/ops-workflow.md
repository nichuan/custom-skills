# srm-workbench 排查作业规范（动手前必读）

> `knowledge/architecture/*` 与 `knowledge/srm/*` 解决「是什么 / 为什么」，本文解决「怎么动手」：查哪个库、用什么工具、源码在哪。

## 一、数据库路由规则（强制，查询前必判）

⚠️ srm-workbench 的数据**分布在多个数据库**，且随租户/环境可能变化，**绝不能写死库名**。

**环境 → Archery 实例**（`archery_query` 的 `instance` 参数）：按 `environment` 选择——`prod` → `prod`（SAAS-SRM-PROD数据库）、`dev` → `dev`（SAAS-SRM-DEV数据库）、`test` → `test`（SAAS-SRM-TEST数据库）；aws 海外单实例 `aws`（JP-SaaS-1-Prod-RW-8.0）。同一环境内的库路由按下表，跨环境不混查。

| 表 / 前缀 | 目标库 | 说明 |
|---|---|---|
| `swbh_*` | `srm_workbench` | 角色工作台表（待办/卡片/关注/动态/权限组/错误记录） |
| `ssrc_*` / `spfm_*` / `sslm_*` / `sodr_*` / `hiam_*` 等业务源表 | `srm` | 业务主库 |
| `slod_*` | `srm_logistics_delivery` | 物流发货 |
| `spfm_rel_table_record` | `srm` | rel-table 宽表（大量工作台配置在此，见 `architecture/config-storage.md`） |

规则：

1. **先用表前缀判定，拿不准就探测，禁止猜**：用 `archery_describe_table` 在候选库逐一试，谁返回成功结构就用谁。遇「表不存在」先怀疑库判错，换库再探，不要直接断言表缺失。
2. **跨库联查 JOIN 必须带库前缀**：如 `srm_workbench.swbh_todo_definition JOIN srm.ssrc_rfx_header`。
3. **永远显式传 `db_name`**，不要依赖默认库（默认库通常为 `srm`）。

## 二、工具选型与安全红线

| 目的 | 工具 | 约束 |
|---|---|---|
| 查库 / 表结构 | `zhenyun-pangu-mcp`：`archery_query` / `archery_describe_table` / `archery_list_columns` / `archery_list_databases` | **仅只读**；写 SQL 一律生成后交由用户在 Archery 执行 |
| 查认知层（企业事实/排查经验） | `search_knowledge` / `get_knowledge` | 排查前先查，避免重复劳动；知识 id=35~41 为本 skill 同源内容 |
| 查 ES（待办 / 单据索引） | `zhenyun-pangu-mcp`：`es_search` / `es_count` / `es_get`（带 `env` 参数选 prod/dev/test） | ⛔ **两条铁律**：① 严禁删除/更新/写入 ES，只允许 `_search`/`_count`/单文档读取；② 单次查询最多 100 条（`size` 超出自截断）。**未配置该环境 ES 时降级 Kibana 人工查询**：生成 DSL 让用户在 Kibana Dev Tools 查询后贴回结果（见 SKILL.md §ES 查询降级路径） |
| 查日志（捞请求 DSL / traceId） | `obs_sls_query` / `obs_log_query`（按环境路由） | 捞 `/card-search/query` 两段 DSL 用日志 |
| 读源码 | 本地源码优先（路径见下）；本地缺失或需确认线上版本时用 `gitlab_search_code` / `gitlab_get_file`（仓库 `operation-srm/srm-workbench`） | 只读 |

> **ES 链接是唯一额外项**：Archery / 日志 / 代码检索 / 认知层的凭证均与标准 `zhenyun-pangu-mcp` 一致，**只有 ES 链接与凭证需要维护者额外补入 `zhenyun-pangu-mcp/.env`**（按环境维护 prod/dev/test 三套：prod 用 `ES_BASE_URL`/`ES_USERNAME`/`ES_PASSWORD`，dev/test 用 `ES_DEV_*`/`ES_TEST_*`，占位符见 `.env.example` 的「正式环境 ES」段）。**未配置某环境 ES 时不影响排查**：进入 Kibana 人工查询降级模式（生成 DSL 让用户查询后贴回，见 SKILL.md §ES 查询降级路径），仅当用户无 Kibana 时才用库表侧证据推理并标注证据缺失。
> **凭据纪律**：所有账号密码只存在于 MCP 自身 `.env`，严禁写入本仓库任何文件、示例或对话。

## 三、源码与资料路径

- **源码**：`<本地源码根>/srm-workbench`（Java，Spring Boot + Cola，包 `org.srm.workbench`）
  - controller：`src/main/java/org/srm/workbench/api/controller/v1`（ES 对象管理/发布/重建：`DocObjectDefinitionSiteController`）
  - 应用服务 / JobHandler：`src/main/java/org/srm/workbench/app`（超级搜索拼装 `EsSearchServiceImpl`；ES 发布 `DocObjectDefinitionServiceImpl`；文档写入 `WorkBenchDataBatchProcessServiceImpl`；安全刷数 `app/datafix/*`）
  - 消费者 / 基础设施：`src/main/java/org/srm/workbench/infra`（ES 索引操作 `infra/es/EsIndexOperation`）
- **配套资料（不随仓库分发，按需本地索取）**：
  - `srm-workbench-sql/*.sql`：工作台初始化 / 核对 SQL（实表 INSERT 来源）
  - `srm-workbench-rel-table/*.xlsx`：rel-table 宽表配置数据（sheet 名 = `table_code`）
  - 采购员工作台技术手册 / 交接文档 / 常见问题（docx / xlsx）

## 四、排查 SOP（精简版）

1. **明确问题面**：环境、租户、现象（缺失/多/错/慢）、单据类型或模块。
2. **先排除配置 / 数据问题**（优先级最高）：待办定义 `swbh_todo_definition`、字段映射、ES 对象发布状态、租户是否在启用清单 → 见 `srm/bug-triage-playbook.md`。
3. **再定位代码层**：按 `architecture/code-map.md` 的类路径读源码，判断是代码缺陷还是数据 / 配置问题。
   - 「超级搜索查不到」→ `srm/case-search-rcv-not-found.md`
   - 「待办 count 有值但无单据」→ `srm/case-todo-count-no-doc.md`
   - 「整改模块异常」→ `srm/rectify-module.md`
4. **给结论**：明确区分「配置 / 数据问题（运维或产品调整）」还是「代码 bug（改源码）」，给出修复方向。写操作一律交用户执行。
