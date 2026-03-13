# ssrc_source_result 寻源结果表

## 表说明
寻源结果表，报价行维度，记录询价单/招标单的最终中标/选用结果。

## 核心字段（高频使用）

| 字段名 | 数据类型 | 说明 | 关联 |
|--------|----------|------|------|
| result_id | bigint | 主键 | — |
| tenant_id | bigint | 租户ID | hpfm_tenant.tenant_id |
| source_header_id | bigint | 寻源单头id | ssrc_rfx_header.rfx_header_id |
| source_from | varchar | 来源：RFX/BID | — |
| source_num | varchar | 寻源单号 | — |
| source_type | varchar | 寻源类型：NORMAL/常规、OEM、PROJECT/项目、OUTSOURCE/外协、CONSIGN/寄售 | — |
| supplier_company_id | bigint | 供应商公司ID | — |
| supplier_company_name | varchar | 供应方企业名称 | — |
| company_id | bigint | 采购方企业ID | — |
| item_id | bigint | 物料ID | — |
| item_code | varchar | 物料代码 | — |
| item_name | varchar | 物料描述 | — |
| item_num | int | 行号 | — |
| quantity | decimal | 数量 | — |
| unit_price | decimal | 单价 | — |
| tax_included_flag | tinyint | 含税标识 | — |
| tax_rate | decimal | 税率 | — |
| currency_code | varchar | 币种 | — |
| valid_promised_date | date | 承诺交货日期 | — |
| valid_delivery_cycle | varchar | 供货周期 | — |
| finish_date | datetime | 完成时间 | — |
| sync_status | varchar | 同步ERP状态：UNSYNCHRONIZED/未导入、SYNCHRONIZING/导入中、SYNCHRONIZED/已导入、SYNC_FAILURE/导入失败 | — |
| result_status | varchar | 寻源结果状态 | — |
| quotation_line_id | bigint | 报价行id | ssrc_rfx_quotation_line.quotation_line_id |
| source_line_item_id | bigint | 来源物料行ID | ssrc_rfx_line_item.rfx_line_item_id |

## 其他字段

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| pur_organization_id | bigint | 采购方采购组织ID |
| inv_organization_id | bigint | 库存组织ID |
| item_category_id | bigint | 物品类别 |
| uom_id | bigint | 单位 |
| tax_id | bigint | 税率ID |
| exchange_rate | decimal | 汇率 |
| price_category | varchar | 价格类型：STANDARD/标准、SAMPLE/样品 |
| erp_number | varchar | ERP反馈编码 |
| import_erp_status | varchar | 导入ERP状态 |
| object_version_number | bigint | 行版本号（乐观锁） |
| creation_date | datetime | 创建日期 |
| created_by | bigint | 创建人 |
| last_updated_by | bigint | 最后更新人 |
| last_update_date | datetime | 最后更新日期 |

## 常用查询示例

```sql
-- 查询某询价单的寻源结果
SELECT sr.supplier_company_name, sr.item_code, sr.item_name,
       sr.quantity, sr.unit_price, sr.sync_status
FROM ssrc_source_result sr
WHERE sr.tenant_id = 155357
  AND sr.source_from = 'RFX'
  AND sr.source_header_id = 5923933;

-- 查询已同步ERP的寻源结果
SELECT *
FROM ssrc_source_result
WHERE tenant_id = 155357
  AND source_from = 'RFX'
  AND source_header_id = 5923933
  AND sync_status = 'SYNCHRONIZED';
```
