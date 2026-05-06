# ssrc_source_result_change_history 寻源结果变更历史表

## 表说明
寻源结果变更历史表，记录寻源结果被订单占用/释放的变更轨迹。仅在"寻源结果被订单错误占用"场景下，才需要操作此表。

## 核心字段（高频使用）

| 字段名 | 数据类型 | 说明 | 关联 |
|--------|----------|------|------|
| history_id | bigint | 主键 | — |
| tenant_id | bigint | 租户ID | hpfm_tenant.tenant_id |
| source_result_id | bigint | 寻源结果ID | ssrc_source_result.result_id |
| change_type | varchar | 变更类型：OCCUPY/占用、RELEASE/释放 | — |
| order_num | varchar | 订单编号 | — |
| order_line_id | bigint | 订单行ID | — |
| occupation_quantity | decimal | 占用数量 | — |
| remarks | varchar | 备注 | — |
| object_version_number | bigint | 行版本号（乐观锁） | — |
| creation_date | datetime | 创建日期 | — |
| created_by | bigint | 创建人 | — |
| last_updated_by | bigint | 最后更新人 | — |
| last_update_date | datetime | 最后更新日期 | — |

## 常用查询示例

```sql
-- 查询某寻源结果的变更历史
SELECT history_id,
       change_type,
       order_num,
       occupation_quantity,
       creation_date
FROM   ssrc_source_result_change_history
WHERE  tenant_id = 155357
  AND  source_result_id = {result_id}
ORDER BY creation_date DESC;

-- 查询被订单占用的寻源结果变更记录
SELECT h.history_id,
       h.source_result_id,
       h.order_num,
       h.occupation_quantity
FROM   ssrc_source_result_change_history h
WHERE  h.tenant_id = 155357
  AND  h.change_type = 'OCCUPY'
  AND  h.order_num = 'PO2026032600001';
```
