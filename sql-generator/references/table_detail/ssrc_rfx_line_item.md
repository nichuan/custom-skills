# ssrc_rfx_line_item 表详细结构

询价单物料行表

## 表信息
- **表名**: ssrc_rfx_line_item
- **主键**: rfx_line_item_id
- **外键**: rfx_header_id（关联 ssrc_rfx_header.rfx_header_id），1:N 关系
- **说明**: 存储询价单下的每个物料/采购项目

## 核心字段详情

| 字段名                  | 数据类型  | 说明                                               |
|------------------------|-----------|---------------------------------------------------|
| rfx_line_item_id       | bigint    | 物料行ID（主键）                                   |
| rfx_header_id          | bigint    | 询价单头ID                                        |
| rfx_line_item_num      | int       | 行号                                              |
| tenant_id              | bigint    | 所属租户ID                                        |
| item_id                | bigint    | 物料ID                                            |
| item_code              | varchar   | 物料代码                                          |
| item_name              | varchar   | 物料名称                                          |
| item_category_id       | bigint    | 物料类别ID                                        |
| rfx_quantity           | decimal   | 询价数量                                          |
| uom_id                 | bigint    | 计量单位ID                                        |
| delivery_address       | varchar   | 收货地址                                          |
| demand_date            | date      | 需求日期                                          |
| tax_included_flag      | tinyint   | 含税标识                                          |
| tax_rate               | decimal   | 税率                                              |
| max_limit_price        | decimal   | 最高限价                                          |
| min_limit_price        | decimal   | 最低限价                                          |
| cost_price             | decimal   | 成本价                                            |
| estimated_price        | decimal   | 预估含税单价                                      |
| estimated_amount       | decimal   | 预估含税金额                                      |
| freight_included_flag  | tinyint   | 是否含运费标志                                    |
| round_flag             | tinyint   | 多轮报价标志                                      |
| current_round_number   | int       | 所处轮次                                          |
| ladder_inquiry_flag    | tinyint   | 阶梯报价标志                                      |
| quotation_end_date     | datetime  | 报价截止时间                                      |
| brand                  | varchar   | 品牌                                              |
| manufacturer           | varchar   | 制造商                                            |
| specs                  | varchar   | 规格                                              |
| model                  | varchar   | 型号                                              |
| item_remark            | longtext  | 物品说明                                          |
| line_item_remark       | longtext  | 物料行备注                                        |
| saving_amount          | decimal   | 节支金额                                          |
| saving_ratio           | decimal   | 节支率                                            |
| pr_num                 | varchar   | 申请编号                                          |
| pr_line_num            | int       | 申请行号                                          |
| object_version_number  | bigint    | 行版本号，用来处理锁                              |
| creation_date          | datetime  | 创建日期                                          |
| last_update_date       | datetime  | 最后更新日期                                      |

## 常用查询

### 查询询价单下所有物料行
```sql
SELECT * FROM ssrc_rfx_line_item
WHERE tenant_id = 155357 AND rfx_header_id = 5923933
ORDER BY rfx_line_item_num;
```

### 查询物料行基本信息
```sql
SELECT rfx_line_item_id, rfx_line_item_num, item_code, item_name,
       rfx_quantity, max_limit_price, demand_date
FROM ssrc_rfx_line_item
WHERE tenant_id = 155357 AND rfx_header_id = 5923933;
```

### 统计询价单物料数量
```sql
SELECT rfx_header_id, COUNT(*) AS item_count, SUM(estimated_amount) AS total_estimated
FROM ssrc_rfx_line_item
WHERE tenant_id = 155357 AND rfx_header_id = 5923933
GROUP BY rfx_header_id;
```
