# ssrc_rfx_quotation_header 表详细结构

报价单头表

## 表信息
- **表名**: ssrc_rfx_quotation_header
- **主键**: quotation_header_id
- **外键**: rfx_header_id（关联 ssrc_rfx_header.rfx_header_id），1:N 关系
- **说明**: 每个供应商对应一条报价单头，与 ssrc_evaluate_score/ssrc_evaluate_summary 通过 quotation_header_id 关联（1:1）

## 核心字段详情

| 字段名                          | 数据类型  | 说明                                                                       |
|--------------------------------|-----------|---------------------------------------------------------------------------|
| quotation_header_id            | bigint    | 报价单头ID（主键）                                                         |
| rfx_header_id                  | bigint    | RFx单头ID                                                                 |
| tenant_id                      | bigint    | 所属租户ID                                                                 |
| quotation_num                  | varchar   | RFx报价单号                                                               |
| round_number                   | int       | 轮次                                                                       |
| quotation_status               | varchar   | 报价单状态（SSRC.RFX_QUOTATION_STATUS）：NEW/新建、QUOTED/已报价、FINISHED/结束 |
| supplier_tenant_id             | bigint    | 供应商租户ID                                                               |
| supplier_company_id            | bigint    | 供应商公司ID                                                               |
| supplier_company_name          | varchar   | 供应方企业名称                                                             |
| rfx_line_supplier_id           | bigint    | 供应商行表ID（关联 ssrc_rfx_line_supplier）                               |
| tax_included_flag              | tinyint   | 含税标识                                                                   |
| tax_rate                       | decimal   | 税率                                                                       |
| currency_code                  | varchar   | 币种                                                                       |
| exchange_rate                  | decimal   | 汇率                                                                       |
| qtn_total_amount               | decimal   | 报价总含税金额                                                             |
| qtn_tax_amount                 | decimal   | 报价总税额                                                                 |
| qtn_net_amount                 | decimal   | 报价总未税金额                                                             |
| suggested_qtn_total_amount     | decimal   | 选用报价总含税金额                                                         |
| suggested_qtn_net_amount       | decimal   | 选用报价总税额（实为含税）                                                 |
| suggested_qtn_tax_amount       | decimal   | 选用报价总未税金额（实为税额）                                             |
| pre_approve_status             | varchar   | 资格预审供应商状态：NEW/未提交、SUBMITED/已提交、APPROVED/已通过、REFUSED/未通过 |
| bargain_flag                   | tinyint   | 议价标识                                                                   |
| all_select_flag                | tinyint   | 整单选用标志                                                               |
| saving_amount                  | decimal   | 节支金额                                                                   |
| saving_ratio                   | decimal   | 节支率                                                                     |
| entry_method                   | varchar   | 录入方式：OFFLINE/线下录入、ONLINE/线上录入                                |
| quotation_remark               | longtext  | 备注                                                                       |
| object_version_number          | bigint    | 行版本号，用来处理锁                                                       |
| creation_date                  | datetime  | 创建日期                                                                   |
| last_update_date               | datetime  | 最后更新日期                                                               |

## 常用查询

### 查询询价单下所有报价单
```sql
SELECT * FROM ssrc_rfx_quotation_header
WHERE tenant_id = 155357 AND rfx_header_id = 5923933;
```

### 查询已报价的供应商
```sql
SELECT quotation_header_id, supplier_company_id, supplier_company_name,
       quotation_status, qtn_total_amount
FROM ssrc_rfx_quotation_header
WHERE tenant_id = 155357
  AND rfx_header_id = 5923933
  AND quotation_status = 'QUOTED'
ORDER BY qtn_total_amount ASC;
```

### 关联询价单和报价单
```sql
SELECT h.rfx_num, h.rfx_title,
       q.supplier_company_name, q.quotation_status, q.qtn_total_amount
FROM ssrc_rfx_header h
INNER JOIN ssrc_rfx_quotation_header q ON h.rfx_header_id = q.rfx_header_id
WHERE h.tenant_id = 155357 AND h.rfx_header_id = 5923933;
```

## 注意事项
- `quotation_header_id` 是评分表（ssrc_evaluate_score、ssrc_evaluate_summary）的关联键，1:1 对应一个供应商
- 同一个 rfx_header_id 下可能有多个轮次（round_number）的报价单
