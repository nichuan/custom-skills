# 角色工作台（srm-workbench）完整设计逻辑总览

> 仓库：`operation-srm/srm-workbench` (develop 分支) | 前端：`srm-front-swbh`
> 包名：`org.srm.workbench` | 架构：Cola
> 本文档为 bug-triage 技能的内部逻辑字典，供快速定位问题。

## 一、整体架构与数据流

```
业务系统改库 → binlog(DTS/DRS, Kafka topic=spring.kafka.topic.workbench)
   → WorkBenchDataProcessConsumer (KafkaListener, group-id=workbench.kafka.group-id.document)
   → ConsumerUtils.convertAliYunDRSVOs (阿里云DRS结构转华为云兼容结构, 因delete结构变更)
   → WorkBenchDataBatchProcessServiceImpl.batchProcessData(huaweiDRSVOS)
       ├─ docBatchProcess     → 冗余进 ES (按 combineCode 索引)
       ├─ todoBatchProcess    → 生成/清除 待办 (DB: swbh_todo_definition + 待办数据表)
       └─ actionBatchProcess  → 生成 动态/关注 (DB: swbh_action_definition)
   失败 → swbh_err_record (errRecordRepository.record) → 补偿 JobHandler
```

关键前置判断：
- `WorkbenchRedisUtils.getWorkbenchTenantSet()`：角色工作台**已启用的租户清单**（Redis 缓存）。只有启用租户的变更才会被处理。
- `docObjectRelList`：`queryDocObjectInfo()`，仅 `publishStatus=PUBLISHED` 的对象参与。一个表可映射多个 combineCode（多索引）。
- 按 `tenantId` 分组处理，且 tenant 须命中启用清单。

## 二、双轨配置存储（查错前先判断走哪条路）

| 轨道 | 表 | 内容 |
|---|---|---|
| A 实表 | `srm_workbench`.`swbh_*` | todo_definition / action_definition / err_record / card_definition / subscribe_rel 等23张直表 |
| B 宽表 | `srm`.`spfm_rel_table_record` | 按 `table_code` 分类，字段塞 `value1~value75`。超级搜索相关配置全在这 |

### rel-table 宽表常用 table_code
- `swbh_doc_type_search_filed` —— 超级搜索**关键字匹配字段**（每行 value1=单据类型combineCode）
- `swbh_doc_type_index_filed` —— ES 索引字段定义（即 `doc_object_rel_field` 的来源之一）
- `swbh_doc_type_dimension_mapping` —— 权限维度字段映射（businessObjectCode → 字段）
- `swbh_doc_type_line_field` —— ES **冗余行字段**（决定哪些业务字段被冗余进 ES 文档）
- `swbh_doc_object_rel` —— 组合业务对象（索引对象）定义
- （待办/关注条件等也在此宽表）

> 读配置入口：`RelTableRepositoryImpl` → `DataCache.getSearchField()` / `getIndexField()` / `getDimensionMapping()` 等，底层 `RelTableHelper.selectByCondition(tenantId, tableCode, ...)`。
> **注意：超级搜索字段 `getSearchField()` 默认只读 `tenant_id=0`（平台级默认）配置。**

## 三、ES 文档写入（docBatchProcess）

写入字段来源（search 侧能 match 的前提）：
1. `queryDocObjectInfo()` → combineCode / docObjectRelId / mainTableFlag / relBusinessObjectCode
2. `queryDocTypeLineField()` (`swbh_doc_type_line_field`) → 冗余进 ES 的字段清单（按 combineCode 过滤）
3. `queryDocObjectRelField(docObjectRelId)` (`doc_object_rel_field`) → 索引发布字段，**按租户区分**（平台0 + 租户专属）
4. `queryDimensionMapping()` → 权限维度字段（写入 ES 文档供权限过滤）
5. `queryDocObjectFieldTranslate()` → 主数据翻译 SQL（DEFAULT 作用于 ES）
6. `mainTableFlag==1` 为主表（header），才查权限维度并写入权限相关字段

ES 文档结构：`indexName = combineCode.toLowerCase()`，`pkName` 为主键。
`EsDataOperation` 通用 ES 读写（bulk/单条 upsert/delete）。

**结论**：搜索生效三要素 = ① 字段冗余进 ES（`line_field`+`rel_field`）② 关键字匹配配置（`search_filed`）③ 业务表真实有值 + 存量已刷数。

## 四、待办（todoBatchProcess）

- 配置：`swbh_todo_definition`（待办定义，实表）。匹配条件来自配置表。
- 待办数据与单据**分开存储**（独立待办表），按 `combineCode + 单据主键` 关联。
- 生成/清除由消费触发：`todoBatchProcess` 按定义条件判断该单据是否满足待办，满足则 upsert 待办，不满足则删除。
- **分页/筛选/排序**：列表查询时筛选器是单据字段、排序按待办生成时间 → 需回查单据重排（见 code_map 待办分页重排说明）。
- 失败落 `swbh_err_record`，由 `TodoConsumerCompensateHandle` / 补偿 JobHandler 处理。

## 五、动态/关注（actionBatchProcess）

- 配置：`swbh_action_definition`（动态/关注定义，实表）。
- 动态（单据动态流）由消费写入；关注（用户关注某单据）由用户操作写入 `swbh_action_definition` 相关。
- 整改模块受**权限组 + 订阅**双重控制：`subscriptionUser` / `subscriptionRole`。

## 六、超级搜索（DocDataSearchController.maintain → DocDataSearchServiceImpl.list）

入口：`/v1/{organizationId}/doc_data_search/maintain`
请求 DTO：`EsRequestParamDTO`（含 keyword、page、size、asyncCountFlag、type 等）

**写死三大类并发查询**（核心是 `futureMap`）：
- `SearchType.DOC` → `docDatalist`（单据综合查询）
- `SearchType.SUPPLIER` → `querySupplier`（供应商）
- `SearchType.ITEM` → `queryItem`（物料主数据）

`switch(type)` 只处理 DOC/SUPPLIER/ITEM，无 default 承接新类型。
新增并列大类（如"提示词"）→ 改 list() 的 futureMap + switch + `WorkBenchConstant.SearchType` + `EsAllResponseResultDTO` + 前端 tab。

### 单据查询 DSL 拼装（EsSearchServiceImpl）
- `buildDocDataSearchDSL` / `buildDocSearchRequest`：
  - 关键字匹配字段 `querySearchField()`（`swbh_doc_type_search_filed`）→ 按 combineCode 分组，拼 multiMatch/should
  - 索引字段 `queryIndexField()`（`swbh_doc_type_index_filed`）
  - 权限维度过滤 `queryDimensionMapping()` + 当前用户权限组 → bool filter
- **搜索范围（目前有效）**：`swbh_doc_type_search_filed` 平台级(tenant=0)共 30 类单据编码（PR/PO/RF/RFX/寻源项目/收货/发货/标签/计划/供应商生命周期族/索赔/异常/合同/账单/收费/结算/物料主数据等）。

### 单据类型内部扩展（策略工厂）
`EsDataFactory.register(combineCode, XxxHandleImpl)`，每个单据一个 `XxxHandleImpl` 实现 `EsDataHandle`（queryesdata 包下几十个 Handler：PR/RFX/收货/发货/合同/供应商生命周期...）。工厂模式供"单据类型内部"扩展，非"搜索大类"扩展。

## 七、权限组数据权限（RoleAuthorityServiceImpl）

用户查询工作台/超级搜索时，ES 查询额外拼接**数据权限 filter**：
- 取当前用户所属 `accessGroup`（权限组，配置于 `swbh_auth_access` 等）
- 维度映射（`swbh_doc_type_dimension_mapping`）把"权限组维度"映射到 ES 文档的具体字段
- 拼 bool filter：仅返回该用户权限组可见的单据
- 权限变更链路：`UserAuthorityChangeConsumer` → `UserAccessGroupChangeJobHandler` → `EsDocumentAccessChangeJobHandler`（批量 bulk 回刷 ES 文档权限字段，量大有 OOM 风险）

> 超级搜索"查不到单据"常见根因：① 权限组维度映射缺失 ② 索引未刷权限字段 ③ 权限组未配置。

## 八、工作台卡片/统计（CardSearchServiceImpl）

- 工作台 tab 的计数（待办/关注/动态/单据总数）由 `CardSearchServiceImpl` **异步聚合**：
  - 主查询返回 tab 骨架
  - 各卡片计数异步（Future/线程池）查 ES 聚合（如某单据类型 count by 状态）
  - 计数配置来自卡片定义表
- 常见现象：计数延迟/不对 → 看异步聚合是否抛错、ES 聚合条件是否与定义一致。

## 九、WebSocket 实时推送

`WebSocketDomainServiceImpl` + `webSocketDomainService`：单据状态变更/待办生成时，经消费程序通过 WebSocket 推前端实时刷新。

## 十、ES 初始化与新租户上线

- `ESDataInitializerController` / `SWBH_INIT` 脚本：初始化索引、刷全量数据。
- 新租户上线：① 加入 `WorkbenchRedisUtils` 启用租户清单 ② 配置 rel-table（维度映射/冗余字段/索引字段/搜索字段）③ 跑初始化刷数。

## 十一、常见排查入口速查

| 现象 | 优先查 |
|---|---|
| 超级搜索查不到某单据 | ① search_filed 有该 combineCode？ ② ES 索引有该字段且已刷数？ ③ 权限组维度映射/ES权限字段？ ④ 租户是否启用 |
| 待办不显示/计数不对 | ① todo_definition 条件 ② 消费是否成功(err_record) ③ 分页重排逻辑 |
| 动态/关注异常 | action_definition + subscriptionUser/Role 订阅 |
| 权限组不生效 | dimension_mapping + EsDocumentAccessChangeJobHandler 回刷 |
| 卡片计数不对 | CardSearchServiceImpl 异步聚合 + 卡片定义 |
| 新增搜索字段 | line_field + rel_field(进ES) + search_filed(匹配) + 存量刷数 |
