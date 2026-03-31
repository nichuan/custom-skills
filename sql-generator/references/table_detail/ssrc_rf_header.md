# ssrc_rf_header - 征询单头表

## 表说明
征询单头表，存储征询单（RFI/RFP）的头信息。是SRM采购寻源系统的核心业务表之一，记录征询单的基本信息和状态。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| rf_header_id | bigint(20) | 主键，征询单头ID | PRIMARY |
| tenant_id | bigint(20) | 租户ID | INDEX (idx_ssrc_rf_header_tenant_id) |
| rf_num | varchar(60) | RF单号 | UNIQUE (rf_num, tenant_id) |
| rf_title | varchar(500) | RF标题 | INDEX |
| template_id | bigint(20) | 寻源模板ID | INDEX |
| rf_status | varchar(30) | RF表状态 | INDEX |
| display_rf_status | varchar(30) | RF展示状态 | - |
| source_category | varchar(30) | RFI/RFP | INDEX |
| source_method | varchar(30) | 询价方式 | - |
| currency_code | varchar(30) | 币种 | - |
| company_id | bigint(20) | 采购方公司 | INDEX |
| unit_id | bigint(20) | 需求部门 | INDEX |
| pur_organization_id | bigint(20) | 采购方采购组织 | INDEX |
| pur_agent_id | bigint(20) | 采购员 | INDEX |
| pur_contact_id | bigint(20) | 采购联系人 | INDEX |
| pur_contact_email | varchar(240) | 采购联系人邮箱 | - |
| international_tel_code | varchar(30) | 国际电话区号 | - |
| pur_contact_phone | varchar(60) | 采购联系人电话 | - |
| rf_remark | longtext | 备注 | - |
| rfi_attachment_uuid | varchar(60) | RFI附件UUID | - |
| tech_attachment_uuid | varchar(60) | 技术附件UUID | - |
| business_attachment_uuid | varchar(60) | 商务附件UUID | - |
| current_sequence_num | tinyint(4) | 当前专家评分组别 | - |
| copy_rf_header_id | bigint(20) | 复制来源id | INDEX |
| current_node | varchar(30) | 当前节点 | - |
| source_nodes | varchar(500) | 流程节点 | - |
| released_date | datetime | 发布日期 | INDEX |
| released_by | bigint(20) | 发布人 | INDEX |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| notice_node_code | varchar(30) | 公告节点编码SSRC.RF_NOTICE_NODE_CODE(0/默认值&#124;10/发布成功&#124;20/专家评分完成&#124;40/入围名单确认&#124;30/退回至确认入围名单) | - |
| check_attachment_uuid | varchar(60) | 确定供应商附件UUID | - |
| approve_status | varchar(30) | RF审批状态 | INDEX |
| finishing_rate | int(11) | 维护完成率 | - |
| adjust_times | int(11) | 调整次数 | - |
| pre_attachment_uuid | varchar(60) | 评分推荐候选人附件 | - |
| source_project_id | bigint(20) | 寻源立项id | INDEX |
| source_from | varchar(30) | 单据来源 | - |
| finish_create_source | varchar(30) | 确定供应商完成后创建单据的类型 | - |
| rfx_template_id | bigint(20) | 创建询价单模板id | INDEX |
| close_date | datetime | 征询单关闭时间 | INDEX |
| close_by | bigint(20) | 征询单关闭人 | INDEX |
| close_remark | longtext | 征询单关闭理由 | - |
| close_attachment_uuid | varchar(60) | 征询单关闭附件 uuid | - |
| close_snap_by | bigint(20) | 临时征询单关闭人 | INDEX |
| close_snap_remark | longtext | 临时征询单关闭理由 | - |
| close_snap_attachment_uuid | varchar(60) | 临时征询单关闭附件 uuid | - |
| subject_matter_rule | varchar(30) | 标的规则SSRC.SUBJECT_MATTER_RULE(PACK/分标段包&#124;NONE/不区分) | - |
| benchmark_price_type | varchar(30) | 基准价(值集:SFIN.BENCHMARK_PRICE) | - |
| local_suggested_net_amount | decimal(20,6) | 本币建议选用未税税额 | - |
| local_suggested_tax_amount | decimal(20,6) | 本币建议选用税额 | - |
| local_suggested_total_amount | decimal(20,6) | 本币建议选用总金额 | - |
| finished_by | bigint(20) | 征询单完成人 | INDEX |

## 核心索引
- PRIMARY: `rf_header_id`
- UNIQUE: `ssrc_rf_header_u2` - (rf_num, tenant_id)
- INDEX: `idx_ssrc_rf_header_tenant_id` - (tenant_id)
- INDEX: `ssrc_rf_header_n2` - (template_id)
- INDEX: `ssrc_rf_header_n3` - (rf_status)
- INDEX: `ssrc_rf_header_n4` - (source_category)
- INDEX: `ssrc_rf_header_n5` - (company_id)
- INDEX: `ssrc_rf_header_n6` - (unit_id)
- INDEX: `ssrc_rf_header_n7` - (pur_organization_id)
- INDEX: `ssrc_rf_header_n8` - (pur_agent_id)
- INDEX: `ssrc_rf_header_n9` - (pur_contact_id)
- INDEX: `ssrc_rf_header_n10` - (copy_rf_header_id)
- INDEX: `ssrc_rf_header_n11` - (released_date)
- INDEX: `ssrc_rf_header_n12` - (released_by)
- INDEX: `ssrc_rf_header_n13` - (approve_status)
- INDEX: `ssrc_rf_header_n14` - (source_project_id)
- INDEX: `ssrc_rf_header_n15` - (rfx_template_id)
- INDEX: `ssrc_rf_header_n16` - (close_date)
- INDEX: `ssrc_rf_header_n17` - (close_by)
- INDEX: `ssrc_rf_header_n18` - (close_snap_by)
- INDEX: `ssrc_rf_header_n19` - (finished_by)
- INDEX: `ssrc_rf_header_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 征询单相关
- `ssrc_rf_action.rf_header_id` - 关联征询单操作记录
- `ssrc_rf_conf_rule.source_from_id` - 关联征询单配置规则
- `ssrc_rf_line_item.rf_header_id` - 关联征询单物料行
- `ssrc_rf_line_supplier.rf_header_id` - 关联征询单供应商行
- `ssrc_rf_quotation_header.rf_header_id` - 关联征询单报价头

## 常见查询场景

### 1. 根据征询单号查询征询单信息
```sql
SELECT rf_header_id, rf_num, rf_title, rf_status, source_category
FROM ssrc_rf_header
WHERE tenant_id = {tenant_id}
  AND rf_num = '{rf_num}';
```

### 2. 查询征询单的物料行信息
```sql
SELECT rf_line_item_id, item_code, item_name, demand_quantity
FROM ssrc_rf_line_item
WHERE tenant_id = {tenant_id}
  AND rf_header_id = {rf_header_id}
ORDER BY rf_line_item_num;
```

### 3. 查询征询单的供应商行信息
```sql
SELECT rf_line_supplier_id, supplier_company_name, feedback_status
FROM ssrc_rf_line_supplier
WHERE tenant_id = {tenant_id}
  AND rf_header_id = {rf_header_id};
```

### 4. 查询征询单的报价头信息
```sql
SELECT quotation_header_id, quotation_num, quotation_status, supplier_company_name
FROM ssrc_rf_quotation_header
WHERE tenant_id = {tenant_id}
  AND rf_header_id = {rf_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **唯一标识**：`(rf_num, tenant_id)` 组合唯一
3. **状态管理**：支持多种状态（新建、审批中、已发布、已关闭等）
4. **来源类型**：支持RFI（信息征询书）和RFP（方案征询书）
5. **复制功能**：支持从其他征询单复制
6. **关闭功能**：支持征询单的关闭操作
