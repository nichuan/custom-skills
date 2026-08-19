# 配置表（虚拟表）——非物理表

> 企业事实层。配置表是一种虚拟表，不是数据库物理表。其「结构定义」与「数据」分别存在两张特定物理表里，被大量用于标准代码和二开逻辑。**排障时在物理库里找不到某张表，大概率它其实是配置表**，应按此处理，而不是直接断言"表不存在"。

## 实现机制

- 结构定义存 `spfm_rel_table_definition`：一条记录 = 一张虚拟表的「建表信息」（`table_code` 表编码、`table_name` 表名、`description` 描述、`module` 所属模块、`mapping_json` 列映射）。
- 数据存 `spfm_rel_table_record`：一张宽表，用通用 slot 列 `value1~value75`（varchar）、`longValue1~50`（longtext）、`index0~50`（decimal）承载所有虚拟表数据；具体哪一列对应哪个业务字段由该虚拟表定义/`mapping_json` 决定。
- 租户维度 = `tenant_id`：`tenant_id = 0` 是**平台级**配置表（一般供标准代码做配置项判断）；`tenant_id ≠ 0` 是**租户定制**配置表。
- 租户分表：部分租户配置数据存在 `spfm_rel_table_record_{租户编码下划线}` 分表，命名 = `spfm_rel_table_record_` + 租户编码转小写下划线（如奥克斯 SOJO 为 `spfm_rel_table_record_srm_sojo`）。用 `archery_describe_table("spfm_rel_table_record_srm_{租户}")` 探测分表是否存在。

## 通用查询范式（不依赖具体虚拟表结构，违反即不得下结论）

```sql
-- ① 按 table_code 定位虚拟表：确认存在、看描述/模块/平台级还是租户级
SELECT id, tenant_id, table_code, table_name, module, platform_only
FROM spfm_rel_table_definition
WHERE table_code = '<虚拟表编码>'
ORDER BY tenant_id;

-- ② 查虚拟表数据（必带 tenant_id 走联合索引）
SELECT id, tenant_id, value1, value2, value3, longValue, index1
FROM spfm_rel_table_record
WHERE table_code = '<虚拟表编码>' AND tenant_id = <0 或目标租户 ID>
LIMIT 100;

-- ③ 租户分表：先 archery_describe_table 确认分表存在，再查
```

## 约束与细节

- **先看 `spfm_rel_table_definition`，再查 record**：definition 决定这张虚拟表存不存在、有没有租户级定制、字段怎么映射，不要跳过直接查 record。
- 查 record 必须带 `tenant_id`（严格适用 tenant_id 约束）；索引全是 `(table_code, tenant_id, valueN/indexN)` 联合前缀，`WHERE table_code=? AND tenant_id=?` 天然命中。
- 平台级与租户级要分别查：标准代码判断用 `tenant_id=0`；排查某租户行为用 `tenant_id=<该租户ID>`；两者都可能存在且都生效。
- 读数据要先确认列映射：record 是通用 slot，`valueN/longValueN/indexN` 对应哪个业务列看 `mapping_json` 与字段定义，不要凭空猜测 `value3` 就是某业务字段。
- 虚拟表编码即 `table_code`，报错/日志里的"表名"或代码里的表名往往就是 `table_code`；物理库 `archery_describe_table` 找不到时，优先用 `table_code` 去 `spfm_rel_table_definition` 查是否配置表。
- 判断某租户是否被某平台级配置项命中（如黑名单），可反查该虚拟表在 record 中 `tenant_id=0` 下是否含该租户，或查租户定制分表。
