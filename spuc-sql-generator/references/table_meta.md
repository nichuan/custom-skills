# 盘古（订单履约域）核心表元数据

本文件是 **业务语义 / 速查层**：仅沉淀数据库拿不到、或高频复用容易写错的业务语义（主键、关联、状态/枚举速查、库归属）。
**表的原始结构（字段名、类型、注释、拓展字段、索引）一律通过 sql-ops MCP 实时获取**（详见 `SKILL.md`）：

- `describe_table('<表名>')` —— 返回完整字段清单与表注释
- `validate_table_columns('<表名>', ['字段A','字段B'])` —— 校验字段是否存在

## 库归属（重要）

| 库 | 表前缀 | 说明 |
|----|--------|------|
| `srm` | `sodr_*`、`sinv_*`、`spuc_*`、`sslm_*`、`hpfm_*`、`iam_*`、`siec_*` | 订单、收货事务、老送货单、主数据、状态机 |
| `srm_logistics_delivery` | `slod_*` | 发货工作台（送货单/送货计划/标签），跨库 JOIN 必须带库名前缀 |

## 元数据格式
- **表名**: 主键、核心字段、关联键(外键)

---

## 核心表列表

### 基础平台 / 主数据
- **hpfm_tenant**: tenant_id(主键)、tenant_num(租户编码)、tenant_name(租户名)、enabled_flag
- **hpfm_company**: company_id(主键)、tenant_id、company_num(公司编码)、company_name(公司名称)
- **iam_user**: id(主键，业务表人员ID指向此id)、organization_id(等价tenant_id)、login_name、real_name
- **sslm_supplier_basic**: supplier_company_id(主键，平台供应商id)、tenant_id、supplier_company_name、supplier_num
- **sslm_external_supplier**: supplier_id(主键，本地供应商id)、tenant_id、link_id(**=平台supplier_company_id**)、supplier_name、supplier_num
- **spfm_operation_unit**: operation_unit_id(主键，业务实体OU)、tenant_id、ou_code、ou_name
- **spcm_item**: item_id(主键，物料)、tenant_id、item_code、item_name
- **spfm_inv_organization**: inv_organization_id(主键，库存组织)、tenant_id、organization_code
- **spfm_uom**: uom_id(主键，单位)、tenant_id、uom_code、uom_name

### 采购订单（SODR）
- **sodr_po_header**: po_header_id(主键)、tenant_id、po_num(订单号)、status_code、approved_flag、erp_approval_flag、released_flag、confirmed_flag、closed_flag、cancelled_flag、change_sync_status、amount、tax_include_amount(**含税金额，注意与收货行 tax_included_amount 拼写不同**)、supplier_company_id、supplier_id、pe_supplier(平台id-本地id拼接)、settle_pe_supplier、company_id、object_version_number(**乐观锁，更新必须+1**)
- **sodr_po_line**: po_line_id(主键)、po_header_id(关联sodr_po_header)、tenant_id、line_num、item_id、item_code、quantity、closed_flag、cancelled_flag、object_version_number
- **sodr_po_line_location**: po_line_location_id(主键，**发运行**)、po_line_id(关联sodr_po_line)、po_header_id、tenant_id、quantity、shipped_quantity、received_quantity、returned_quantity、occupied_quantity(送货占用)、can_create_asn_flag(可制单标识)、closed_flag、cancelled_flag、object_version_number
- **sodr_po_header_es / sodr_po_line_es / sodr_po_line_location_es**: 订单头/行/发运行与外部系统(ERP)映射；同步失败需删除对应 ES 数据
- **sodr_po_header_sign**: sign_id(主键)、po_header_id、tenant_id、electric_sign_status(EFFECTED已生效/CANCELLATION已作废)
- **sodr_po_status_sync_record**: record_id(主键)、tenant_id、po_header_id、sync_type(SRM_EXP_ERP新建同步/DELIVERY_EXP_ERP交期同步/ORDER_DELIVERY_WORK订单同步发货工作台)、sync_status(SUCCESS/FAIL)
- **sodr_consumer_idempotent**: 消息消费幂等记录（订单/发货消息）
- **sodr_po_change_record**: 订单变更/操作记录

### 收货工作台事务（SINV_RCV）
- **sinv_rcv_trx_header**: rcv_trx_header_id(主键)、tenant_id、rcv_trx_num(事务单号)、trx_type_code(事务类型)、rcv_trx_status、supplier_num(**收货侧用 supplier_num**)、company_id
- **sinv_rcv_trx_line**: rcv_trx_line_id(主键)、rcv_trx_header_id(关联sinv_rcv_trx_header)、tenant_id、po_header_id、po_line_id、po_line_location_id(关联订单发运行)、quantity、tax_included_amount(**注意拼写**)、complete_flag(待收货完成标识，订单确认→0、取消/关闭→1)
- **sinv_rcv_trx_order_link**: link_id(主键)、tenant_id、rcv_trx_header_id、来源单据链接（订单→收货事务）
- **sinv_rcv_trx_header_es / sinv_rcv_trx_line_es**: 收货事务与外部系统映射
- **sinv_rcv_trx_header_ext / sinv_rcv_trx_line_ext**: 收货事务扩展表
- **sinv_rcv_change_record**: record_id(主键)、tenant_id、source_document_id、source_document_table(sinv_rcv_trx_header头维度/sinv_rcv_trx_line行维度)、import_type(见枚举)、import_status(SUCCESS/FAIL/IMPORTING)、external_system_code(外部系统编码，多外部系统时WHERE必带)
- **sinv_rcv_trx_score**: 收货事务评分
- **sinv_rcv_record_strategy_mapping**: 收货记录与策略映射
- **spuc_sinv_sitf_import_split_line**: 收货批量同步调度分片配置（重推调度需含租户）

#### sinv_rcv_change_record.import_type 枚举速查
| 值 | 含义 |
|----|------|
| SETTLE | 推结算 |
| SINV_TO_SLOD | 推发货工作台 |
| SINV_TO_SODR | 推订单（**修复须极谨慎**） |
| SINV_TO_PR | 推申请 |
| RCV_EXPORT | 推外部（ERP等） |
| SINV_TO_MALL | 推商城 |
| SINV_TO_OUTSOURCE | 推委外 |
| ANT_AUDIT | 反审核 |

### 发货工作台（SLOD，库：srm_logistics_delivery）
- **slod_asn_header**: asn_header_id(主键)、tenant_id、asn_num(送货单号)、asn_status、supplier_code(**发货侧用 supplier_code**)
- **slod_asn_line**: asn_line_id(主键)、asn_header_id(关联slod_asn_header)、tenant_id、po_header_id、po_line_id、po_line_location_id、quantity
- **slod_plan_header / slod_plan_line**: 送货计划头/行（plan_header_id / plan_line_id）
- **slod_label_header / slod_label_line**: 标签头/行（label_header_id / label_line_id）
- **slod_asn_header_es / slod_asn_line_es**（及 plan/label 对应 es 表）: 与外部系统映射
- **slod_delivery_init_info_link**: 订单初始化发货链接（订单发运行→发货工作台）
- **slod_po_dly_record**: 订单发货记录
- **slod_idempotent_record**: 幂等记录，record_type：'10'=收货、'20'=订单初始化
- **slod_trx_dly_detail**: 收货事务发货明细
- **slod_delivery_header_ext / slod_delivery_line_ext**: 发货扩展表（按 source_type 区分 ASN/PLAN/LABEL）
- **slod_dly_line_export_record**: 发货行导出记录
- **slod_po_dly_strategy_change_record**: 发货策略变更记录
- **slod_node_config**: 租户发货工作台节点配置（判断租户是否开启发货工作台）

### 老送货单（SINV_ASN，库：srm）
- **sinv_asn_header**: asn_header_id(主键)、tenant_id、asn_num、asn_status、supplier_num
- **sinv_asn_line**: asn_line_id(主键)、asn_header_id(关联sinv_asn_header)、tenant_id、po_header_id、po_line_location_id、quantity
- **sinv_asn_header_es / sinv_asn_line_es**: 老送货单与外部系统映射
- **sinv_label_header / sinv_label_line**: 老标签头/行

> ⚠️ **老送货单（sinv_asn_\*）与发货工作台送货单（slod_asn_\*）是两套独立表体系**，先确认租户是否开启发货工作台再选表。

### 委外（SINV_OUTSOURCE）
- **sinv_outsource_\* 系列**: 委外单据表（结构用 describe_table 实时获取）；清理时**先删 ES 表、再删业务表**

### 状态机（SIEC）
- **siec_\* 系列**: 单据状态机流转记录（结构用 describe_table 实时获取）；排查状态卡住时结合状态机流转记录与业务表状态字段核对

---

## 高频状态/枚举速查

### sodr_po_header.status_code（LOV: SODR.PO_STATUS）
`PENDING`(新建) / `APPROVING`(审批中) / `APPROVED`(审批通过) / `PUBLISHED`(已发布，confirmed_flag=1 时展示为已确认) / `REJECTED`(拒绝)

### 通用 closed_flag / cancelled_flag 取值
`0`=否、`1`=是、`2`=处理中、`3`=待确认（如 cancelled_flag=3 为取消待确认）。**关闭与取消互斥。**

### import_status（sinv_rcv_change_record 等）
`SUCCESS` / `FAIL`（改回 FAIL 可触发重推）/ `IMPORTING`

---

## 维护说明

1. 新表按上述格式添加，标注主键、关联键与**库归属**
2. 仅列出高频使用的 3-5 个核心字段
3. 状态/枚举等数据库拿不到的业务知识沉淀在此文件
4. 完整 SQL 示例通过 sql-template MCP 的 `save_sql_template` 沉淀（category 用盘古专属分类，见 `SKILL.md`）

### 表命名规范
- **sodr_**: 采购订单域
- **sinv_**: 收货/老送货/委外域
- **slod_**: 发货工作台域（独立库 srm_logistics_delivery）
- **spuc_**: 盘古采购公共配置
- **siec_**: 状态机
- **sslm_**: 供应商主数据；**hpfm_/iam_/spfm_/spcm_**: 平台与主数据
