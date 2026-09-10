---
name: knowledge-governance
description: 甄云盘古认知库查询与治理助手。用于检索、查看、沉淀、修正、归档或删除 knowledge_docs 中的稳定业务知识、系统机制和排障经验，也可用 search_pangu/diagnose_context 做跨认知层发现。不用于维护 SQL 模板、表目录或查询实时生产数据。
---

# 盘古认知库治理

## 职责边界

本 Skill 管理 `knowledge_docs` 中可复用、相对稳定的知识：业务规则、系统机制、配置模型、数据模型和已经核验的排障经验。

- 当前日志、数据、DDL、服务状态不是知识库事实，分别交给日志、Archery 和排障 Skill 实时确认。
- SQL 模板由 `ssrc-sql-generator` / `spuc-sql-generator` 管理；表目录和关联关系由相应 SQL Skill 管理。
- `search_pangu` / `diagnose_context` 只用于发现候选上下文；命中模板或表后转交对应 Owner，不在本 Skill 越权维护。

## 工具选择

| 目标 | 工具 |
| --- | --- |
| 按关键词、类型、系统、模块或状态检索知识 | `search_knowledge` |
| 获取单条知识的完整正文与元数据 | `get_knowledge` |
| 从知识、模板、表和关系中快速发现线索 | `search_pangu` |
| 为排障汇集认知层候选上下文 | `diagnose_context` |
| 新增已确认的稳定知识 | `save_knowledge` |
| 修正文档、归类或状态 | `update_knowledge` |
| 物理删除错误、重复且无需保留的知识 | `delete_knowledge` |

## 工作流

1. 写入前先 `search_knowledge` 查重；需要全文时用真实 `doc_id` 调 `get_knowledge`。
2. 区分稳定知识与本次即时证据。未经实时工具或可靠资料核验的结论只能保持 `draft`，不得标为 `verified`。
3. `save_knowledge` / `update_knowledge` 前向用户展示准备写入或修改的内容并取得明确确认。只传本次需要变更的字段。
4. 内容过时但仍有参考价值时，优先 `update_knowledge(status="deprecated"|"archived")`；仅在用户明确要求物理删除后调用 `delete_knowledge`，删除前必须再次 `get_knowledge` 核对目标。
5. 写入后报告 `doc_id`、状态和实际变更，不把 MCP 返回成功等同于业务事实已被核验。

## 内容与参数约束

- `content_md` 使用结构清晰的 Markdown；不得包含密码、Token、AccessKey、个人敏感信息或未脱敏的生产数据。
- `core_tables`、`tags`、`related_template_ids` 使用逗号分隔字符串。
- `knowledge_type` 使用 `business/system/technical/troubleshooting/data_model/configuration/experience/rule`。
- `status` 使用 `draft/verified/deprecated/archived`。只有经可靠证据核验后才能设为 `verified`。
- `skip_dup_check` 默认保持 `false`；不能为绕过重复检测而开启。

## 输出

查询时给出命中文档的 `id`、标题、类型、状态、系统/模块和相关性说明。治理操作应清楚区分“新增、部分更新、归档、物理删除”，并说明是否需要用户确认；未获确认不得调用写工具。
