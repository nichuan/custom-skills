# 案例：超级搜索查询不到收货单（权限/字段映射问题）

> 来源：`采购员工作问题排查案例/采购员工作台超级搜索查询不到收货单问题排查.txt`
> 类型：搜索类 bug（根因为权限维度字段映射不匹配）
> 用途：后续遇到"超级搜索查不到某类单据"时，优先套用本案例的排查思路。

## 1. 现象
用户在采购员工作台**超级搜索**中，按采购组织（`purOrganizationId=3`）作为查询条件，搜索**收货单**时查不到结果；
但按其他条件或换维度能查到。怀疑是数据权限 / ES 维度过滤导致。

## 2. 排查路径
1. **确认 ES 里到底有没有这条单据 + 它的权限维度值**
   - 直接查 ES 收货单索引，确认单据存在，且 `purOrganizationId` 维度字段的值是否为预期的 `3`。
2. **核对权限维度配置表 `swbh_doc_type_dimension_mapping`**
   - 看收货单（`combineCode`）在该表里定义的"权限维度字段名"是什么。
   - 发现配置的是 `purOrganizationId`。
3. **核对单据源表字段**
   - 收货单头表 `sinv_rcv_trx_header` 实际字段名为 `purchase_org_id`（注意：**下划线 + 全小写**），且当时该字段值为 **null**。
   - 即：配置表字段名（`purOrganizationId`）≠ 头表字段名（`purchase_org_id`），字段名不匹配 → 取不到值（或取到 null）。
4. **确认生成权限维度的代码**
   - `WorkBenchDataBatchProcessServiceImpl#insertESDimension` 负责按 `swbh_doc_type_dimension_mapping` 取字段值、生成单据权限维度写入 ES。
   - 因为字段名不匹配 + 头表值为 null，采购组织维度**没有被正确写入 ES**。
5. **搜索时拼维度过滤**
   - 超级搜索按 `purOrganizationId=3` 拼权限维度查询，但 ES 里该单据没有这个维度值 → 被过滤掉 → 查不到。

## 3. 根因
- **字段名不匹配**：权限维度配置用 `purOrganizationId`，而源表是 `purchase_org_id`，导致维度值取不到。
- **源表字段为 null**：即便映射对了，`sinv_rcv_trx_header.purchase_org_id` 当时为 null，维度仍写不进 ES。
- **附加坑（表不匹配）**：该单据（`SPUC_SINV_WORKBENCH_FINISHED`）的"单据权限"来源其实是**行表** `sinv_rcv_trx_line`，但工作台配置挂的是**头表** `sinv_rcv_trx_header`，表也不对。

## 4. 涉及表 / 类 / SQL
- 配置/权限表：`swbh_doc_type_permission_data_set`、`swbh_doc_type_dimension_mapping`、`swbh_auth_access`、`swbh_access_group`、`swbh_user_access_group`
- 业务源表：`sinv_rcv_trx_header`（头）、`sinv_rcv_trx_line`（行）
- 代码：`WorkBenchDataBatchProcessServiceImpl#insertESDimension`
- 核对 SQL 示例：
```sql
-- 查某单据类型的维度映射配置
SELECT * FROM swbh_doc_type_dimension_mapping
WHERE combine_code = 'SPUC_SINV_WORKBENCH_FINISHED';

-- 查收货单头表采购组织字段实际值
SELECT header_id, purchase_org_id FROM sinv_rcv_trx_header
WHERE tenant_id = ? AND purchase_org_id = 3;
```

## 5. 避坑点（沉淀给后续）
- 超级搜索查不到 ≠ 数据不存在，**先查 ES 确认单据在不在、维度值对不对**，再排查权限链。
- 权限维度问题优先看 `swbh_doc_type_dimension_mapping` 的字段名是否和**源表真实字段名**一致（大小写、下划线、驼峰都很关键）。
- 注意单据权限来源是头表还是行表，配置挂错表是常见低级坑。
- 字段为 null 也会导致维度写不进 ES，排查时一并确认源数据完整性。
