# 独立脚本（Marmot 脚本库，rel-table 宽表虚拟表）

> 企业事实层。独立脚本（Marmot 脚本库）与适配器埋点脚本（`sada_adaptor_task_*`，见 `adapter-js.md`）是**两套独立体系**。独立脚本没有独立物理表，全部存于 rel-table 宽表（虚拟表机制，见 `virtual-table.md`）。2026-09-05 dev 实测（traceId LF0OYREN）+ 数据库验证。

## 存储位置（`srm` 库，rel-table 宽表）

所有独立脚本存于 `srm.spfm_rel_table_record`，`table_code = 'marmot_script_library'`。

## 槽位字段映射（value 槽位按列顺序约定，无语义化列名）

| 槽位 | 内容 | 示例 |
|---|---|---|
| `value1` | 类型标志 | `1` / `2` |
| `value2` | 租户编码（apply 租户） | `SRM-PECHION` |
| `value3` | 脚本编码（task_code） | `SCUX_SRM_PECHION_PAYMENT_STATEMENT_PDF_PRINT_ADAPTOR` |
| `value4` | 描述（常含猪齿鱼任务号） | `srm-84641，百雀羚付款结算单打印.` |
| `value5` | 内容类型标记 | `template` / `api` 等 |
| `longValue1`（或相邻 longValue 槽位） | 脚本/模板正文（Base64） | 样本为 UTF-16LE JSON；JS 正文按行探测编码 |

⚠️ **关键陷阱**：该表所有行 `tenant_id = 0`，租户编码在 `value2` 槽位。查询独立脚本【禁止按 `tenant_id` 过滤】，必须按 `table_code + value2`。

## Agent 标准读取流程（MCP 工具链）

```text
search_standalone_scripts(tenant, query)
  → get_standalone_script_info(script_id)
  → search_standalone_script_source(script_id, query)
  → get_standalone_script_source(script_id, start_line, end_line)
```

- `tenant` 参数底层过滤 `value2`；`query` 匹配 `value3`（脚本编码）/`value4`（描述）。
- MCP 在服务端完成 Base64 解码（自动探测 UTF-16LE/UTF-16BE/UTF-8），Agent 只接收正文文本。
- 定位字段、函数、接口地址或报文时先搜索正文，再读取局部行号；只有确需全局分析时才 `full=true`。
- 禁止用通用 `archery_query` 把 `longValue*` Base64 正文返回给 Agent。

## 底层数据模型（维护 Tool 时使用）

```sql
-- ① 按租户编码列独立脚本元信息（tenant_id 恒为 0，禁止用 tenant_id 过滤）
SELECT id, value1, value2 AS tenant_num, value3 AS task_code, value4 AS description, value5
FROM spfm_rel_table_record
WHERE table_code = 'marmot_script_library' AND value2 = '<租户编码>'
LIMIT 50;

-- ② 正文在 longValue 槽位（探测 longValue/longValue1~5 取第一个非空）
SELECT id, value3, longValue1
FROM spfm_rel_table_record
WHERE table_code = 'marmot_script_library' AND value2 = '<租户编码>' AND value3 = '<脚本编码>';
```

## 前端链路（识别信号）

- 独立脚本列表：`POST /sada/v1/rel-table-records/marmot_script_library/page` → `srm-adaptor` 的 `org.srm.marmot.controller.RelTableAccessSiteController.list` → rel-table 通用查询（日志特征：`JdbcUtils rel-table sql executed, args:[["<租户编码>"]]`）。
- 脚本编辑器打开：`GET /sada/v1/adaptor-script/auto-model`、`/sada/v1/adaptor-script/auto-prompt`（AI 辅助编辑的模型配置与提示词）。
- 日志中出现 `marmot_script_library` 或 rel-table 宽表查询 → 当前问题与独立脚本相关。

## 与适配器埋点脚本的对照

| | 独立脚本 | 适配器埋点脚本 |
|---|---|---|
| 存储表 | `spfm_rel_table_record`（table_code=`marmot_script_library`，虚拟表） | `sada_adaptor_task_header/_line`（物理表） |
| 租户字段 | `value2` 槽位（tenant_id=0） | `apply_tenant_num`（无 tenant_id 列） |
| 正文编码 | `longValue*` 槽位，Base64（UTF-16LE/BE/UTF-8 按行探测） | `script_content`，Base64(UTF-16BE) |
| 执行方式 | srm-script-container 独立执行（定时任务/导入/打印模板/API 配置等） | 挂钩点 BEFORE/AFTER 执行，与标准逻辑同事务 |
| 典型场景 | 定时任务、PDF/送货单打印模板、Excel 导入、消息/邮件提醒、OCR/外部 API 配置 | ERP/WMS/OA 对接、报文字段映射、回调推送、单据前/后处理 |

## 结论口径

排查租户二开时，独立脚本与适配器脚本**都要查**（先适配器后独立，拿不准就两套都查）；任一命中即以脚本实际逻辑为准，报告中给出 script_id、task_code 与解码后的关键逻辑；标准库代码只作为对照。
