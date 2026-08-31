# 日志平台路由知识

> 本文件是企业事实（Knowledge 层），由 MCP `zhenyun-pangu-mcp` 实际承载平台/数据源选择。
> 排障 Agent 只需理解"何时选哪个工具"，**不需要也不能替代 MCP 去拼装 Project/Logstore/namespace/AccessKey**。

## 平台归属（2026-08 现状）

| 环境 | 日志平台 | 调用工具 | 说明 |
|------|----------|----------|------|
| cn 国内盘古 `prod` | 阿里云 SLS | `obs_sls_query(system="盘古", environment="prod")` | namespace=`saas-prod` |
| cn 国内盘古 `dev` | 阿里云 SLS | `obs_sls_query(environment="dev")` | namespace=`saas-dev-new` |
| cn 国内盘古 `test` | 阿里云 SLS | `obs_sls_query(environment="test")` | namespace=`saas-test-new` |
| AWS 海外（jp-saas-1，全部环境） | Loki | `obs_log_query(region="aws")` / `obs_log_trace` | 仅当用户明确说是 AWS 海外环境 |

一句话：**国内公有云盘古（prod + 非生产 dev/test）全部走阿里云 SLS；Loki 只剩 AWS 海外。默认按 cn/盘古处理，不要默认 aws。**

⚠️ 变迁记录：盘古非生产曾短暂迁移到 Loki（`logs.going-link.net`），现已**迁回阿里云 SLS**。
`obs_log_*` 不再接受 `region="cn"`（会返回「请改用 `obs_sls_query`」的提示），查国内盘古非生产不要再用 Loki 工具。

## 环境键怎么传

- `obs_sls_query` 的 `environment` 直接用 `prod` / `dev` / `test`（也接受「生产/正式」「测试」等口语别名），
  不确定时用 `obs_sls_targets()` 列出真实映射。
- `obs_log_query` 的 `env` 不是字面系统名（如 test），而是 Loki 数据源键（aws 下为 `prod`/`nonprod`/`ops`）；
  不确定时先 `obs_log_datasources(region="aws")` 确认真实键，**严禁瞎猜 env，也不要默认 aws**。

## Loki vs SLS 字段差异（查询语法由 MCP 能力决定，不在 Skill 重复）

- Loki 标签（无前缀，写在 `{...}` 流选择器）：`namespace` / `service_name` / `pod` / `container` / `app`。
- SLS 字段（下划线前缀）：`_namespace_` / `_container_name_` / `traceId` / `level` / `content`。
- 二者**不要混用**：Loki 的 traceId 直接按子串匹配（日志正文多为 `[abc]` 方括号），不要写死 `traceId=` 前缀。

## 排障常用参数

- 有 traceId → `obs_sls_query(trace_id=..., environment=...)` 走「ERROR/WARN + 全链路」两阶段查询；
  AWS 侧用 `obs_log_trace(trace_id, region="aws")`。
- `level` 默认 `ERROR`，传 `""` 表示不过滤级别；`limit` 首次给 100~200。
- 时间：`time_range` 支持 `最近30分钟`/`最近2小时`/`最近3天`、`今天`/`昨天`/`本周`/`上月`、`2h`/`1d`，
  或 `YYYY-MM-DD HH:mm~HH:mm`（北京时间）。
- `auto_expand` 默认开启：未显式指定时间窗且 0 命中时自动扩到最近 24h、72h 各重试一次
  （实际窗口见 `meta.attempted_windows`），避免因时间对齐偏差误判"日志不存在"。

## 凭据原则

日志凭据只配置在 MCP 服务端的 `.env` / MCP `env` 中，禁止写入 Skill、提示词、命令行参数或诊断报告。
