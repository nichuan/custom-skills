# 整改 / 待办模块排查要点（采购员工作台）

本文件补充采购员工作台内**整改类单据**与**待办（Action）**的专项排查知识。
通用架构、权限组模型、消费程序见 `service_overview.md` / `bug_triage.md` / `db_tables.md`。

## 1. 整改类单据标识（combineCode / todoCode）

整改模块（结算整改、预付整改、发票整改等）在 ES 中以独立索引存储，常见标识：

- 单据索引 / combineCode：`SRM_C_SRM_SSTA_SETTLE_HEADER`（结算整改头）
- 待办（Action）索引：`srm_todo_record`
- 整改相关 todoCode 清单（来自结算整改待办查询 DSL）：
  - `SSTA.APPROVE_PREPAYMENT` — 预付整改审批
  - `SSTA.SETTLE_APPROVE_INVOICE` — 发票整改审批
  - `SSTA.SETTLE_APPROVE_PAYMENT` — 付款整改审批
  - `SSTA.SETTLE_REFUSE_INVOICE` — 发票整改驳回
  - `SSTA.SETTLE_REFUSE_PAYMENT` — 付款整改驳回
  - `SSTA.SETTLE_REFUSE_PREPAYMENT` — 预付整改驳回
  - `SSTA.SETTLE_HEADER.WFL` — 工作流类（需 `isApproved = 0`）

> 注：具体租户/环境可能不同，排查时应以实际 ES 中的 `header.combineCode` / `header.todoCode` 为准，可用 DSL 模板现场枚举。

## 2. 待办查询 DSL 模板（核对待办是否存在）

排查"待办缺失 / 计数不对"时，直接用以下 DSL 在 ES 中核对。

### 2.1 按单据 + 用户查待办
```json
GET srm_todo_record/_search
{
  "from": 0, "size": 10,
  "query": {
    "bool": {
      "should": [{
        "bool": {
          "must": [{ "terms": { "header.documentId": ["<单据ID>"], "boost": 1 } }],
          "filter": [
            { "term": { "header.combineCode": { "value": "<COMBINE_CODE>", "boost": 1 } } },
            { "term": { "header.tenantId": { "value": <租户ID>, "boost": 1 } } },
            { "bool": {
                "should": [
                  { "bool": { "filter": [{ "terms": { "header.todoCode": ["<TODO_CODE>"], "boost": 1 } }] } },
                  { "bool": { "filter": [
                      { "terms": { "header.todoCode": ["<COMBINE>.WFL"], "boost": 1 } },
                      { "term": { "header.isApproved": { "value": 0, "boost": 1 } } }
                  ] } }
                ],
                "minimum_should_match": "1" } }
          ],
          "should": [
            { "term": { "header.subscriptionUser": { "value": <用户ID>, "boost": 1 } } },
            { "term": { "header.subscriptionRole": { "value": <角色ID>, "boost": 1 } } }
          ],
          "minimum_should_match": "1" } } } ],
      "minimum_should_match": "1" } }
}
```

### 2.2 删除某条待办（仅在确认需清理时使用，需用户执行）
```
DELETE /srm_todo_record/_doc/<_id>
```

### 2.3 按 rfxHeaderId 查具体单据（超级搜索/卡片定位用）
```json
GET <index>/_search
{
  "from": 0, "size": 5000,
  "query": { "bool": { "should": [
    { "bool": { "must": [{ "terms": { "header.rfxHeaderId": ["<ID>"], "boost": 1.0 } }] } }
  ], "minimum_should_match": "1" } }
}
```

## 3. 整改待办异常排查链路

现象（待办不显示 / 计数错 / 消失）→ 按此顺序排查：

1. **ES 中是否真的有待办**：用 §2.1 DSL 查 `srm_todo_record`，确认 `subscriptionUser` / `subscriptionRole` 是否命中当前用户。
   - 命中角色而非用户时，确认用户是否已绑定该角色。
2. **消费程序是否生成了 Action**：整改单据落库后，由消费程序监听 binlog 生成待办写入 ES。若 ES 无记录：
   - 查 `swbh_err_record`（消费失败错误记录），由补偿 JobHandler 重试；
   - 核对 binlog 流里该单据是否有对应事件（参考案例文件夹 `阿里云的删除binlog.txt` 的核对思路）。
3. **权限 / 订阅校验**：整改单据同样受 `swbh_auth_access` / `swbh_access_group` 权限组控制，确认用户所属权限组有权限（见 `db_tables.md` 权限表）。
4. **工作流挂起**：若 `act_hi_actinst` 无 binlog，工作流类待办（`.WFL`）无法自动清除，表现为"已办仍显示"。

## 4. 初始化 / 配置清单（新租户或整改模块异常时核对）

来自 `采购员工作台项目初始化` 手稿，整改模块相关初始化项：
- 建表 / 配置表结构（多云环境需初始化，公有云不需要）
- 角色工作台初始化租户列表：`swbh_initialize_tenant_list`
- 前端隐藏租户清单：`swbh_front_hide_whitelist`
- 建 ES 索引：`SWBH_INIT_INDEX`
- 初始化业务数据 PlayGround：`SWBH_INIT`
- 整改单据的个性化单元配置：`swhb_front_customizer`
- 单据状态标签样式：`swbh_doc_status_style`
- 卡片信息 / 卡片分组：`swbh_card` / `swbh_card_doc_relation`
- 单据权限集配置：`swbh_doc_type_permission_data_set`（权限集 code 由 `srm` 库的 `iam_menu.code` 关联，查 `iam_menu` 时需显式 `db_name="srm"`）

> 排查"整改模块整片不显示"时，优先核对上述初始化项是否在该租户落全。
