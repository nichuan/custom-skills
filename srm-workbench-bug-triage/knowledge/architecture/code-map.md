# 关键代码定位速查

包名前缀：`org.srm.workbench`。
⚠️ **源码位置**：以 MCP 的 `PG_ROOT` 配置和 `search_repo` 实际返回为准。**排查时优先搜索本地源码**（如 `src/main/java/org/srm/workbench` 下的 `api/app/domain/infra`）。当前 GitLab 项目/代码搜索未启用；只有从用户或可靠证据获得真实 `project_id/ref/path` 后，才可用 `gitlab_list_branches` / `gitlab_list_tree` / `gitlab_get_file` 精确读取。

## Controller（界面入口）
- 超级查询：`api/controller/v1/DocDataSearchController`
- ES 数据初始化：`api/controller/v1/ESDataInitializerController`
- **ES 对象管理 / 发布 / 重建索引（超级搜索字段接入入口）**：`api/controller/v1/DocObjectDefinitionSiteController`
  - `PUT /doc-object-definitions/doc-publish`（:118-126）→ 调 `DocObjectDefinitionServiceImpl.publish` → `doEsPublish`（异步）→ `esIndexService.batchCreateIndex` → 对已发布单据对象走 `updateMapping`（增量 `putMapping`，只更新 mapping 结构，不回填数据）
  - `PUT /doc-object-definitions/reindex`（:128-171）→ `rebuild=true` 会先 `deleteIndex` 再 `initIndex` **全量重建索引（删索引、搜索窗口不可用）**；生产十几亿数据**严禁**用 rebuild
- 其余工作台查询接口：`api/controller/v1/*WorkBench*.java`

## 消费程序（infra.consumer）
- 单据消费：`infra/consumer/WorkBenchDataProcessConsumer`
- 工作流消费：`infra/consumer/WorkFlowDataProcessConsumer`
- 单据权限变更：`app/event/UserAuthorityChangeConsumer`
- 物流权限变更：`app/event/LogisticsRolePermissionConsumer`

## JobHandler（补偿/清除/定时，app.jobhandler）
- 单据消费补偿：`DocConsumerCompensateHandle`
- 待办消费补偿：`TodoConsumerCompensateHandle`
- 待办消费清除：`TodoConsumerEliminateHandle`
- 关注消费补偿：`ActionConsumerCompensateHandle`
- 关注消费清除：`ActionConsumerEliminateHandle`
- 工作流补偿：`WorkFlowConsumerCompensateHandle`
- 行字段冗余：`LineFieldCompensateHandler`
- 用户权限组变更：`UserAccessGroupChangeJobHandler`
- ES 权限更新：`EsDocumentAccessChangeJobHandler`
- 物流角色权限补偿：`LogisticsRolePermissionCompensateHandler`

## 领域/应用服务（超级搜索字段配置相关）
- **ES 文档搜索字段拼装（查询侧）**：`app/service/impl/EsSearchServiceImpl`
  - `buildDocSearchRequest` / `buildDraftTotalSearchRequest` / `buildDraftDocSearchRequest`：都用 `searchFieldDTOMap.get(combineCode)` 取 `swbh_doc_type_search_filed` 配置的字段，在 `docNum` 非空时拼成 `multiMatch` 多字段任一命中（三处一致，约 :343-361）
- **ES 对象发布（更新索引结构）**：`app/service/impl/DocObjectDefinitionServiceImpl`
  - `publish(strategy, level, list)`（:113-162）：把 `swbh_doc_object_rel_field` 中 `index_flag=1` 且 `UNPUBLISHED` 的字段置 `PENDING`，异步调 `doEsPublish`
  - `doEsPublish(strategy)`（:165-177，`@Async`）：`CURRENT` 立即 `batchCreateIndex(PENDING)`；`DELAY` 排到**次日凌晨 1 点**才执行
- **ES 索引创建/更新（mapping）**：`infra/es/service/impl/EsIndexServiceImpl`
  - `createOrUpdateEsIndex`（:79-92）：`PENDING`/初始化 → `createOneDocObjectIndex`（新建）；`PUBLISHED` → `updateIndexMapping`（增量 `putMapping`）
  - `buildEsField`（:319-356）：遍历 `swbh_doc_object_rel_field` 按 `dataType` 生成 ES mapping（varchar → TEXT/IK 分词或 KEYWORD），并回填 `dataType`/`sortedFlag`
- **ES 索引操作（底层 putMapping / updateByQuery）**：`infra/es/EsIndexOperation`
  - `updateMapping`（:113-129）：执行 `PutMappingRequest`，增量加字段定义，**不删索引、不碰数据**（十几亿数据安全）
- **ES 文档构建 / 写入（含历史重灌）**：`app/service/impl/WorkBenchDataBatchProcessServiceImpl`
  - `updateESData`（:1093+）：按 `getIndexFieldsByCombineCode`（`swbh_doc_object_rel_field`）+ `getIndexField`（`swbh_doc_type_index_filed`）筛选字段写入 ES 文档
  - `insertESDimension`：权限维度字段写入
- **安全刷新历史数据（DataFix，不删索引）**：`app/datafix/*`
  - `EsSourceReMappingByDocNum`：用 `UpdateByQueryRequest`（`setSlices(2)`/`setScroll(15min)`/`setBatchSize(3000)`/`setConflicts("proceed")`/`setRefresh(true)`，:38-43）按查询原地回写 `ctx._source = ctx._source`，让 ES 按新 mapping 重新解析文档补齐新字段；**不删索引、不停搜索**（十几亿环境刷历史的正确方式）
  - `TodoActionIndexAppendUkField`：榜样示例——直接 `indexOperation.updateMapping(...)` 给已存在索引增量加字段，不删索引
- WebSocket 提示：`domain/service/impl/WebSocketDomainServiceImpl`
- 权限组初始化：`AccessGroupInitializer`、`AuthAccessInitializer`

## 关键 ES 文档字段（待办排查用）
- `combineCode`：组合业务编码
- `documentId`：单据主键
- `documentKey`：组合业务对象 + 待办编码 + 单据主键
- `todoCode`：待办编码
- `assignee` / `businessRoleUuid`：经办人 / 业务角色

## 排查技巧
- 搜索消费逻辑：用 `search_repo(keyword="WorkBenchDataProcessConsumer", mode="content")` 或搜索 `@Consumer`，并根据返回路径继续局部读取。
- 搜索某单据待办生成：用 `search_repo` 搜对应 `todoCode` 或单据类型常量。
- 搜索某字段映射：配置在菜单"单据字段映射"，库表见 db_tables.md
- **超级搜索"新增可搜字段"完整链路**（纯配置 + 安全刷新，详见 `references/super_search_field_config.md`）：
  1. `swbh_doc_object_rel_field`（`srm_workbench`）：登记业务字段（`bo_field_code`、个性化字段需先在 BO 模型注册、`index_flag=1`、发布）——决定字段**进 ES 存储**
  2. ES 对象管理点发布 / `doc-publish` 接口 → `updateMapping` 增量加字段定义（**只更新结构、对海量数据零影响**）
  3. 刷历史：十几亿数据**严禁** `reindex rebuild=true`（删索引全量重建）；用 `app/datafix` 下 `UpdateByQueryRequest` 类脚本（参考 `EsSourceReMappingByDocNum`）原地回写，不删索引
  4. `swbh_doc_type_search_filed`（`srm` 库 `spfm_rel_table_record`，`table_code='swbh_doc_type_search_filed'`）：加 `searchFiled=字段名` ——决定字段**能被关键字搜到**
  5. （可选）`swhb_front_customizer`（`SEARCH_FRONT_CUSTOMIZER`）：前端筛选器入口
  - 关键区分：`swbh_doc_type_search_filed`（SEARCH_FILED）只管"搜"，`swbh_doc_type_index_filed`（INDEX_FILED）+ `swbh_doc_object_rel_field` 才管"存"。只配 search 不配 index/rel_field → 字段不在 ES 搜不到；只配 index 不配 search → 存了但搜不到。
