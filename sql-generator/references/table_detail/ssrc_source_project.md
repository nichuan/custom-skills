# ssrc_source_project - 寻源立项表

## 表说明
寻源立项表，存储寻源立项的基本信息。是SRM采购寻源系统的核心业务表之一，记录寻源立项的创建、审批、执行等状态。

## 表结构

| 字段名 | 类型 | 说明 | 索引 |
|--------|------|------|------|
| source_project_id | bigint(20) | 主键，寻源立项ID | PRIMARY |
| tenant_id | bigint(20) | 所属租户ID，hpfm_tenant.tenant_id | INDEX (idx_ssrc_source_project_tenant_id) |
| source_project_num | varchar(60) | 项目编码 | UNIQUE (source_project_num, tenant_id) |
| source_project_name | varchar(240) | 项目名称 | INDEX |
| source_project_status | varchar(30) | 项目状态SSRC.SOURCE_PROJECT_STATUS(NEW/新建 &#124; CANCEL/已取消 &#124; APPROVING/已提交 &#124; REFUSE/审批拒绝 &#124; APPROVED/审批通过) | INDEX |
| project_from | varchar(30) | MUNUAL/手工创建 &#124; REFERENCE/引用申请 | - |
| source_category | varchar(30) | 寻源类别 | INDEX |
| source_method | varchar(30) | 询价方式SSRC.SOURCE_METHOD(INVITE/邀请&#124;OPEN/合作伙伴公开&#124;ALL_OPEN/全平台公开) | - |
| company_id | bigint(20) | 公司id | INDEX |
| contact_user_id | bigint(20) | 联系人id | INDEX |
| contact_mobilephone | varchar(60) | 联系人手机 | - |
| contact_mail | varchar(240) | 联系人邮箱 | - |
| estimated_date | date | 预计完成日期 | INDEX |
| budget_amount | decimal(20,6) | 预算金额 | - |
| method_id | bigint(20) | 评标办法id | INDEX |
| method_remark | longtext | 评标办法说明 | - |
| source_project_remark | longtext | 评标办法说明 | - |
| unit_id | bigint(20) | 需求部门 | INDEX |
| component_description | varchar(500) | 组件描述 | - |
| reference_flag | tinyint(1) | 引用标识 | - |
| source_header_id | bigint(20) | 被引用单据id | INDEX |
| source_header_num | varchar(60) | 被引用单据编号 | INDEX |
| object_version_number | bigint(20) | 行版本号，用来处理锁 | - |
| creation_date | datetime | 创建时间 | - |
| created_by | bigint(20) | 创建人 | - |
| last_updated_by | bigint(20) | 最后更新人 | - |
| last_update_date | datetime | 最后更新时间 | INDEX |
| source_date | datetime | 寻源时间 | INDEX |
| deposit_amount | decimal(20,6) | 保证金金额 | - |
| payment_type_id | bigint(20) | 付款方式 | INDEX |
| payment_term_id | bigint(20) | 付款条款 | INDEX |
| source_project_attachment_uuid | varchar(60) | 立项附件UUID | - |
| subject_matter_rule | varchar(30) | 标的规则SSRC.SUBJECT_MATTER_RULE(PACK/分标段包&#124;NONE/不区分) | - |
| finishing_rate | int(11) | 维护完成率 | - |
| approval_comments | longtext | 审批意见 | - |
| international_tel_code | varchar(30) | 国际电话区号 | - |
| currency_code | varchar(30) | 币种 | - |
| total_estimated_amount | decimal(20,6) | 预估总金额 | - |
| sourced_flag | tinyint(1) | 寻源是否结束。(包括其中某一条询价单的关闭，取消。完成) | - |
| source_config | varchar(500) | RFX 节点配置 | - |
| source_member | longtext | 寻源成员 | - |
| secondary_source_category | varchar(30) | 次级寻源类别SSRC.SECONDARY_SOURCE_CATEGORY(RFQ/询价&#124;RFA/竞价&#124;BID/招投标&#124;NEW_BID/新招投标) | INDEX |
| purchaser_id | bigint(20) | 采购人id | INDEX |
| copy_source_project_id | bigint(20) | 复制寻源项目id | INDEX |
| pur_organization_id | bigint(20) | 采购组织id | INDEX |
| closed_comments | varchar(500) | 关闭理由 | - |
| closed_attachment_uuid | varchar(60) | 关闭附件UuId | - |
| closed_by | bigint(20) | 关闭人 | INDEX |
| closed_date | datetime | 关闭时间 | INDEX |
| closed_status | varchar(30) | 关闭状态 | - |
| source_request | varchar(500) | 寻源要求 | - |

## 核心索引
- PRIMARY: `source_project_id`
- UNIQUE: `ssrc_source_project_u2` - (source_project_num, tenant_id)
- INDEX: `idx_ssrc_source_project_tenant_id` - (tenant_id)
- INDEX: `ssrc_source_project_n2` - (source_project_name)
- INDEX: `ssrc_source_project_n3` - (source_project_status)
- INDEX: `ssrc_source_project_n4` - (source_category)
- INDEX: `ssrc_source_project_n5` - (company_id)
- INDEX: `ssrc_source_project_n6` - (contact_user_id)
- INDEX: `ssrc_source_project_n7` - (estimated_date)
- INDEX: `ssrc_source_project_n8` - (method_id)
- INDEX: `ssrc_source_project_n9` - (unit_id)
- INDEX: `ssrc_source_project_n10` - (source_header_id)
- INDEX: `ssrc_source_project_n11` - (source_header_num)
- INDEX: `ssrc_source_project_n12` - (source_date)
- INDEX: `ssrc_source_project_n13` - (payment_type_id)
- INDEX: `ssrc_source_project_n14` - (payment_term_id)
- INDEX: `ssrc_source_project_n15` - (secondary_source_category)
- INDEX: `ssrc_source_project_n16` - (purchaser_id)
- INDEX: `ssrc_source_project_n17` - (copy_source_project_id)
- INDEX: `ssrc_source_project_n18` - (pur_organization_id)
- INDEX: `ssrc_source_project_n19` - (closed_by)
- INDEX: `ssrc_source_project_n20` - (closed_date)
- INDEX: `ssrc_source_project_n103` - (last_update_date)

## 业务关联
在SRM采购寻源系统中，此表与其他业务表关联：

### 寻源立项相关
- `ssrc_project_line_item.source_project_id` - 关联立项物料行表
- `ssrc_project_line_section.source_project_id` - 关联立项标段表
- `ssrc_project_line_supplier.source_project_id` - 关联立项供应商行表

### 询价单相关
- `ssrc_rfx_header.source_project_id` - 关联询价单头表

## 常见查询场景

### 1. 根据项目编码查询寻源立项信息
```sql
SELECT source_project_id, source_project_num, source_project_name, source_project_status
FROM ssrc_source_project
WHERE tenant_id = {tenant_id}
  AND source_project_num = '{source_project_num}';
```

### 2. 查询寻源立项的物料行信息
```sql
SELECT pli.project_line_item_id, pli.item_code, pli.item_name, pli.required_quantity
FROM ssrc_project_line_item pli
WHERE pli.tenant_id = {tenant_id}
  AND pli.source_project_id = {source_project_id}
ORDER BY pli.project_line_item_num;
```

### 3. 查询寻源立项的标段信息
```sql
SELECT pls.project_line_section_id, pls.section_code, pls.section_name
FROM ssrc_project_line_section pls
WHERE pls.tenant_id = {tenant_id}
  AND pls.source_project_id = {source_project_id}
ORDER BY pls.section_num;
```

### 4. 查询寻源立项的供应商信息
```sql
SELECT pls.project_line_supplier_id, pls.supplier_company_name, pls.contact_name
FROM ssrc_project_line_supplier pls
WHERE pls.tenant_id = {tenant_id}
  AND pls.source_project_id = {source_project_id};
```

### 5. 查询寻源立项关联的询价单信息
```sql
SELECT sp.source_project_num, sp.source_project_name, rfx.rfx_num, rfx.rfx_title
FROM ssrc_source_project sp
INNER JOIN ssrc_rfx_header rfx ON sp.source_project_id = rfx.source_project_id
WHERE sp.tenant_id = {tenant_id}
  AND sp.source_project_id = {source_project_id};
```

## 重要说明
1. **租户隔离**：通过 `tenant_id` 实现租户级别的数据隔离
2. **唯一标识**：`(source_project_num, tenant_id)` 组合唯一
3. **状态管理**：支持新建、已取消、已提交、审批拒绝、审批通过等状态
4. **来源方式**：支持手工创建和引用申请两种方式
5. **寻源类别**：支持询价、竞价、招投标等寻源类别
6. **引用标识**：`reference_flag = 1` 表示该立项引用了其他单据
7. **关闭功能**：支持寻源立项的关闭操作
8. **复制功能**：支持从其他寻源立项复制
