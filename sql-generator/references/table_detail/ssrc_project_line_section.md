# ssrc_project_line_section - 寻源立项标段/包表

## 表说明
寻源立项标段/包表，存储寻源立项单的标段/包信息。是SRM采购寻源系统的核心业务表之一，用于将寻源立项的物料分组管理。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| project_line_section_id | bigint(20) | 主键，标段/包ID | PRIMARY |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_project_line_section_tenant_id) |
| source_project_id | bigint(20) | 寻源立项id | INDEX |
| section_num | bigint(20) | 标段/包行号 | - |
| section_code | varchar(60) | 标段/包编号 | INDEX |
| section_name | varchar(240) | 标段/包名称 | INDEX |
| section_remark | varchar(500) | 标段/包备注 | - |
| section_attachment_uuid | varchar(60) | 标段/包附件 | - |
| reference_flag | tinyint(1) | 引用标识 | - |
| source_header_id | bigint(20) | 被引用单据id | INDEX |
| source_from | varchar(30) | 被引用单据类型 | - |
| source_header_num | varchar(60) | 被引用单据编号 | INDEX |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| finish_flag | tinyint(1) | 寻源/招标单完成标识 | - |
| temp_source_header_id | bigint(20) | 临时单据Id | INDEX |
| create_source_flag | tinyint(1) | 发布寻源单标识 | - |
| section_estimated_amount | decimal(20,6) | 标段预估金额 | - |

## 核心索引
- PRIMARY: `project_line_section_id`
- INDEX: `idx_ssrc_project_line_section_tenant_id` - (tenant_id)
- INDEX: `ssrc_project_line_section_n2` - (source_project_id)
- INDEX: `ssrc_project_line_section_n3` - (section_code)
- INDEX: `ssrc_project_line_section_n4` - (section_name)
- INDEX: `ssrc_project_line_section_n5` - (source_header_id)
- INDEX: `ssrc_project_line_section_n6` - (source_header_num)
- INDEX: `ssrc_project_line_section_n7` - (temp_source_header_id)
- INDEX: `ssrc_project_line_section_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 寻源立项相关
- `ssrc_project_line_item.project_line_section_id` - 关联立项物料行的标段/包ID

### 询价单相关
- `ssrc_rfx_header.project_line_section_id` - 关联询价单的标段/包ID
- `ssrc_rfx_line_item.project_line_section_id` - 关联询价单物料行的标段/包ID

## 常见查询场景

### 1. 根据寻源立项ID查询标段/包列表
```sql
SELECT project_line_section_id, section_code, section_name, section_estimated_amount
FROM ssrc_project_line_section
WHERE tenant_id = {tenant_id}
  AND source_project_id = {source_project_id}
ORDER BY section_num;
```

### 2. 根据标段编码查询标段信息
```sql
SELECT project_line_section_id, source_project_id, section_code, section_name
FROM ssrc_project_line_section
WHERE tenant_id = {tenant_id}
  AND section_code = '{section_code}';
```

### 3. 查询询价单关联的标段信息
```sql
SELECT rfx.rfx_num, rfx.rfx_title, pls.section_code, pls.section_name
FROM ssrc_rfx_header rfx
INNER JOIN ssrc_project_line_section pls ON rfx.project_line_section_id = pls.project_line_section_id
WHERE rfx.tenant_id = {tenant_id}
  AND rfx.rfx_header_id = {rfx_header_id};
```

### 4. 查询标段下的物料行信息
```sql
SELECT pli.project_line_item_id, pli.item_code, pli.item_name, pli.required_quantity
FROM ssrc_project_line_item pli
WHERE pli.tenant_id = {tenant_id}
  AND pli.project_line_section_id = {project_line_section_id}
ORDER BY pli.project_line_item_num;
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **寻源立项关联**：通过 `source_project_id` 关联寻源立项头表
3. **引用标识**：`reference_flag = 1` 表示该标段引用了其他单据
4. **完成标识**：`finish_flag = 1` 表示寻源/招标单已完成
5. **发布标识**：`create_source_flag = 1` 表示已发布寻源单
