# ssrc_project_line_item - 寻源立项物料行表

## 表说明
寻源立项物料行表，存储寻源立项单的物料行信息。是SRM采购寻源系统的核心业务表之一，记录寻源立项的物料需求明细。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| project_line_item_id | bigint(20) | 主键，物料行ID | PRIMARY |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_project_line_item_tenant_id) |
| source_project_id | bigint(20) | 寻源立项id | INDEX |
| project_line_item_num | bigint(20) | 行号 | - |
| ou_id | bigint(20) | 业务实体 | INDEX |
| inv_organization_id | bigint(20) | 库存组织 | INDEX |
| item_id | bigint(20) | 物料id | INDEX |
| item_code | varchar(60) | 物料编码 | INDEX |
| item_name | varchar(500) | 物料描述 | - |
| item_category_id | bigint(20) | 物料类别id | INDEX |
| item_remark | longtext | 物料备注 | - |
| item_attachment_uuid | varchar(60) | 物料行附件 | - |
| uom_id | bigint(20) | 单位id | - |
| required_quantity | decimal(20,6) | 需求数量 | - |
| cost_price | decimal(20,6) | 成本价 | - |
| total_price | decimal(20,6) | 总价 | - |
| pr_header_id | bigint(20) | 申请头id | INDEX |
| pr_num | varchar(60) | 申请编号 | INDEX |
| pr_line_id | bigint(20) | 申请行id | INDEX |
| pr_line_num | int(11) | 申请行号 | - |
| request_user_id | bigint(20) | 申请人 | - |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| executable_quantity | decimal(20,6) | 可执行数量 | - |
| occupied_quantity | decimal(20,6) | 已占用数量 | - |
| executing_status | varchar(30) | 执行状态 | - |
| project_task_id | bigint(20) | 项目信息id，关联siec_project_task | INDEX |
| specifications | varchar(500) | 规格 | - |
| model | varchar(100) | 型号 | - |
| project_line_section_id | bigint(20) | 标段/包id | INDEX |
| estimated_price | decimal(20,6) | 预估单价 | - |
| estimated_amount | decimal(20,6) | 预估金额 | - |
| occupationQuantity | decimal(20,6) | 已占用数量 | - |
| pr_display_line_num | varchar(30) | 采购申请行展示行号 | - |
| quotation_template_id | bigint(20) | 报价模板id | INDEX |
| execution_strategy_code | varchar(30) | 执行策略编码 | - |
| secondary_uom_id | bigint(20) | 辅助单位ID | - |
| secondary_quantity | decimal(20,6) | 辅助数量 | - |
| price_batch | decimal(20,6) | 价格批量 | - |
| quotation_detail_init_flag | tinyint(1) | 报价明细初始化标识 | - |

## 核心索引
- PRIMARY: `project_line_item_id`
- INDEX: `idx_ssrc_project_line_item_tenant_id` - (tenant_id)
- INDEX: `ssrc_project_line_item_n2` - (source_project_id)
- INDEX: `ssrc_project_line_item_n3` - (ou_id)
- INDEX: `ssrc_project_line_item_n4` - (inv_organization_id)
- INDEX: `ssrc_project_line_item_n5` - (item_id)
- INDEX: `ssrc_project_line_item_n6` - (item_code)
- INDEX: `ssrc_project_line_item_n7` - (item_category_id)
- INDEX: `ssrc_project_line_item_n8` - (pr_header_id)
- INDEX: `ssrc_project_line_item_n9` - (pr_num)
- INDEX: `ssrc_project_line_item_n10` - (pr_line_id)
- INDEX: `ssrc_project_line_item_n11` - (project_task_id)
- INDEX: `ssrc_project_line_item_n12` - (project_line_section_id)
- INDEX: `ssrc_project_line_item_n13` - (quotation_template_id)
- INDEX: `ssrc_project_line_item_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 询价单相关
- `ssrc_rfx_line_item.project_line_item_id` - 关联询价单物料行的立项物料行ID

### 其他业务表
- 通过 `source_project_id` 关联寻源立项头表
- 通过 `pr_header_id` 和 `pr_line_id` 关联采购申请

## 常见查询场景

### 1. 根据寻源立项ID查询物料行列表
```sql
SELECT project_line_item_id, item_code, item_name, required_quantity, uom_id
FROM ssrc_project_line_item
WHERE tenant_id = {tenant_id}
  AND source_project_id = {source_project_id}
ORDER BY project_line_item_num;
```

### 2. 根据物料编码查询立项物料行
```sql
SELECT project_line_item_id, source_project_id, item_code, item_name, required_quantity
FROM ssrc_project_line_item
WHERE tenant_id = {tenant_id}
  AND item_code = '{item_code}';
```

### 3. 查询询价单关联的立项物料行信息
```sql
SELECT rli.rfx_line_item_id, rli.item_code, pli.required_quantity, pli.estimated_price
FROM ssrc_rfx_line_item rli
INNER JOIN ssrc_project_line_item pli ON rli.project_line_item_id = pli.project_line_item_id
WHERE rli.tenant_id = {tenant_id}
  AND rli.rfx_header_id = {rfx_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **寻源立项关联**：通过 `source_project_id` 关联寻源立项头表
3. **采购申请关联**：通过 `pr_header_id` 和 `pr_line_id` 关联采购申请
4. **标段关联**：通过 `project_line_section_id` 关联标段/包
5. **双单位支持**：支持辅助单位和辅助数量
