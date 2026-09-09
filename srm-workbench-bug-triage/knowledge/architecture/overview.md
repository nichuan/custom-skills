# srm-workbench 服务概览

采购员工作台（采购员一站式作业平台）由 **消费程序**（把数据刷入 ES + 生成/清除待办关注）与 **界面查询接口** 两部分组成。代码在 `srm-workbench`，前端在 `srm-front-swbh`。

## 一、消费程序
### 1. 单据消费程序（刷 ES + 生成/清除待办关注）
- 监听 topic（cm 变量 `SWBH_WORK_BENCH_TOPIC`，各环境不同），消息内容为 binlog。
- 根据 binlog 将单据按指定格式刷入 ES，并按配置字段生成/清除待办与关注。
- 代码：`org.srm.workbench.infra.consumer.WorkBenchDataProcessConsumer`
- 注意事项：
  - ES 不稳定导致消费失败需记录失败记录补偿（`swbh_err_record`）。
  - 清除任务查 ES 现有数据，与库核对判断有效性。
  - 单据权限相关数据也需刷入 ES（见权限组）。
  - 部分单据字段在行上（如物料），需冗余到头维度才能被搜索 → 定时任务处理。

### 补偿 JobHandler（消费/清除）
- `org.srm.workbench.app.jobhandler.DocConsumerCompensateHandle` 单据补偿
- `org.srm.workbench.app.jobhandler.TodoConsumerCompensateHandle` 待办补偿
- `org.srm.workbench.app.jobhandler.TodoConsumerEliminateHandle` 待办清除
- `org.srm.workbench.app.jobhandler.ActionConsumerCompensateHandle` 关注补偿
- `org.srm.workbench.app.jobhandler.ActionConsumerEliminateHandle` 关注清除

### 行字段冗余
- `org.srm.workbench.app.service.impl.WorkBenchDataBatchProcessServiceImpl#recordChangeLine` 消费时判断需冗余字段变化，记录头 id
- `org.srm.workbench.app.jobhandler.LineFieldCompensateHandler` 定时任务

### WebSocket 提示
- 待办生成/清除时发 WebSocket 给前端：`org.srm.workbench.domain.service.impl.WebSocketDomainServiceImpl`

### 2. 工作流消费程序
- 监听同一 topic，只处理 `act_hi_actinst` 表 binlog，判断生成/清除工作流待办。
- 代码：`org.srm.workbench.infra.consumer.WorkFlowDataProcessConsumer` / `org.srm.workbench.app.jobhandler.WorkFlowConsumerCompensateHandle`
- 注意：工作流挂起时 `act_hi_actinst` 无变化 → 无 binlog → 无法捕捉挂起，经办人仍能查到该待办。
- 工作流待办唯一性：通过 `proc_inst_id_`、`execution_id_`、`task_id_`、`assignee_`、`tenant_id_` 五字段判定新生成/清除。

### 3. 单据权限 / 物流权限消费
- 单据权限：表 `hiam_user_authority`、`hiam_user_authority_line`；`org.srm.workbench.app.event.UserAuthorityChangeConsumer`
- 物流权限：表 `slod_strategy_permission`、`sinv_rcv_strategy_permission`；`org.srm.workbench.app.event.LogisticsRolePermissionConsumer`

## 二、界面（查询接口）
页面分 **超级查询** 与 **采购员工作台** 两部分。
- 超级查询：单据/供应商/物料三类聚合查询，关键字匹配 → 拿单据头主键 → feign 调各模块详情 → 组装。
  - 代码：`org.srm.workbench.api.controller.v1.DocDataSearchController`
  - 注意：①尚未对接逻辑删除，部分已删单据仍可被搜出；②详情用 feign 调用，开放后可能有性能问题。
- 采购员工作台：待处理（待办）、待阅读（关注）、我发起、我经办、待转单、草稿箱。
  - 待处理/待阅读：按 角色+用户 查询待办/关注 → feign 调详情组装。
  - 注意：待办与单据分开存，分页时筛选器条件是单据字段，排序按待办生成时间 → 需回查待办重排（见 bug_triage）。
  - 待阅读"忽略"后查不到且总数 -1。
  - 待转单：feign 调各模块汇总转单类型；有拦截器优化性能。
  - 草稿箱：各单据"新建"状态代码写死（后续应改配置项）。
  - 我经办：部分单据仅行处理、头最后更新人未变 → 查不到。

## 三、配置项（运维/产品侧，常是问题根因）
1. 待办与关注：配置待办/关注类型、条件、跳转页。
2. 单据字段映射：前端展示字段及格式。
3. ES 对象管理：需刷 ES 的单据及字段。
4. 脚本：`SWBH_INIT`（租户初始化）。

## 四、权限组（ES 数据权限过滤）
作用：ES 查询时做单据权限过滤。相关表见 `db_tables.md`（swbh_access_group 等）。
- 租户 ES 初始化：`AccessGroupInitializer`、`AuthAccessInitializer`
- 变更：`UserAuthorityChangeConsumer` → 记 `swbh_user_auth_change_record` → `UserAccessGroupChangeJobHandler`（每 5/4 分钟扫 100 用户）→ `EsDocumentAccessChangeJobHandler`（每 30/10 分钟更新 ES）
- ES 权限更新失败补偿：`DocAccessChangeCompensateHandle`（本地线程，最多 3 次）
- 物流单据额外有基于角色的权限控制：`WorkBenchDataBatchProcessServiceImpl#insertESDimension`、`LogisticsRolePermissionConsumer`、`LogisticsRolePermissionCompensateHandler`

## 五、新租户初始化
- 发版时先停消费（改 cm `SWBH_WORK_BENCH_TOPIC` 让其他节点不消费），初始化新租户，再改回。
- 代码：`org.srm.workbench.api.controller.v1.ESDataInitializerController#batchInit`
- 风险：不停消费其他节点丢 binlog；与 binlog 并行写可能致 ES 经办人缺失。
