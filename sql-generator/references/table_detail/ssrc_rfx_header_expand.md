# ssrc_rfx_header_expand 表详细结构

询价单头拓展表

## 表信息
- **表名**: ssrc_rfx_header_expand
- **主键**: rfx_header_expand_id
- **外键**: rfx_header_id（关联 ssrc_rfx_header.rfx_header_id），1:1 关系
- **说明**: 存储询价单的计算状态和扩展信息，与询价单头 1:1 关联

## 字段详情

| 字段名                 | 数据类型  | 说明                     |
|-----------------------|-----------|--------------------------|
| rfx_header_expand_id  | bigint    | 主键                     |
| rfx_header_id         | bigint    | 询价单头ID               |
| tenant_id             | bigint    | 所属租户ID               |
| rfx_real_status       | varchar   | 询价单计算后的实际状态   |
| rfx_secondary_status  | varchar   | 询价单二级状态           |
| bidding_status        | varchar   | 竞价单竞价状态           |
| error_flag            | tinyint   | 错误标识                 |
| error_message         | longtext  | 错误信息                 |
| error_times           | bigint    | 错误次数                 |
| object_version_number | bigint    | 行版本号，用来处理锁     |
| creation_date         | datetime  | 创建日期                 |
| created_by            | bigint    | 创建人                   |
| last_updated_by       | bigint    | 最后更新人               |
| last_update_date      | datetime  | 最后更新日期             |

## 常用查询

### 查询询价单拓展信息
```sql
SELECT * FROM ssrc_rfx_header_expand
WHERE tenant_id = 155357 AND rfx_header_id = 5923933;
```

### 关联查询询价单和拓展信息
```sql
SELECT h.rfx_header_id, h.rfx_num, h.rfx_status,
       e.rfx_real_status, e.bidding_status
FROM ssrc_rfx_header h
INNER JOIN ssrc_rfx_header_expand e ON h.rfx_header_id = e.rfx_header_id
WHERE h.tenant_id = 155357 AND h.rfx_header_id = 5923933;
```

## 注意事项
- 与 `ssrc_rfx_header` 是 1:1 关系
- `rfx_real_status` 是系统计算后的状态，可能与 `rfx_header.rfx_status` 不同
- 主要用于存储询价单的计算状态，避免频繁更新主表
