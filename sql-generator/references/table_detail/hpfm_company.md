# hpfm_company - 公司信息表

## 表说明
公司信息表，存储系统中所有公司的基本信息。是SRM采购寻源系统的基础平台表之一，询价单、报价单等业务表通过 company_id 或 supplier_company_id 关联此表。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| company_id | bigint(20) | 主键，公司ID | PRIMARY |
| company_num | varchar(30) | 公司编码，自动生成 | UNIQUE (company_num, tenant_id) |
| group_id | bigint(20) | 集团ID | - |
| tenant_id | bigint(20) | 租户ID，从集团带过来 | INDEX (idx_hpfm_company_tenant_id) |
| unit_id | bigint(20) | 组织ID | - |
| domestic_foreign_relation | tinyint(1) | 境内境外，IN境内，OUT境外 | - |
| unified_social_code | varchar(30) | 统一社会信用码 | INDEX |
| organizing_institution_code | varchar(30) | 组织机构代码，和统一社会信用码至少存在一个 | INDEX |
| company_name | varchar(500) | 公司名称 | INDEX |
| short_name | varchar(50) | 公司简称 | - |
| company_type | varchar(30) | 公司类型 | - |
| registered_country_id | bigint(20) | 国家 | - |
| registered_region_id | bigint(20) | 地区ID，树形值集 | - |
| address_detail | varchar(500) | 详细地址 | - |
| duns_code | varchar(30) | 邓白氏编码 | INDEX |
| taxpayer_type | varchar(30) | 纳税人类型，值集HPFM.TAXPAYER_TYPE | - |
| legal_rep_name | varchar(120) | 法定代表人姓名 | - |
| build_date | date | 成立日期 | - |
| registered_capital | decimal(20,6) | 注册资本 | - |
| licence_end_date | date | 营业期限 | - |
| business_scope | longtext | 经营范围 | - |
| long_term_flag | tinyint(1) | 长期标志，1：长期，0：非长期 | - |
| licence_url | varchar(480) | 营业执照URL | - |
| source_key | bigint(20) | 源数据key | INDEX |
| source_code | varchar(30) | 来源，值集：HPFM.DATA_SOURCE | INDEX |
| enabled_flag | tinyint(1) | 启用标识 | - |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| service_area | varchar(500) | 服务区域 | - |
| version_number | bigint(20) | basic版本号，关联spfm_company_basic表version_number | - |
| certification_type | varchar(30) | 认证类型，值集SSLM_CERTIFICATION_TYPE，1企业，2个人 | - |
| certification_region_id | bigint(20) | 认证地区(国家枚举)，值集视图HPFM.COUNTRY | - |

## 核心索引
- PRIMARY: `company_id`
- UNIQUE: `hpfm_company_u2` - (company_num, tenant_id)
- INDEX: `hpfm_company_n1` - (company_id, tenant_id)
- INDEX: `idx_hpfm_company_tenant_id` - (tenant_id)
- INDEX: `hpfm_company_n3` - (company_name)
- INDEX: `hpfm_company_n4` - (unified_social_code)
- INDEX: `hpfm_company_n5` - (organizing_institution_code)
- INDEX: `hpfm_company_n6` - (duns_code)
- INDEX: `hpfm_company_n7` - (source_key, source_code)
- INDEX: `company_num_index` - (company_num)
- INDEX: `hpfm_company_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表被多个核心业务表关联：

### 询价单相关
- `ssrc_rfx_header.company_id` - 关联询价单的公司ID（采购方公司）
- `ssrc_rfx_line_supplier.supplier_company_id` - 关联询价单供应商的公司ID

### 报价单相关
- `ssrc_rfx_quotation_header.supplier_company_id` - 关联报价单的供应商公司ID

### 其他业务表
- 基本所有表里的 `companyId` 或 `supplierCompanyId` 都会关联此表

## 常见查询场景

### 1. 根据公司编码查询公司信息
```sql
SELECT company_id, company_num, company_name, company_type
FROM hpfm_company
WHERE tenant_id = {tenant_id}
  AND company_num = '{company_num}';
```

### 2. 根据统一社会信用码查询公司
```sql
SELECT company_id, company_num, company_name, unified_social_code
FROM hpfm_company
WHERE tenant_id = {tenant_id}
  AND unified_social_code = '{social_code}';
```

### 3. 查询询价单的采购方公司信息
```sql
SELECT h.rfx_num, h.rfx_title, hc.company_name, hc.company_num
FROM ssrc_rfx_header h
INNER JOIN hpfm_company hc ON h.company_id = hc.company_id
WHERE h.tenant_id = {tenant_id}
  AND h.rfx_num = '{rfx_num}';
```

### 4. 查询询价单的供应商公司信息
```sql
SELECT h.rfx_num, qls.supplier_company_name, hc.company_num, hc.company_type
FROM ssrc_rfx_header h
INNER JOIN ssrc_rfx_line_supplier qls ON h.rfx_header_id = qls.rfx_header_id
INNER JOIN hpfm_company hc ON qls.supplier_company_id = hc.company_id
WHERE h.tenant_id = {tenant_id}
  AND h.rfx_header_id = {rfx_header_id};
```

### 5. 查询报价单的供应商公司信息
```sql
SELECT qh.quotation_header_id, qh.quotation_status,
       hc.company_name, hc.company_num, hc.duns_code
FROM ssrc_rfx_quotation_header qh
INNER JOIN hpfm_company hc ON qh.supplier_company_id = hc.company_id
WHERE qh.tenant_id = {tenant_id}
  AND qh.rfx_header_id = {rfx_header_id};
```

### 6. 根据邓白氏编码查询公司
```sql
SELECT company_id, company_num, company_name, duns_code
FROM hpfm_company
WHERE tenant_id = {tenant_id}
  AND duns_code = '{duns_code}';
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **唯一标识**：`(company_num, tenant_id)` 组合唯一
3. **通用关联**：几乎所有需要公司信息的业务表都会关联此表
4. **扩展字段**：此表不包含 attribute 前缀的拓展字段
5. **启用标识**：`enabled_flag = 1` 表示启用状态
