# 天工（Tiangong）环境知识

> 企业事实层。天工与盘古是两套独立系统，日志与数据库实例互不通用。

## 系统与环境

天工支持：`paas-dev` / `paas-test` / `saas-dev` / `saas-test` / `sandbox` / `prod`。

## 日志

- 天工日志走 Loki（`obs_log_query(region="cn")`）或 SLS（`obs_sls_query(system="天工")`），具体由 MCP 按环境路由。
- 系统别名：`tg`/`tiangong` 归一化为 `天工`，`pg`/`pangu` 归一化为 `盘古`，**不要混用天工 `paas-*` 命名与盘古路由**。

## 数据库

- 天工为 PostgreSQL，使用天工专属 PgSQL 实例别名（由 `archery_list_instances` 确认）。
- **勿用盘古实例（`prod`/`test`/`dev`）查天工库**，否则得到错误数据。

## 代码库

天工代码同样遵循"标准库 + 租户二开"拓扑（见 `knowledge/architecture/srm-repository-topology.md`），排查时按模块与租户定位对应 Group。
