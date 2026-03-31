# ssrc_rfx_item_sup_assign 表详细结构

询价单物料供应商分配表

## 表信息
- **表名**: ssrc_rfx_item_sup_assign
- **主键**: item_sup_assign_id
- **外键**: rfx_header_id（关联 ssrc_rfx_header.rfx_header_id），rfx_line_supplier_id（关联 ssrc_rfx_line_supplier.rfx_line_supplier_id）
- **说明**: 存储询价单中每个供应商被分配的物料信息，1个供应商可以被分配多个物料

## 核心字段详情

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| item_sup_assign_id | bigint | 物料供应商分配ID（主键） |
| rfx_header_id | bigint | 询价单头ID |
| rfx_line_supplier_id | bigint | 供应商行ID |
| tenant_id | bigint | 所属租户ID |
| rfx_line_item_id | bigint | 物料行ID |
| invite_flag | tinyint | 邀请标识：0=未邀请，1=已邀请 |
| object_version_number | bigint | 行版本号，用来处理锁 |
| creation_date | datetime | 创建日期 |
| last_update_date | datetime | 最后更新日期 |

## 常用查询

### 查询询价单下某供应商的物料分配情况
```sql
SELECT isa.item_sup_assign_id,
       isa.rfx_line_item_id,
       isa.invite_flag,
       rli.item_code,
       rli.item_name
FROM ssrc_rfx_item_sup_assign isa
LEFT JOIN ssrc_rfx_line_item rli ON isa.rfx_line_item_id = rli.rfx_line_item_id
WHERE isa.tenant_id = 170091
  AND isa.rfx_header_id = 6014964
  AND isa.rfx_line_supplier_id = 16081474;
```

### 查询询价单下所有供应商的物料分配情况
```sql
SELECT isa.item_sup_assign_id,
       rls.supplier_company_name,
       rli.item_code,
       rli.item_name,
       isa.invite_flag
FROM ssrc_rfx_item_sup_assign isa
LEFT JOIN ssrc_rfx_line_supplier rls ON isa.rfx_line_supplier_id = rls.rfx_line_supplier_id
LEFT JOIN ssrc_rfx_line_item rli ON isa.rfx_line_item_id = rli.rfx_line_item_id
WHERE isa.tenant_id = 170091
  AND isa.rfx_header_id = 6014964
ORDER BY rls.supplier_company_name, rli.item_code;
```

### 统计供应商已分配物料数量
```sql
SELECT rls.supplier_company_name,
       COUNT(*) AS total_items,
       SUM(CASE WHEN isa.invite_flag = 1 THEN 1 ELSE 0 END) AS invited_items
FROM ssrc_rfx_item_sup_assign isa
LEFT JOIN ssrc_rfx_line_supplier rls ON isa.rfx_line_supplier_id = rls.rfx_line_supplier_id
WHERE isa.tenant_id = 170091
  AND isa.rfx_header_id = 6014964
GROUP BY rls.supplier_company_name;
```
