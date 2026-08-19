# 日志平台路由知识

> 本文件是企业事实（Knowledge 层），由 MCP `zhenyun-pangun-mcp` 实际承载平台/数据源选择。
> 排障 Agent 只需理解"何时选哪个工具"，**不需要也不能替代 MCP 去拼装 Project/Logstore/namespace/AccessKey**。

## 平台归属

| 环境 | 日志平台 | 调用工具 | 说明 |
|------|----------|----------|------|
| cn 国内盘古 `prod` | 阿里云 SLS | `obs_sls_query(system="盘古")` | 唯一走 SLS 的场景 |
| cn 国内盘古 `dev`/`test`（非生产） | Loki | `obs_log_query(region="cn")` / `obs_log_trace` | 非生产一律 Loki |
| AWS 海外（jp-saas-1，全部环境） | Loki | `obs_log_query(region="aws")` | 仅当用户明确说是 AWS 海外环境才用 |

一句话：**除「cn 国内盘古 prod」走 SLS 外，其余（cn 非生产 + 全部 AWS）都走 Loki。默认按 cn 处理，不要默认 aws。**

## region / env 的获取方式

- `env` 不是字面系统名（如 test），而是 MCP 数据源键：`cn` 下为 `prod`/`nonprod`/`ops`，**「test 环境」对应 `env="nonprod"`**（namespace 如 `saas-test-new`）。
- 不确定 region/env 时，先 `obs_log_datasources(region)` 确认真实键，**严禁瞎猜 env，也不要默认 aws**。

## Loki vs SLS 字段差异（查询语法由 MCP 能力决定，不在 Skill 重复）

- Loki 标签（无前缀，写在 `{...}` 流选择器）：`namespace` / `service_name` / `pod` / `container` / `app`。
- SLS 字段（下划线前缀）：`_namespace_` / `_container_name_` / `traceId` / `level` / `content`。
- 二者**不要混用**：Loki 的 traceId 直接按子串匹配（日志正文多为 `[abc]` 方括号），不要写死 `traceId=` 前缀。

## 凭据原则

日志凭据只配置在 MCP 服务端的 `.env` / MCP `env` 中，禁止写入 Skill、提示词、命令行参数或诊断报告。
