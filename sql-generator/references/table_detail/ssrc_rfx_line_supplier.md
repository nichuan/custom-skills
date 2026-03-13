# ssrc_rfx_line_supplier 表详细结构

询价单供应商行表

## 表信息
- **表名**: ssrc_rfx_line_supplier
- **主键**: rfx_line_supplier_id
- **外键**: rfx_header_id（关联 ssrc_rfx_header.rfx_header_id），1:N 关系
- **说明**: 存储询价单邀请的每个供应商信息，1个询价单可以对应多个供应商

## 核心字段详情

| 字段名                        | 数据类型  | 说明                                                                          |
|------------------------------|-----------|------------------------------------------------------------------------------|
| rfx_line_supplier_id         | bigint    | 供应商行ID（主键）                                                            |
| rfx_header_id                | bigint    | 询价单头ID                                                                    |
| tenant_id                    | bigint    | 所属租户ID                                                                    |
| supplier_tenant_id           | bigint    | 供应商租户ID                                                                  |
| supplier_company_id          | bigint    | 供应商公司ID                                                                  |
| supplier_company_name        | varchar   | 供应方企业名称                                                                |
| supplier_contact_id          | bigint    | 供应商联系人ID                                                                |
| contact_name                 | varchar   | 联系人名称                                                                    |
| contact_mail                 | varchar   | 联系人邮箱                                                                    |
| contact_mobilephone          | varchar   | 联系人手机号                                                                  |
| feedback_status              | varchar   | 反馈状态（SSRC.RFX_FEEDBACK_STATUS）：PARTICIPATED/参与、ABANDONED/不参与、NEW/未反馈 |
| feedback_remark              | longtext  | 供应商报价状况备注                                                            |
| read_flag                    | tinyint   | 供应商已读标识                                                                |
| abandon_remark               | longtext  | 放弃理由                                                                      |
| suggested_remark             | longtext  | 选用理由                                                                      |
| allotted_ratio               | decimal   | 分配比例                                                                      |
| append_flag                  | tinyint   | 添加标识                                                                      |
| supplier_status              | varchar   | 供应商行状态                                                                  |
| off_line_flag                | tinyint   | 线下录入标识                                                                  |
| supplier_id                  | bigint    | 外部供应商ID                                                                  |
| object_version_number        | bigint    | 行版本号，用来处理锁                                                          |
| creation_date                | datetime  | 创建日期                                                                      |
| last_update_date             | datetime  | 最后更新日期                                                                  |

## 常用查询

### 查询询价单下所有供应商
```sql
SELECT * FROM ssrc_rfx_line_supplier
WHERE tenant_id = 155357 AND rfx_header_id = 5923933;
```

### 查询已参与报价的供应商
```sql
SELECT rfx_line_supplier_id, supplier_company_id, supplier_company_name, feedback_status
FROM ssrc_rfx_line_supplier
WHERE tenant_id = 155357
  AND rfx_header_id = 5923933
  AND feedback_status = 'PARTICIPATED';
```

### 统计各反馈状态供应商数
```sql
SELECT feedback_status, COUNT(*) AS cnt
FROM ssrc_rfx_line_supplier
WHERE tenant_id = 155357 AND rfx_header_id = 5923933
GROUP BY feedback_status;
```
