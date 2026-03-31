# ssrc_rf_line_item - 征询单物料行表

## 表说明
征询单物料行表，存储征询单的物料行信息。是SRM采购寻源系统的核心业务表之一，记录征询单的物料需求明细。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| rf_line_item_id | bigint(20) | 主键，物料行ID | PRIMARY |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_rf_line_item_tenant_id) |
| rf_header_id | bigint(20) | 征询单头ID | INDEX |
| rf_line_item_num | int(11) | 行号 | - |
| ou_id | bigint(20) | 业务实体 | INDEX |
| inv_organization_id | bigint(20) | 库存组织 | INDEX |
| item_id | bigint(20) | 物料ID | INDEX |
| item_code | varchar(60) | 物料代码 | INDEX |
| item_name | varchar(500) | 物料名称 | - |
| item_category_id | bigint(20) | 物品类别 | INDEX |
| item_specs | varchar(500) | 物料规格 | - |
| demand_quantity | decimal(20,6) | 需求数量 | - |
| price_batch | decimal(20,6) | 价格批量 | - |
| uom_id | bigint(20) | 单位 | - |
| tax_included_flag | tinyint(1) | 含税标识 | - |
| tax_id | bigint(20) | 税率ID | INDEX |
| tax_rate | decimal(5,2) | 税率 | - |
| demand_date | date | 需求日期 | INDEX |
| ladder_inquiry_flag | tinyint(1) | 阶梯报价标志 | - |
| attachment_uuid | varchar(60) | 附件UUID | - |
| pr_header_id | bigint(20) | 申请头id | INDEX |
| pr_line_id | bigint(20) | 申请行id | INDEX |
| pr_num | varchar(60) | 申请编号 | INDEX |
| pr_line_num | int(11) | 申请行号 | - |
| pr_display_line_num | varchar(30) | 采购申请行展示行号 | - |
| project_line_section_id | bigint(20) | 标段id | INDEX |
| project_line_item_id | bigint(20) | 立项物料行ID | INDEX |
| copy_rf_line_item_id | bigint(20) | 复制原行id | INDEX |
| selection_strategy | varchar(30) | 询价单选择策略SSRC.RFX_ SELECTION_STRATEGY(RECOMMENDATION/推荐供应商&#124; RELEASE/释放采购申请&#124; CANCEL/不释放采购申请) | - |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| project_task_id | bigint(20) | 项目信息id，关联siec_project_task | INDEX |
| rf_line_section_id | bigint(20) | 征询标段id | INDEX |
| source_rf_line_id | bigint(20) | rfi 转RFP RFI 物料行id | INDEX |
| secondary_uom_id | bigint(20) | 辅助单位ID | - |
| secondary_quantity | decimal(20,6) | 辅助数量 | - |

## 核心索引
- PRIMARY: `rf_line_item_id`
- INDEX: `idx_ssrc_rf_line_item_tenant_id` - (tenant_id)
- INDEX: `ssrc_rf_line_item_n2` - (rf_header_id)
- INDEX: `ssrc_rf_line_item_n3` - (ou_id)
- INDEX: `ssrc_rf_line_item_n4` - (inv_organization_id)
- INDEX: `ssrc_rf_line_item_n5` - (item_id)
- INDEX: `ssrc_rf_line_item_n6` - (item_code)
- INDEX: `ssrc_rf_line_item_n7` - (item_category_id)
- INDEX: `ssrc_rf_line_item_n8` - (tax_id)
- INDEX: `ssrc_rf_line_item_n9` - (demand_date)
- INDEX: `ssrc_rf_line_item_n10` - (pr_header_id)
- INDEX: `ssrc_rf_line_item_n11` - (pr_line_id)
- INDEX: `ssrc_rf_line_item_n12` - (pr_num)
- INDEX: `ssrc_rf_line_item_n13` - (project_line_section_id)
- INDEX: `ssrc_rf_line_item_n14` - (project_line_item_id)
- INDEX: `ssrc_rf_line_item_n15` - (copy_rf_line_item_id)
- INDEX: `ssrc_rf_line_item_n16` - (project_task_id)
- INDEX: `ssrc_rf_line_item_n17` - (rf_line_section_id)
- INDEX: `ssrc_rf_line_item_n18` - (source_rf_line_id)
- INDEX: `ssrc_rf_line_item_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 征询单相关
- 通过 `rf_header_id` 关联征询单头表 `ssrc_rf_header`
- `ssrc_rf_item_sup_assign.rf_line_item_id` - 关联物料供应商分配表
- `ssrc_rf_quotation_line.rf_line_item_id` - 关联征询单报价行表

## 常见查询场景

### 1. 根据征询单ID查询物料行列表
```sql
SELECT rf_line_item_id, item_code, item_name, demand_quantity, uom_id, demand_date
FROM ssrc_rf_line_item
WHERE tenant_id = {tenant_id}
  AND rf_header_id = {rf_header_id}
ORDER BY rf_line_item_num;
```

### 2. 根据物料编码查询征询单物料行
```sql
SELECT rf_line_item_id, rf_header_id, item_code, item_name, demand_quantity
FROM ssrc_rf_line_item
WHERE tenant_id = {tenant_id}
  AND item_code = '{item_code}';
```

### 3. 查询征询单的报价行信息
```sql
SELECT rli.rf_line_item_id, rli.item_code, rql.quotation_line_status, rql.valid_quotation_price
FROM ssrc_rf_line_item rli
INNER JOIN ssrc_rf_quotation_line rql ON rli.rf_line_item_id = rql.rf_line_item_id
WHERE rli.tenant_id = {tenant_id}
  AND rli.rf_header_id = {rf_header_id};
```

### 4. 查询征询单的物料供应商分配信息
```sql
SELECT rli.rf_line_item_id, rli.item_code, isa.rf_line_supplier_id, isa.max_limit_price
FROM ssrc_rf_line_item rli
INNER JOIN ssrc_rf_item_sup_assign isa ON rli.rf_line_item_id = isa.rf_line_item_id
WHERE rli.tenant_id = {tenant_id}
  AND rli.rf_header_id = {rf_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **征询单关联**：通过 `rf_header_id` 关联征询单头表
3. **采购申请关联**：通过 `pr_header_id` 和 `pr_line_id` 关联采购申请
4. **立项关联**：通过 `project_line_item_id` 关联立项物料行
5. **标段关联**：通过 `project_line_section_id` 关联标段
6. **双单位支持**：支持辅助单位和辅助数量
7. **阶梯报价**：支持阶梯报价功能
