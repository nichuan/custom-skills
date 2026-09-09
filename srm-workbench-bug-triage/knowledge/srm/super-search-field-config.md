# 超级搜索「额外字段查询」配置与 ES 刷新知识

> 适用场景：用户想在超级搜索中新增一个可关键字搜索的字段（如询价单头表个性化 varchar 字段），或排查"字段搜不到 / ES 里没有该字段"类问题。
> 源码位置：`D:\devTools\code\srm\srm-workbench`（org.srm.workbench）。以下结论均来自本地源码核对。

---

## 一、核心结论：三张配置表职责分离

超级搜索"能不能搜某字段"与"该字段在不在 ES 里"由不同配置驱动，**绝不互通**。

| 配置表（宽表） | 库 | 代码读取入口 | 职责 |
|---|---|---|---|
| `swbh_doc_type_search_filed`（`SEARCH_FILED`） | `srm.spfm_rel_table_record` | `DataCache.getSearchField()` → `EsSearchServiceImpl` 拼 `multiMatch` | **只决定「关键字能搜哪些字段」**（查询侧） |
| `swbh_doc_type_index_filed`（`INDEX_FILED`） | `srm.spfm_rel_table_record` | `DataCache.getIndexField()` | 决定「按单据类型挂哪些 id 类索引」 |
| `swbh_doc_object_rel_field`（`srm_workbench` 库） | `srm_workbench` | `DataCache.getIndexFieldsByCombineCode()`（`by docObjectRelId`） | **决定「ES 文档里存哪些业务字段 + 什么类型」**（写入侧，最关键的字段登记表） |

代码证据：
- `DataCache.java:197-208`：`getIndexField()` 读 `INDEX_FILED`、`getSearchField()` 读 `SEARCH_FILED`，两个独立缓存。
- `RelTableRepositoryImpl.java:38-49`：`queryIndexField()` 与 `querySearchField()` 各自独立。
- `WorkBenchDataBatchProcessServiceImpl` 的 `updateESData`（:1093+）写入文档时，依据 `getIndexFieldsByCombineCode` + `getIndexField`，**不是** `searchFiled`。

**一句话**：`swbh_doc_type_search_filed` 只管"搜"，不管"存"；"存"由 `swbh_doc_object_rel_field`（业务字段明细）+ `swbh_doc_type_index_filed`（单据类型挂索引）决定。

---

## 二、新增一个可搜字段的完整步骤（以"询价单头表加个性化 varchar 字段"为例）

假设目标：在询价单（`combineCode` 如 `SRM_C_SRM_SSRC_RFX_HEADER`）头表，把个性化 varchar 字段 `attributeVarchar1` 纳入超级搜索。

### 步骤 1：ES 对象管理登记字段（最关键）
- 目标表：`swbh_doc_object_rel_field`（`srm_workbench` 库）
- 给该单据的 `doc_object_rel_id` 新增一行：
  - `bo_field_code` = `attribute_varchar1`（数据库列名下划线；代码会 `Tool.lineToHump` 转成 ES 里驼峰 `attributeVarchar1`）
  - `bo_field_id` = 对应 `hmde_bo_field.bo_field_id`（个性化字段需先在 BO 模型注册）
  - `index_flag` = 1（标记为索引字段，才进 mapping 和写入）
  - `publish_status` = `PUBLISHED`（发布后回填 `dataType`）
  - `data_type`：varchar → 通常映射为 `TEXT`（IK 分词）。若只需精确匹配不想被分词，看 ES 对象管理界面能否指定 `KEYWORD`。
- 这一步就是"ES 对象管理界面新增字段并发布"。发布动作触发 `EsIndexServiceImpl` 重建/更新该 combineCode 的索引 mapping（:277-287），把字段加进 header。

### 步骤 2：更新 ES 索引结构（mapping）
- 点发布（`doc-publish` 接口，见第三节）或等待 `DocObjectFieldsSyncJobHandler` 夜间同步后手动发布。
- 实际执行 `EsIndexOperation.updateMapping`（:113-129）的 `PutMappingRequest` —— **增量加字段定义，不删索引、不碰数据**。
- `DocObjectFieldsSyncJobHandler`（:47-89）：每晚同步 BO 模型字段进 `swbh_doc_object_rel_field` 配置表（自动补新字段行），但**只改配置表、不重建 ES**，仍需另外触发发布。

### 步骤 3：刷新历史数据（见第四节，十几亿数据务必谨慎）
- mapping 更新后，**已有文档不会自动带新字段值**（只新增了字段定义，旧文档 `_source` 里没有该值）。
- 新产生/变更的询价单通过 binlog 消费（`updateESData`）写入时会带上它。
- 存量单据必须额外刷（用 `updateByQuery` 而非全量重建）。

### 步骤 4：登记超级搜索配置
- 宽表 `srm.spfm_rel_table_record`，`table_code='swbh_doc_type_search_filed'`，`value1 = combineCode`，`SearchFiledDTO.searchFiled = attributeVarchar1`（ES 驼峰值）。
- 之后 `EsSearchServiceImpl` 的 `multiMatch` 才会匹配该字段。

### 步骤 5（可选）：前端筛选器
- 若要在超级搜索前端露出该字段筛选入口，在 `swhb_front_customizer`（`SEARCH_FRONT_CUSTOMIZER`）加配置。

**只有步骤 4 配了但步骤 1-3 没做** → 字段不在 ES，搜不到；**只做 1-3 没做 4** → 字段存进去了但关键字搜索不匹配。

---

## 三、`doc-publish` 与 `reindex` 接口区别（来自 `DocObjectDefinitionSiteController.java`）

### `PUT /doc-object-definitions/doc-publish`（:118-126）
- 进入 `DocObjectDefinitionServiceImpl.publish` → `doEsPublish`（`@Async`，:165-177）→ `esIndexService.batchCreateIndex(PENDING)`。
- 对已发布单据对象走 `updateIndexMapping`（增量 `putMapping`）。
- 参数 `time`：
  - `current`：**立即**执行 `putMapping`（mapping 马上加字段）。
  - `delay`：**排到次日凌晨 1 点**才执行（含伪随机延迟避免多实例并发），别以为点了就立刻生效。
- **只更新 mapping 结构（加字段定义），不回填历史数据。**

### `PUT /doc-object-definitions/reindex`（:128-171）
- `rebuild=true`：**先 `deleteIndex` 删索引，再 `initIndex` 全量重建并灌数据**（:165-167）。
- `flush-all=true` 重建所有 `PUBLISHED` 索引；`indexNames` 指定单个/部分索引。
- ⚠️ **会删索引**，删除-重建窗口内该单据类型搜索短暂不可用；全量重建对 DB/ES 压力极大。

---

## 四、海量数据（十几亿）安全刷新原则 ⛔

**绝对禁止**在十几亿正式环境用 `reindex?rebuild=true`（全量删索引重建，搜索停摆数小时、压垮集群）。

**正确做法：更新结构 + `updateByQuery` 刷历史，都不删索引。**

### 更新结构（零风险）
- `doc-publish` / `updateMapping` 是增量 `putMapping`，毫秒级、对现有数据和线上零影响，可随时做。
- 榜样：`app/datafix/TodoActionIndexAppendUkField.java:34-49` 直接 `indexOperation.updateMapping(...)` 给已存在索引加字段。

### 刷历史（`updateByQuery`，不删索引）
- 榜样：`app/datafix/EsSourceReMappingByDocNum.java:36-53` 用 `UpdateByQueryRequest` 按查询原地回写：
  - `setScript("ctx._source = ctx._source")` —— 让 ES 按新 mapping 重新解析文档 `_source`，补齐新字段。
  - 海量调优参数：`setSlices(2)` / `setScroll(TimeValue.timeValueMinutes(15))` / `setBatchSize(3000)` / `setConflicts("proceed")` / `setRefresh(true)`（:38-43）。
  - **不删索引、不停搜索**，后台批量回写，过程中新字段逐步补齐。
  - ⚠️ 必须**限定到具体索引**（如只跑 `srm_c_srm_ssrc_rfx_header`），不要 `srm_c_*` 全量（十几亿下太猛）。

### 关键前提：字段值来源判定（情形 A / B）
- **情形 A**：字段值已存在于文档 `_source` 原始数据里（旧 mapping 没定义 → 老文档 `_source` 其实已存该值，只是未被索引）。
  → `ctx._source = ctx._source` 原样重解析即可让 ES 识别并索引它，`EsSourceReMappingByDocNum` 直接适用。
- **情形 B**：字段值是写入 ES 时实时计算/翻译出来的（如要查扩展表才能拿到，逻辑在 `WorkBenchDataBatchProcessServiceImpl.updateESData` 里拼）。
  → 老文档 `_source` 根本没有这字段，光 `updateByQuery` 原样回写造不出值，需走按单据号批量重灌（参考 `EsDocNumAnalysisFix` 依赖的按 docNum 重算方式），或只对有数据的单据做增量补。

---

## 五、概念澄清

- **"更新 ES 索引结构" = 更新 mapping（字段映射定义）**，类似给表 `ALTER TABLE ADD COLUMN`。只让索引"认识"新字段、以后新文档能存它；**不会**自动把历史文档该字段值补上。
- ES 文档结构（以 `srm_c_srm_ssrc_rfx_header` 为例）：`access`（权限维度，来自 `swbh_doc_type_dimension_mapping` + `insertESDimension`，值是权限组 id 集合）、`header`（业务字段，来自 `swbh_doc_object_rel_field`）、`handleRecords`（经办人，代码写死结构）。
- "搜不到"的常见根因链：字段没在 `swbh_doc_object_rel_field` 登记（`index_flag=1`）→ 没进 mapping → ES 无此字段；或 mapping 有了但没在 `swbh_doc_type_search_filed` 登记 → multiMatch 不匹配；或 mapping 有了、search 也配了，但历史数据没刷 → 老单据搜不到（新单据能搜到）。
