# 盘古（订单履约域）表关联关系与业务规则

本文件沉淀**数据库拿不到的业务知识**：表间关联、状态流转、上下游联动规则。字段级结构一律走 zhenyun-pangun-mcp 的 Archery 工具（`archery_describe_table` / `archery_list_columns`）。

---

## 一、主链路关联

```
寻源结果/申请/合同
   └─> sodr_po_header (po_header_id)                      -- 采购订单头
         ├─ 1:N sodr_po_line (po_line_id)                 -- 订单行
         │        └─ 1:N sodr_po_line_location            -- 发运行（数量占用核心）
         ├─ 1:1..N sodr_po_header_es / *_line_es / *_line_location_es   -- ERP 映射
         ├─ 1:N sodr_po_header_sign                       -- 电子签章
         └─ 1:N sodr_po_status_sync_record                -- 同步记录

发运行 sodr_po_line_location
   ├─（开启发货工作台）→ slod_delivery_init_info_link → slod_asn_*/slod_plan_*/slod_label_*
   ├─（未开启）→ sinv_asn_line.po_line_location_id（老送货单，占用 occupied_quantity）
   └─> sinv_rcv_trx_line.po_line_location_id              -- 收货事务行回写收发货数量

收货事务 sinv_rcv_trx_header (rcv_trx_header_id)
   ├─ 来源：sinv_rcv_trx_order_link（订单→事务链接）
   ├─ 1:N sinv_rcv_trx_line (rcv_trx_line_id)
   ├─ ES：sinv_rcv_trx_header_es / sinv_rcv_trx_line_es
   └─ 导出：sinv_rcv_change_record（import_type 区分推结算/推外部/推订单/推商城/推委外/...）
```

### 关键关联键
| 关系 | 关联键 |
|------|--------|
| 订单头 ↔ 行 ↔ 发运行 | `po_header_id` → `po_line_id` → `po_line_location_id` |
| 订单 ↔ 收货事务行 | `sinv_rcv_trx_line.po_header_id / po_line_id / po_line_location_id` |
| 订单 ↔ 发货工作台 | `slod_asn_line.po_line_location_id`（跨库，slod 在 `srm_logistics_delivery`） |
| 订单 ↔ 老送货单 | `sinv_asn_line.po_line_location_id` |
| 平台供应商 ↔ 本地供应商 | `sslm_external_supplier.link_id = sslm_supplier_basic.supplier_company_id` |
| 导出记录 ↔ 事务 | `sinv_rcv_change_record.source_document_id` + `source_document_table`（头/行维度） |

---

## 二、订单状态机规则（sodr_po_header）

状态由 `status_code` + 多个 flag 组合表达，修复必须**整组同步改**：

| 目标状态 | approved | erp_approval | released | confirmed | status_code | 附加动作 |
|----------|----------|--------------|----------|-----------|-------------|----------|
| 新建 | 0 | 0 | 0 | 0 | PENDING | 清 change_sync_status |
| 审批通过 | 1 | 1 | 0 | 0 | APPROVED | — |
| 已发布 | 1 | 1 | 1 | 0 | PUBLISHED | released_date=now()、清 po_upgrade_re_confirm_flag |
| 已确认 | 1 | 1 | 1 | 1 | PUBLISHED | 展示层按 confirmed_flag 翻译为已确认 |

附加规则：
1. **乐观锁**：所有 `sodr_*` 表 UPDATE 必带 `object_version_number = object_version_number + 1`。
2. **关闭/取消互斥**：`closed_flag` 与 `cancelled_flag` 不能同时为 1；取值 0/1/2/3（否/是/处理中/待确认）。
3. **整单取消**：头金额归零（`amount=0, tax_include_amount=0`）；行取消：发运行 `can_create_asn_flag=0`，并按剩余有效行重算头金额。
4. **下游联动**：订单确认→`sinv_rcv_trx_line.complete_flag=0`（打开待收货）；取消/关闭→`complete_flag=1`。
5. 状态推进/回退优先走平台标准修复接口或状态机（siec），SQL 直改仅限接口无法覆盖场景。

---

## 三、供应商与主数据修复规则

1. `pe_supplier` = `supplier_company_id` + `-` + `supplier_id`（**平台id-本地id**拼接）；`settle_pe_supplier` = `settle_supplier_id-settle_erp_supplier_id`；两者为空则不处理。
2. 修复公司字段时同步检查结算公司（`settle_company_id/settle_company_name`）。
3. 供应商编码字段命名差异（写 SQL 前必须核对）：
   - 订单头：`supplier_code`
   - 收货事务/老送货单：`supplier_num`
   - 发货工作台：`supplier_code`
4. 含税金额拼写差异：订单头 `tax_include_amount`，收货事务行 `tax_included_amount`。

---

## 四、ES 表（外部系统映射）联动规则

1. `*_es` 表保存 SRM 单据与外部系统（ERP 等）的映射。
2. **同步状态「成功→失败」：必须删除对应 ES 表数据**，否则残留映射导致重复/冲突。
3. 「失败→成功」：若无 ES 数据，需先修头/行业务表，再按业务表取值**插入** ES 数据。
4. 委外等清理场景：**先删 ES 表，再删业务表**。

---

## 五、导出/重推规则（sinv_rcv_change_record）

1. `import_status` 改回 `FAIL` 可触发重推；`IMPORTING` 表示进行中。
2. `import_type='SINV_TO_SODR'`（推订单）修复**必须极其谨慎**，可能影响订单数量/金额。
3. 对接多外部系统的租户：WHERE 必带 `external_system_code`。
4. 部分租户配置「导出外部成功才推结算」：修复推外部状态时关注结算联动。
5. 批量重推调度：`SINV_TO_SETTLE_BATCH_SYNC` / `SINV_TO_SLOD_BATCH_SYNC` / `SINV_TO_SODR_BATCH_SYNC`，复制临时任务加参 `{"importStatus":"IMPORTING"}`；分片配置表 `spuc_sinv_sitf_import_split_line` 需包含目标租户。

---

## 六、数据清理规则（上下游协同，缺一不可）

### 收货事务清理清单
`sinv_rcv_trx_order_link` → `sinv_rcv_trx_header/line` → `sinv_rcv_trx_header_es/line_es` → `sinv_rcv_trx_header_ext/line_ext` → `sinv_rcv_trx_score` → `sinv_rcv_record_strategy_mapping`；
若租户开启发货工作台，另含：`slod_idempotent_record`(record_type='10') + `slod_trx_dly_detail`。

### 发货工作台清理清单
`slod_delivery_init_info_link` → `slod_po_dly_record` → `slod_idempotent_record`(record_type='20') → ASN/PLAN/LABEL 三套头行 + 各自 `*_es` → `slod_delivery_header_ext/line_ext`(按 source_type) → `slod_dly_line_export_record` → `slod_po_dly_strategy_change_record`。

### 订单删除清单（6 张表）
`sodr_po_header` + `sodr_po_line` + `sodr_po_line_location` + 三张对应 `*_es`。
**删除前必须确认**：前置单据（申请/寻源结果/合同）数量占用释放、预算释放。

### 清理三原则
1. 只针对指定租户（WHERE 必带 tenant_id）；
2. 指定单据必须上下游协同清理（按上面清单逐表覆盖）;
3. 建议用 `SELECT concat('DELETE FROM xx WHERE ...')` 反查生成删除语句，人工复核后执行。

---

## 七、老送货单 vs 发货工作台（选表判断）

| 维度 | 老送货单 | 发货工作台 |
|------|----------|------------|
| 库/表 | `srm.sinv_asn_*`、`sinv_label_*` | `srm_logistics_delivery.slod_asn_*`、`slod_plan_*`、`slod_label_*` |
| 占用回写 | `sodr_po_line_location.occupied_quantity` | 经 `slod_delivery_init_info_link` 初始化管理 |
| 判断依据 | 租户未开启发货工作台 | `slod_node_config` 存在租户配置 |

不确定时：先查 `slod_node_config` 或向用户确认，**严禁两套表混用**。

---

## 八、留痕与安全（写入类通用）

1. 数据修复 UPDATE 统一带：`last_update_date = now()`；`sodr_*` 另带 `object_version_number+1`。
2. 建议留痕：`attribute_longtext10 = concat(IFNULL(attribute_longtext10,','),'数据修复/<工单号>')`（部分物流表用 `attribute_longtext60`，使用前用 `archery_list_columns` 校验字段是否存在）。
3. UPDATE/DELETE 必须以 `tenant_id + 主键` 定位；执行前保留同 WHERE 的 SELECT 核查段。
4. 事务导入/反审核/重推/订单初始化等场景**优先建议平台数据修复接口或调度**，SQL 直改为兜底手段。
