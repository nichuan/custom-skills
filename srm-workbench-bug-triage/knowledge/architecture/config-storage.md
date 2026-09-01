# 核心数据表与连接信息

## 连接信息（走统一 `zhenyun-pangu-mcp` 的 Archery 工具）
- 默认库名：**`srm_workbench`**（角色工作台 `swbh_*` 表所在库）
- 查 `srm` 库的业务源表（如 `sinv_rcv_trx_header`、`iam_menu` 等）时，显式传 `db_name="srm"`
- 工具：`archery_query`（仅只读 SELECT）、`archery_describe_table`、`archery_list_columns`、`archery_list_databases`
- 凭据：统一由 `zhenyun-pangu-mcp/.env` 提供，**严禁在文档、代码或示例中写死账号密码**
- 使用：`archery_query({"sql": "SELECT ... FROM swbh_xxx ...", "db_name": "srm_workbench"})`；跨 `srm` 库显式传 `db_name="srm"`
- 注意：MCP 仅只读，写操作一律生成 SQL 后由用户在 Archery/生产客户端执行。

## 待办与关注定义
- `swbh_action_definition` 关注定义（关注类型、条件、跳转页）
- `swbh_todo_definition` 待办定义（待办类型、条件、订阅对象、跳转页）
- `swbh_todo_document` 待办数据
- `swbh_action_document` 关注（单据动态）数据

## 权限组（ES 数据权限过滤）
- `swbh_access_group` 权限组定义（含 `where_condition` SQL 条件）
- `swbh_access_data_rule` 权限组关联规则
- `swbh_access_role` 权限组关联角色
- `swbh_access_data_permission` 权限组数据权限
- `swbh_action_authority` 功能权限（关注权限点）
- `swbh_user_auth_change_record` 用户权限变更记录（待同步 ES）

## 消费/补偿记录
- `swbh_err_record` 消费失败记录（由补偿 JobHandler 处理）

## 单据权限来源表
- `hiam_user_authority` / `hiam_user_authority_line` 单据权限（用户级）
- `slod_strategy_permission` 物流权限
- `sinv_rcv_strategy_permission` 收货策略权限

## 工作流
- `act_hi_actinst` 流程实例历史活动（工作流待办消费来源）

## ⚠️ 双轨数据模型（排查前必读：配置数据有两类存储方式）

采购员工作台的配置数据有**两种完全不同的存储形态**，查错前必须先判断目标配置属于哪一类，否则会查错库/查错表：

### 轨道 A：实表（直接建表、INSERT 写入）—— 在 `srm_workbench` 库
- 形如 `swbh_todo_definition`、`swbh_doc_object_rel`、`swbh_action_definition`、`swbh_access_group`、`swbh_err_record` 等 **23 张 `swbh_*` 实表**。
- 数据由 `srm-workbench-sql/*.sql` 脚本**直接 INSERT** 进对应实表。
- 排查：直接 `SELECT * FROM swbh_xxx WHERE tenant_id=?`，MCP 默认库即 `srm_workbench`。

### 轨道 B：rel-table 宽表（EAV 槽位存储）—— 在 `srm` 库
- 所有 `srm-workbench-rel-table/*.xlsx` 的配置数据，**不是**独立的表，而是全部塞进 `srm.spfm_rel_table_record` 这一张宽表。
- 每个 excel 文件的 **sheet 页名 = `table_code`**（注意：看起来像表名，但实际只是宽表里的一个分类键，并非真实表）。例如：
  - `角色工作台单据权限维度映射*.xlsx` 的 sheet `swbh_doc_type_dimension_mapping`
  - `角色工作台初始化租户清单*.xlsx` 的 sheet `swbh_initialize_tenant_list`
  - `角色工作台导航卡片*.xlsx` 的 sheet `swbh_card`
  - `角色工作台卡片分组关系*.xlsx` 的 sheet `swbh_card_doc_relation`
  - 等等（共 17 个 sheet / table_code）。
- 宽表结构：`(id, tenant_id, table_code, value1~value75, longValue/longValue1~50, index0~index50, unique_index, ...)`，配置字段按列顺序映射到 `valueN` / `indexN` 槽位，**没有语义化列名**。
- 排查：必须 `archery_query` 显式传 `db_name="srm"`，按 `table_code` 过滤：
  ```sql
  -- 查某类配置的全部数据
  SELECT * FROM spfm_rel_table_record
   WHERE table_code = 'swbh_doc_type_dimension_mapping'
     AND tenant_id = ?;

  -- 看某 table_code 有多少条、分布在哪些租户
  SELECT tenant_id, COUNT(*) cnt FROM spfm_rel_table_record
   WHERE table_code = 'swbh_initialize_tenant_list'
   GROUP BY tenant_id;
  ```
- **常见误区**：看到 `swbh_doc_type_dimension_mapping`、`swbh_initialize_tenant_list`、`swbh_card` 这类名字，容易误以为是 `srm_workbench` 的实表去查 → 会报"表不存在"。它们其实只在 `srm.spfm_rel_table_record` 里以 `table_code` 形式存在。

### 两类对照速查（table_code ↔ 含义）
| excel 文件主题 | table_code（sheet 名） | 用途 |
|---|---|---|
| 单据权限维度映射 | `swbh_doc_type_dimension_mapping` | 单据→权限维度映射（超级搜索查不到收货单的根因表，见 `case_search_rcv_not_found.md`） |
| 初始化租户清单 | `swbh_initialize_tenant_list` | 工作台初始化支持的租户 |
| 导航卡片 | `swbh_card` | 首页导航卡片 |
| 卡片分组关系 | `swbh_card_doc_relation` | 卡片与单据关系 |
| 卡片快速入口 | `swbh_cart_quick_link` | 菜单权限集映射 |
| 可快速发起业务 | `swbh_card_doc_type_fast` | 快速发起 |
| 单据主对象索引字段 | `swbh_doc_type_index_filed` | 单据索引字段 |
| 单据编码字段 | `swbh_doc_num_field` | 单据编码字段 |
| 单据配置权限集 | `swbh_doc_type_permission_data_s` | 单据权限集 |
| 单据状态标签样式 | `swbh_doc_status_style` | 状态标签 |
| 单据对象属性翻译 | `swbh_doc_object_field_translate` | 字段翻译 |
| 业务表关系配置 | `swbh_table_rel_config` | 表关系 |
| 相关业务表所属 schema | `swbh_table_schema` | 源表 schema |
| es 存储行字段 | `swbh_doc_type_line_field` | ES 行字段 |
| 超级查询字段(关键字) | `swbh_doc_type_search_filed` | 超级搜索关键字 |
| 供应商工作流表 | `swbh_sslm_work_flow` | 供应商工作流 |
| 新/老待办特殊处理 | `swbh_new_todo_set` | 待办特殊处理 |
| 个性化单元编码收集表 | `swhb_front_customizer` | 前端个性化单元 |

> 完整 sheet→table_code 已核对线上 `spfm_rel_table_record` 真实存在（如 `swbh_card`=56 行、`swbh_doc_type_dimension_mapping`=116 行、`swbh_initialize_tenant_list`=94 行）。

### rel-table 列顺序 ↔ 宽表槽位映射（写核对 SQL 用）
**规则**：excel 第 N 列 → 宽表 `valueN` 槽位（第 1 列=`value1`，第 2 列=`value2`…）；多行 JSON 内容（如卡片名称多语言）也整体落在同一 `valueN` 里。

| table_code | 列数 | 各列含义（→ 槽位） | 典型查询条件 |
|---|---|---|---|
| `swbh_doc_type_dimension_mapping` | 1 | 业务对象 → `value1` | `value1='SRM_C_SLOD_PLAN_HEADER'` |
| `swbh_initialize_tenant_list` | 1 | 租户标识 → `value1` | （按 `table_code`+`tenant_id`） |
| `swbh_doc_type_line_field` | 1 | 单据类型 → `value1` | `value1='SRM_C_XXX'` |
| `swbh_table_rel_config` | 1 | 表Code → `value1` | `value1='sodr_po_line'` |
| `swhb_front_customizer` | 1 | 组合业务对象编码 → `value1` | `value1='SRM_C_SRM_SSLM_KPI_EVAL_HEADER'` |
| `swbh_sslm_work_flow` | 1 | 组合业务对象编码 → `value1` | `value1='SRM_C_SRM_SSLM_SITE_EVAL_HEADER'` |
| `swbh_doc_type_index_filed` | 1 | 业务对象编码 → `value1` | `value1='SRM_C_XXX'` |
| `swbh_doc_object_field_translate` | 1 | 翻译类型 → `value1` | `value1='生命周期阶段'` |
| `swbh_doc_status_style` | 1 | 单据类型 → `value1` | `value1='SRM_C_XXX'` |
| `swbh_doc_num_field` | 1 | 业务对象编码 → `value1` | `value1='SRM_C_XXX'` |
| `swbh_doc_type_permission_data_s` | 1 | 单据对象 → `value1` | `value1='SRM_C_XXX'` |
| `swbh_cart_quick_link` | 1 | 单据类型 → `value1` | `value1='SRM_C_XXX'` |
| `swbh_card_doc_type_fast` | 1 | 单据类型 → `value1` | `value1='SRM_C_SRM_SSRC_SOURCE_PROJECT'` |
| `swbh_card_doc_relation` | 2 | 卡片编码→`value1`，单据类型→`value2` | `value1='SSLM' AND value2='SRM_C_XXX'` |
| `swbh_card` | 3 | 导航卡片编码→`value1`，卡片名称(多语言JSON)→`value2`，导航卡片序号→`value3` | `value1='SODR'` |
| `swbh_new_todo_set` | 1 | 老待办 → `value1` | `value1='SSLM.SUP.CHANGE.APPROVE_REJ'` |
| `swbh_table_schema` | 1 | 表名 → `value1` | `value1='slod_plan_header'` |
| `swbh_doc_type_search_filed` | 1 | 单据类型 → `value1` | `value1='SRM_C_SRM_SSRC_RF_HEADER'` |

> 绝大多数为单值配置（只存一个编码/类型到 `value1`）；仅 `swbh_card_doc_relation`(2列)、`swbh_card`(3列) 为多列，其余都映射到 `value1`。
> 多语言名称（如 `swbh_card.value2`）是整段 JSON：`{"zh_CN":"订单","en_US":"PO","ja_JP":"オーダー","zh_TW":"訂單"}`，核对时用 `LIKE '%订单%'` 或精确匹配 JSON。

### rel-table 排查模板 SQL
```sql
-- 例：查「收货单(SINV_RCV)」是否在单据权限维度映射里（超级搜索查不到的根因排查）
SELECT * FROM spfm_rel_table_record
 WHERE table_code = 'swbh_doc_type_dimension_mapping'
   AND tenant_id = ?
   AND value1 LIKE '%SINV_RCV%';

-- 例：查某卡片编码的配置
SELECT value1, value2, value3 FROM spfm_rel_table_record
 WHERE table_code = 'swbh_card' AND tenant_id = ? AND value1 = 'SODR';

-- 例：核对 rel-table 是否缺某单据类型
SELECT value1 FROM spfm_rel_table_record
 WHERE table_code = 'swbh_doc_type_search_filed' AND tenant_id = ?
   AND value1 = '期望的单据类型编码';
```

## 字段映射配置
- 单据字段映射、ES 对象管理、脚本 `SWBH_INIT` 等配置项在各自配置表，具体表名用 `archery_describe_table` / 业务文档核对。

## 常用核对 SQL 模板
```sql
-- 查某租户某待办编码的待办定义订阅条件
SELECT * FROM swbh_todo_definition WHERE tenant_id = ? AND todo_code = ?;

-- 查某单据待办数据（swbh_todo_document，srm_workbench 库）
SELECT * FROM swbh_todo_document WHERE tenant_id = ? AND document_id = ?;

-- 查消费失败记录
SELECT * FROM swbh_err_record WHERE tenant_id = ? ORDER BY creation_date DESC LIMIT 50;
```
