# ssrc_rfx_quotation_line 表详细结构

报价单行表（物料报价明细）

## 表信息
- **表名**: ssrc_rfx_quotation_line
- **主键**: quotation_line_id
- **外键**: quotation_header_id（关联 ssrc_rfx_quotation_header.quotation_header_id），1:N 关系
- **说明**: 存储每个供应商对每个物料的报价明细，包含有效报价价格和当前报价价格

## 核心字段详情

| 字段名                      | 数据类型  | 说明                                                                     |
|----------------------------|-----------|-------------------------------------------------------------------------|
| quotation_line_id          | bigint    | 报价行ID（主键）                                                         |
| quotation_header_id        | bigint    | 报价单头ID                                                               |
| tenant_id                  | bigint    | 所属租户ID                                                               |
| rfx_line_item_id           | bigint    | 询价单物料行ID（关联 ssrc_rfx_line_item）                               |
| round_number               | int       | 轮次                                                                     |
| quotation_line_status      | varchar   | 报价行状态：NEW/新建、SUBMITTED/已报价、BARGAINED/已还价、TAKEN_BACK/收回、ABANDONED/放弃 |
| valid_quotation_price      | decimal   | 有效报价含税单价                                                         |
| valid_net_price            | decimal   | 有效报价未税单价                                                         |
| valid_quotation_quantity   | decimal   | 有效报价数量                                                             |
| valid_quotation_remark     | longtext  | 有效报价理由                                                             |
| valid_promised_date        | date      | 承诺交货日期                                                             |
| valid_delivery_cycle       | varchar   | 供货周期                                                                 |
| current_quotation_price    | decimal   | 当前报价含税单价                                                         |
| current_quotation_quantity | decimal   | 当前报价数量                                                             |
| tax_included_flag          | tinyint   | 含税标识                                                                 |
| tax_rate                   | decimal   | 税率                                                                     |
| net_price                  | decimal   | 未税单价                                                                 |
| tax_price                  | decimal   | 含税单价                                                                 |
| net_amount                 | decimal   | 未税金额                                                                 |
| tax_amount                 | decimal   | 税额                                                                     |
| total_amount               | decimal   | 含税总金额                                                               |
| suggested_flag             | tinyint   | 建议选用标志                                                             |
| suggested_remark           | longtext  | 建议选用理由                                                             |
| allotted_quantity          | decimal   | 分配数量                                                                 |
| allotted_ratio             | decimal   | 分配比例                                                                 |
| quotation_rank             | bigint    | 报价排名                                                                 |
| bargain_flag               | tinyint   | 还价标志                                                                 |
| brand                      | varchar   | 有效品牌                                                                 |
| freight_included_flag      | tinyint   | 是否含运费标志                                                           |
| freight_amount             | decimal   | 运费金额                                                                 |
| saving_amount              | decimal   | 节支金额                                                                 |
| saving_ratio               | decimal   | 节支率                                                                   |
| quoted_date                | datetime  | 报价时间                                                                 |
| object_version_number      | bigint    | 行版本号，用来处理锁                                                     |
| creation_date              | datetime  | 创建时间                                                                 |
| last_update_date           | datetime  | 最后修改时间                                                             |

## 常用查询

### 查询报价单下的报价行
```sql
SELECT * FROM ssrc_rfx_quotation_line
WHERE tenant_id = 155357 AND quotation_header_id = {quotation_header_id};
```

### 查询某询价单所有供应商的报价
```sql
SELECT q.supplier_company_name,
       li.item_code, li.item_name, li.rfx_quantity,
       ql.valid_quotation_price, ql.total_amount, ql.quotation_rank
FROM ssrc_rfx_quotation_header q
INNER JOIN ssrc_rfx_quotation_line ql ON q.quotation_header_id = ql.quotation_header_id
INNER JOIN ssrc_rfx_line_item li ON ql.rfx_line_item_id = li.rfx_line_item_id
WHERE q.tenant_id = 155357 AND q.rfx_header_id = 5923933
  AND ql.quotation_line_status = 'SUBMITTED'
ORDER BY li.rfx_line_item_num, ql.quotation_rank;
```

### 查询各物料最低报价
```sql
SELECT ql.rfx_line_item_id,
       li.item_code, li.item_name,
       MIN(ql.valid_quotation_price) AS min_price,
       COUNT(*) AS quote_count
FROM ssrc_rfx_quotation_line ql
INNER JOIN ssrc_rfx_quotation_header q ON ql.quotation_header_id = q.quotation_header_id
INNER JOIN ssrc_rfx_line_item li ON ql.rfx_line_item_id = li.rfx_line_item_id
WHERE q.tenant_id = 155357 AND q.rfx_header_id = 5923933
  AND ql.quotation_line_status = 'SUBMITTED'
GROUP BY ql.rfx_line_item_id, li.item_code, li.item_name;
```
