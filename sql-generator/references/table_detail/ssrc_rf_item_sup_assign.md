# ssrc_rf_item_sup_assign - 征询单物料供应商分配表

## 表说明
征询单物料供应商分配表，存储征询单物料行与供应商的分配关系。是SRM采购寻源系统的核心业务表之一，记录哪些供应商被邀请报价哪些物料。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| item_sup_assign_id | bigint(20) | 主键，物料供应商分配ID | PRIMARY |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_rf_item_sup_assign_tenant_id) |
| rf_header_id | bigint(20) | 征询单头ID | INDEX |
| rf_line_item_id | bigint(20) | 征询单物料行ID | INDEX |
| rf_line_supplier_id | bigint(20) | 征询单供应商行ID | INDEX |
| max_limit_price | decimal(20,6) | 最高限价 | - |
| min_limit_price | decimal(20,6) | 最低限价 | - |
| invite_flag | tinyint(1) | 邀请标志 | - |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |

## 核心索引
- PRIMARY: `item_sup_assign_id`
- INDEX: `idx_ssrc_rf_item_sup_assign_tenant_id` - (tenant_id)
- INDEX: `ssrc_rf_item_sup_assign_n2` - (rf_header_id)
- INDEX: `ssrc_rf_item_sup_assign_n3` - (rf_line_item_id)
- INDEX: `ssrc_rf_item_sup_assign_n4` - (rf_line_supplier_id)
- INDEX: `ssrc_rf_item_sup_assign_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 征询单相关
- 通过 `rf_header_id` 关联征询单头表 `ssrc_rf_header`
- 通过 `rf_line_item_id` 关联征询单物料行表 `ssrc_rf_line_item`
- 通过 `rf_line_supplier_id` 关联征询单供应商行表 `ssrc_rf_line_supplier`

## 常见查询场景

### 1. 根据征询单ID查询物料供应商分配列表
```sql
SELECT item_sup_assign_id, rf_line_item_id, rf_line_supplier_id, max_limit_price, min_limit_price
FROM ssrc_rf_item_sup_assign
WHERE tenant_id = {tenant_id}
  AND rf_header_id = {rf_header_id};
```

### 2. 根据物料行ID查询供应商分配信息
```sql
SELECT item_sup_assign_id, rf_line_supplier_id, max_limit_price, min_limit_price, invite_flag
FROM ssrc_rf_item_sup_assign
WHERE tenant_id = {tenant_id}
  AND rf_line_item_id = {rf_line_item_id};
```

### 3. 根据供应商行ID查询物料分配信息
```sql
SELECT item_sup_assign_id, rf_line_item_id, max_limit_price, min_limit_price, invite_flag
FROM ssrc_rf_item_sup_assign
WHERE tenant_id = {tenant_id}
  AND rf_line_supplier_id = {rf_line_supplier_id};
```

### 4. 查询征询单的物料供应商分配详情
```sql
SELECT isa.item_sup_assign_id, rli.item_code, rli.item_name, 
       rls.supplier_company_name, isa.max_limit_price, isa.min_limit_price
FROM ssrc_rf_item_sup_assign isa
INNER JOIN ssrc_rf_line_item rli ON isa.rf_line_item_id = rli.rf_line_item_id
INNER JOIN ssrc_rf_line_supplier rls ON isa.rf_line_supplier_id = rls.rf_line_supplier_id
WHERE isa.tenant_id = {tenant_id}
  AND isa.rf_header_id = {rf_header_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **征询单关联**：通过 `rf_header_id` 关联征询单头表
3. **物料行关联**：通过 `rf_line_item_id` 关联征询单物料行表
4. **供应商行关联**：通过 `rf_line_supplier_id` 关联征询单供应商行表
5. **限价控制**：支持设置最高限价和最低限价
6. **邀请标志**：`invite_flag = 1` 表示已邀请该供应商报价该物料
