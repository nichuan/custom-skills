# hpfm_tenant 表详细结构

租户信息表（平台基础表）

## 表信息
- **表名**: hpfm_tenant
- **主键**: tenant_id
- **关联**: 几乎所有业务表都通过 tenant_id 关联到本表

## 字段详情

| 字段名                     | 数据类型  | 说明                         |
|---------------------------|-----------|------------------------------|
| tenant_id                 | bigint    | 租户ID（主键）               |
| tenant_num                | varchar   | 租户编码                     |
| tenant_name               | varchar   | 租户名                       |
| enabled_flag              | tinyint   | 是否启用：1启用，0未启用     |
| limit_user_qty            | int       | 租户下有效用户数，null不限制 |
| own_expense               | tinyint   | 1自费，0供应商缴费           |
| message_threshold         | int       | 租户消息拦截阈值，默认100    |
| admin_email               | varchar   | 租户管理员邮箱               |
| admin_phone               | varchar   | 租户管理员手机               |
| core_enterprise           | tinyint   | 0非核企，1核企               |
| tenant_admin              | varchar   | 租户管理员                   |
| enable_theme_config       | tinyint   | 主题配置开关：0关闭，1开启   |
| function_group_template   | varchar   | 关联平台目录组               |
| object_version_number     | bigint    | 行版本号，用来处理锁         |
| creation_date             | datetime  | 创建日期                     |
| created_by                | bigint    | 创建人                       |
| last_updated_by           | bigint    | 最后更新人                   |
| last_update_date          | datetime  | 最后更新日期                 |

## 常用查询

### 查询指定租户
```sql
-- 通过租户编码查询租户ID
SELECT tenant_id, tenant_num, tenant_name
FROM hpfm_tenant
WHERE tenant_num = 'SRM-JDENERGY';

-- 查询所有启用的租户
SELECT * FROM hpfm_tenant WHERE enabled_flag = 1;
```

## 注意事项
- `tenant_id = 155357` 对应 `tenant_num = 'SRM-JDENERGY'`（当前主要业务租户）
- 几乎所有业务表都包含 `tenant_id` 字段，用于多租户数据隔离
