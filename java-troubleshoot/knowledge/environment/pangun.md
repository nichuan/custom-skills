# 盘古（Pangun）环境知识

> 企业事实层。平台/实例的真实名称与切换由 MCP 承载，Agent 只需理解环境→实例别名的映射关系。

## 系统与环境

盘古支持：`dev` / `test` / `prod`。

## Archery 实例别名映射（只传别名，真实名由 MCP 自动转换）

| 选定环境 | `site` | `instance` | 说明 |
|----------|--------|------------|------|
| 盘古 `prod` / 不提环境 | `cn` | `prod` | 盘古生产 |
| 盘古 `prod` 生产只读 | `cn` | `prod-ro` | 盘古生产只读 |
| 盘古 `test` | `cn` | `test` | 盘古测试 |
| 盘古 `dev` | `cn` | `dev` | 盘古开发 |
| AWS 海外站点 | `aws` | `aws` | aws 站点盘古库 |

- `site` 只能是 `cn` 或 `aws`；`instance` 必须用别名（`prod`/`prod-ro`/`aws`/`dev`/`test`），**严禁直接传真实实例名**（如 `SAAS-SRM-PROD数据库`）。
- 拿不准实例/库时先 `archery_list_instances(site)` / `archery_list_databases(site, instance)` 确认。
- **Archery 默认实例是 PROD**，site/instance 必须与调查环境一致，显式传参，否则会误查生产数据。
- 拿不准环境时，回到用户确认，不要默认猜 PROD。

## 数据库类型

| 系统 | 数据库类型 | 常用 `instance` 别名 |
|------|------------|----------------------|
| 盘古 | MySQL | `prod`/`prod-ro`/`test`/`dev` |
| 天工 | PostgreSQL | 天工相关 PgSQL 实例别名 |

> 天工（paas-/saas-/sandbox）与盘古实例相互独立，勿混用盘古实例查天工库。
