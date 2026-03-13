# ssrc_rfx_header 表详细结构

询价单头表（核心主表）

## 表信息
- **表名**: ssrc_rfx_header
- **主键**: rfx_header_id
- **外键**: tenant_id（关联 hpfm_tenant.tenant_id）
- **关联**: 询价单相关所有表的核心关联主键

## 核心字段详情

| 字段名                    | 数据类型  | 说明                                                                                         |
|--------------------------|-----------|----------------------------------------------------------------------------------------------|
| rfx_header_id            | bigint    | 询价单头ID（主键）                                                                           |
| tenant_id                | bigint    | 所属租户ID                                                                                   |
| rfx_num                  | varchar   | 询价单单号                                                                                   |
| rfx_title                | varchar   | 询价标题                                                                                     |
| rfx_status               | varchar   | 询价单状态（值集 SSRC.RFX_STATUS）：NEW/新建、RELEASE_APPROVING/发布审批中、NOT_START/未开始、IN_QUOTATION/报价中、SCORING/评分中、CHECK_PENDING/待核价 等 |
| secondary_status         | varchar   | 询价单二级状态（SSRC.RFX_SECONDARY_STATUS）                                                  |
| source_category          | varchar   | 寻源类别（SSRC.SOURCE_CATEGORY）：RFQ/询价、RFA/竞价、BID/招投标                            |
| source_method            | varchar   | 询价方式（SSRC.SOURCE_METHOD）：INVITE/邀请、OPEN/合作伙伴公开、ALL_OPEN/全平台公开          |
| quotation_type           | varchar   | 报价方式（SSRC.QUOTATION_TYPE）：ONLINE/线上报价、OFFLINE/线下报价、ON_OFF/线上线下并行      |
| template_id              | bigint    | 寻源模板ID（关联 ssrc_source_template）                                                     |
| company_id               | bigint    | 采购方企业ID                                                                                 |
| company_name             | varchar   | 公司名称                                                                                     |
| pur_organization_id      | bigint    | 采购方采购组织ID                                                                             |
| budget_amount            | decimal   | 预算金额                                                                                     |
| tax_included_flag        | tinyint   | 含税标识                                                                                     |
| tax_rate                 | decimal   | 税率                                                                                         |
| currency_code            | varchar   | 货币代码                                                                                     |
| quotation_start_date     | datetime  | 报价开始时间                                                                                 |
| quotation_end_date       | datetime  | 报价截止时间                                                                                 |
| latest_quotation_end_date| datetime  | 最晚截止时间                                                                                 |
| round_number             | int       | 轮次                                                                                         |
| released_date            | datetime  | 发布日期                                                                                     |
| released_by              | bigint    | 发布人                                                                                       |
| pretrial_status          | varchar   | 初审状态：NO_TRIAL/未初审、SUBMITED/初审提交                                                 |
| bargain_status           | varchar   | 议价状态：NEW/新建、BARGAIN_SCORING/评审议价中、BARGAIN_CHECKING/核价议价中、CLOSE/关闭      |
| business_weight          | decimal   | 商务组权重                                                                                   |
| technology_weight        | decimal   | 技术组权重                                                                                   |
| saving_amount            | decimal   | 节支金额                                                                                     |
| saving_ratio             | decimal   | 节支率                                                                                       |
| total_estimated_amount   | decimal   | 预估含税金额                                                                                 |
| pur_name                 | varchar   | 采购名称                                                                                     |
| pur_email                | varchar   | 采购邮箱                                                                                     |
| pur_phone                | varchar   | 采购电话                                                                                     |
| pur_user_id              | bigint    | 采购联系人用户ID                                                                             |
| rfx_remark               | longtext  | 备注                                                                                         |
| closed_flag              | tinyint   | 关闭标识                                                                                     |
| object_version_number    | bigint    | 行版本号，用来处理锁                                                                         |
| creation_date            | datetime  | 创建日期                                                                                     |
| created_by               | bigint    | 创建人                                                                                       |
| last_updated_by          | bigint    | 最后更新人                                                                                   |
| last_update_date         | datetime  | 最后更新日期                                                                                 |

## 常用查询

### 按租户和询价单ID查询
```sql
SELECT * FROM ssrc_rfx_header
WHERE tenant_id = 155357 AND rfx_header_id = 5923933;
```

### 按状态查询询价单列表
```sql
SELECT rfx_header_id, rfx_num, rfx_title, rfx_status, quotation_end_date
FROM ssrc_rfx_header
WHERE tenant_id = 155357
  AND rfx_status = 'IN_QUOTATION'
ORDER BY creation_date DESC;
```

### 按时间范围查询
```sql
SELECT * FROM ssrc_rfx_header
WHERE tenant_id = 155357
  AND creation_date BETWEEN '{start_date}' AND '{end_date}'
ORDER BY creation_date DESC;
```

### 统计各状态询价单数量
```sql
SELECT rfx_status, COUNT(*) AS cnt
FROM ssrc_rfx_header
WHERE tenant_id = 155357
GROUP BY rfx_status;
```

## rfx_status 状态值说明
- `NEW` 新建
- `RELEASE_APPROVING` 发布审批中
- `RELEASE_REJECTED` 发布审批拒绝
- `NOT_START` 未开始
- `IN_PREQUAL` 资格预审中
- `PREQUAL_CUTOFF` 资格预审截止
- `IN_QUOTATION` 报价中
- `OPEN_BID_PENDING` 待开标
- `PRETRIAL_PENDING` 待初审
- `SCORING` 评分中
- `CHECK_PENDING` 待核价
- `CHECK_APPROVING` 核价审批中
- `FINISHED` 已完成
- `TERMINATED` 已终止
