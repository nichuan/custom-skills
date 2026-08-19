# SPUC SQL Generator Skill（盘古订单履约域）

## 概述

本 Skill 是专门为 SRM 盘古（订单履约域）设计的 SQL 生成助手，覆盖 **采购订单（SODR）→ 发货（SLOD/老送货单）→ 收货事务（SINV_RCV）→ 导出（结算/外部/商城/委外）** 全链路。采用与 `ssrc-sql-generator` 相同的分层设计：**「本地仅沉淀业务语义、结构事实走 MCP」**，表结构通过 **zhenyun-pangun-mcp 的 Archery 工具** 实时获取，SQL 模板通过 **sql-template MCP（Supabase）** 按盘古专属分类检索与沉淀。

> **与 ssrc-sql-generator 的分工**：
> - `ssrc-sql-generator`：采购寻源（询价单/招标单/报价/评分/资格预审/寻源结果/征询单）
> - `spuc-sql-generator`（本技能）：订单履约（采购订单/收货事务/发货工作台/老送货单/状态机/委外）
> - 模板库通过 **category/doc_type/title 前缀/keywords** 四重区分，避免检索串扰（详见 SKILL.md「盘古模板约定」）。

## 核心特性

1. **结构事实走 MCP**：`describe_table` / `validate_table_columns` / `execute_sql` 实时获取，不本地维护表结构。
2. **业务语义分层**：`table_meta.md`（表速查/枚举/库归属）、`relations.md`（关联/状态机/联动规则）只沉淀数据库拿不到的知识。
3. **模板库 + 分级校验**：盘古专属分类（`订单SPUC`/`物流收货SINV`/`物流发货SLOD`/`盘古通用查询`/`数据修复-盘古`），✅ 已验证模板免 MCP 校验提效。
4. **盘古域专属铁律**：sodr 乐观锁、pe_supplier 组合字段、关闭/取消互斥、ES 表联动、上下游协同清理、跨库前缀（`srm_logistics_delivery`）等。

## 目录结构

```
spuc-sql-generator/
├── SKILL.md                # Skill 入口文件（必读）
├── README.md               # 本文件
├── skill.json              # Skill 配置文件
└── references/
    ├── table_meta.md       # 表名、主键、关联键、库归属、易错枚举
    └── relations.md        # 表关联关系、状态机规则、上下游联动
```

## 快速开始

当用户提出以下需求时触发本 Skill：

1. **订单查询/修复**：「查询订单 PO2026xxx 的状态」「把订单修复为已发布/已确认」「订单整单取消金额归零」
2. **收货事务**：「查收货事务导出结算失败的记录」「把推外部状态改回 FAIL 重推」「清理收货事务数据」
3. **发货工作台**：「查送货单占用数量」「清理订单初始化发货数据」「送货单同步 ERP 失败修复」
4. **老送货单**：「修复老送货单占用数量」「送货单 ES 数据修复」
5. **供应商/主数据修复**：「修复订单头供应商（pe_supplier）」「修复结算公司」
6. **同步/幂等**：「补订单同步记录触发重推」「查消费幂等记录」

## 工作流程（详见 SKILL.md 铁律）

1. `search_sql_template` 按盘古分类检索模板复用
2. 确认单据体系（订单/收货/发货工作台/老送货单）与目标租户（查 `hpfm_tenant`）
3. 分级校验表/字段（已验证模板免校验，其余 `validate_table_columns`）
4. `execute_sql` 逐步取真实主键值（先租户→再单据→再行）
5. 生成 SQL（含核查 SELECT，sodr 带乐观锁，占位符 `<...>` 标注）
6. 完成后询问用户是否 `save_sql_template` 沉淀

## 依赖

- **zhenyun-pangun-mcp（Archery）**：默认实例 `prod`（由别名解析为 SAAS-SRM-PROD 等真实实例名，以 `archery_list_instances` 返回为准），默认库 `srm`，发货工作台域在 `srm_logistics_delivery`
- **sql-template MCP**：Supabase 模板库（与 ssrc 共库，用分类区分）
