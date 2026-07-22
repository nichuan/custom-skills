# iam_user 表详细结构

用户表（平台基础表）—— **所有 SRM 业务表中存储的"人员ID"最终都指向本表的主键 `id`**。

## 关键信息

> ⚠️ **极重要规则（必须严格遵守）**
> 1. **人员ID统一指向 `iam_user.id`**：SRM 各业务表中的 `*_user_id`、`user_id`、`expert_user_id`、`created_by`、`last_updated_by`、`process_user_id`、`deliver_from_user_id`、`deliver_to_user_id` 等所有人员相关字段，存储的都是 `iam_user.id`。凡涉及"修复/查询人员"的数据问题，都必须先通过本表查出对应的 `id`。
> 2. **`organization_id` 即为租户ID**：本表的 `organization_id` 等同其他 SRM 表的 `tenant_id`。⚠️ 注意本表**没有** `tenant_id` 字段，过滤租户数据时必须用 `organization_id`，不能用 `tenant_id`（会报错）。
> 3. **跨租户唯一性问题**：`login_name` 全局唯一；但 `tenant_login_name` 与 `organization_id` 组合唯一（同一租户内唯一）。手机号 `phone` 与 `user_type` 组合唯一。

## 表信息
- **表名**: iam_user
- **主键**: id
- **租户过滤字段**: organization_id（等价其他表的 tenant_id）
- **关联**: 几乎所有业务表的人员字段都通过 `xxx_user_id = iam_user.id` 关联本表

## 字段详情

| 字段名                     | 数据类型      | 说明                                                                 |
|---------------------------|---------------|----------------------------------------------------------------------|
| id                        | bigint(20)    | 用户ID（主键，自增）。业务表中所有人员ID都指向它                     |
| login_name                | varchar(128)  | 用户名（全局唯一，索引 iam_user_u1）                                 |
| email                     | varchar(128)  | 邮箱                                                                 |
| organization_id           | bigint(20)    | 组织ID = **租户ID**（等价其他表的 tenant_id），用于租户过滤          |
| HASH_PASSWORD             | varchar(128)  | Hash后的用户密码                                                     |
| real_name                 | varchar(128)  | 用户真实姓名（索引 iam_user_n3）                                     |
| phone                     | varchar(32)   | 手机号（与 user_type 组合唯一，索引 iam_user_u3 / iam_user_n2）      |
| INTERNATIONAL_TEL_CODE    | varchar(16)   | 国际电话区号，默认 '+86'                                             |
| image_url                 | varchar(480)  | 用户头像地址                                                         |
| profile_photo             | mediumtext    | 用户二进制头像                                                       |
| language                  | varchar(16)   | 语言，默认 'zh_CN'                                                   |
| time_zone                 | varchar(64)   | 时区，默认 'GMT+8'                                                   |
| last_password_updated_at  | datetime      | 上一次密码更新时间                                                   |
| last_login_at             | datetime      | 上一次登录时间                                                       |
| is_enabled                | tinyint(3)    | 用户是否启用：1启用，0未启用                                         |
| is_locked                 | tinyint(3)    | 是否锁定账户：1锁定，0未锁定                                         |
| is_ldap                   | tinyint(3)    | 是否 LDAP 来源：1是，0不是                                           |
| is_admin                  | tinyint(3)    | 是否为管理员用户：1是，0不是                                         |
| locked_until_at           | datetime      | 锁定账户截止时间                                                     |
| password_attempt          | tinyint(3)    | 密码输错累积次数                                                     |
| object_version_number     | bigint(20)    | 行版本号                                                             |
| created_by                | bigint(20)    | 创建人（= iam_user.id）                                              |
| creation_date             | datetime      | 创建日期                                                             |
| last_updated_by           | bigint(20)    | 最后更新人（= iam_user.id）                                          |
| last_update_date          | datetime      | 最后更新日期                                                         |
| user_type                 | varchar(30)   | 用户类型(P/C)：平台用户P / C端用户C，默认 'P'                        |
| attribute1 ~ attribute15  | varchar(150)  | 预留扩展字段 attribute1..attribute15                                 |
| tenant_login_name         | varchar(128)  | 租户级别新用户名（与 organization_id 组合唯一，索引 iam_user_u4）    |
| local_name                | varchar(128)  | 本地名称                                                             |

## 常用查询

### 查询指定租户下的用户
```sql
-- ⚠️ 本表用 organization_id 作为租户过滤，不是 tenant_id
SELECT id, login_name, real_name, email, phone, user_type, is_enabled
FROM iam_user
WHERE organization_id = {tenant_id}
  AND is_enabled = 1;
```

### 通过业务人员ID反查用户信息（数据修复/排查人员必备）
```sql
-- 已知某业务表的 user_id / expert_user_id 等，反查姓名与账号
SELECT id, login_name, real_name, email, organization_id
FROM iam_user
WHERE id = {user_id};
```

### 通过账号/姓名定位用户（数据修复时把账号映射成 id）
```sql
SELECT id, login_name, real_name, organization_id
FROM iam_user
WHERE organization_id = {tenant_id}
  AND login_name = 'xxx';          -- 全局唯一

-- 或通过租户内用户名
SELECT id, login_name, real_name
FROM iam_user
WHERE organization_id = {tenant_id}
  AND tenant_login_name = 'xxx';
```

### 与业务表关联查询人员信息（示例：寻源小组成员）
```sql
SELECT m.rfx_member_id,
       m.rfx_role,
       m.user_id,
       u.login_name,
       u.real_name
FROM   ssrc_rfx_member m
       JOIN iam_user u ON m.user_id = u.id
WHERE  m.tenant_id = {tenant_id}
  AND  m.rfx_header_id = {rfx_header_id};
```

## 数据修复注意事项
- **凡涉及"人员"的修复**，先通过本表把账号/姓名解析为 `iam_user.id`，再用该 `id` 去更新业务表的人员字段（`user_id` / `expert_user_id` / `created_by` 等），不要直接写入账号字符串。
- 过滤本表租户数据时必须用 `organization_id = {tenant_id}`，**不要使用 `tenant_id`**（本表无此字段）。
- 修改用户启用/锁定状态、密码等属于账号安全操作，需谨慎并确认 `organization_id`（租户）正确。
