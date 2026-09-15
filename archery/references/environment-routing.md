# Archery 环境与库路由

仅在需要确认完整实例映射、库清单或处理路由错误时读取本文件。实时可用范围以 `archery_list_instances` 与 `archery_list_databases` 返回为准。

## 实例别名

```text
cn:
  prod      -> SAAS-SRM-PROD数据库
  prod-ro   -> SAAS-SRM-PROD只读数据库
  dev       -> SAAS-SRM-DEV数据库
  test      -> SAAS-SRM-TEST数据库
aws:
  aws / aws-prod -> JP-SaaS-1-Prod-RW-8.0
default_site = cn, default_db = srm
```

## 国内生产常见库

| 库名 | 用途 |
| --- | --- |
| `srm` | 主业务库：寻源、订单履约、平台、主数据、状态机 |
| `srm_logistics_delivery` | 发货工作台 `slod_*` |
| `srm_budget` | 预算 |
| `srm_data_application` | 数据应用 |
| `srm_open_platform` | 开放平台 |
| `srm_requisition_plan` | 申购计划 |
| `srm_workbench` | 采购员工作台 |
| `scavenger_prod` | 用途以实时事实为准 |

一般不查 `mysql`、`information_schema`、`performance_schema`、`sys`、`apolloconfigdb`、`apolloportaldb`、`test` 等系统或内部库。dev、test、aws 的库清单不硬编码，按目标环境实时列举。
