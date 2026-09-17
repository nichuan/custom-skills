# 独立脚本（Marmot 脚本库，rel-table 宽表虚拟表）

> 企业事实层。独立脚本（Marmot 脚本库）与适配器埋点脚本（`sada_adaptor_task_*`，见 `adapter-js.md`）是**两套独立体系**。独立脚本没有独立物理表，全部存于 rel-table 宽表（虚拟表机制，见 `virtual-table.md`）。源码/测试用例映射已于 2026-09-16 由 `cn/prod/srm.spfm_rel_table_definition.mapping_json` 核实；此前将测试输入误记为正文的结论已纠正。

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
| `longValue5`（定义键 `longvalue5`） | `content`，脚本内容（明文或历史 Base64） | 源码读取与搜索的唯一正文列 |
| `longValue1`（定义键 `longvalue1`） | `contentInput`，测试用例（Base64） | 测试输入 JSON，不是脚本源码 |

⚠️ **关键陷阱**：该表所有行 `tenant_id = 0`，租户编码在 `value2` 槽位。查询独立脚本【禁止按 `tenant_id` 过滤】，必须按 `table_code + value2`。

## Agent 标准读取流程（MCP 工具链）

```text
已知 tenant + code
  → zhenyun-script-platform-mcp.independent_script_get

编码不完整
  → zhenyun-pangu-mcp.search_standalone_scripts(tenant, query)
  → 唯一精确身份
  → zhenyun-script-platform-mcp.independent_script_get
```

- `tenant` 参数底层过滤 `value2`；`query` 匹配 `value3`（脚本编码）/`value4`（描述）。
- Pangu 搜索只发现候选；平台当前 Record、版本、Fixture 和源码以 `independent_script_get` 为准。
- Script Platform MCP 直接返回明文源码；Agent 不处理平台 Base64。
- 定位字段、函数、接口地址或报文时在 `independent_script_get` 返回的当前源码中查找。
- 禁止用通用 `archery_query` 直接返回 `longValue*` 存储内容；统一由源码工具处理明文/历史 Base64 并限制返回范围。

## 底层数据模型（维护 Tool 时使用）

```sql
-- ① 按租户编码列独立脚本元信息（tenant_id 恒为 0，禁止用 tenant_id 过滤）
SELECT id, value1, value2 AS tenant_num, value3 AS task_code, value4 AS description, value5
FROM spfm_rel_table_record
WHERE table_code = 'marmot_script_library' AND value2 = '<租户编码>'
LIMIT 50;

-- ② 工具在服务端读取并解码唯一源码列；不得按非空值探测槽位
SELECT id, value3, longValue5 AS encoded_source
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
| 正文编码 | `longValue5`，明文或历史 Base64（UTF-16LE/BE/UTF-8 探测） | `script_content`，Base64(UTF-16BE) |
| 执行方式 | srm-script-container 独立执行（定时任务/导入/打印模板/API 配置等） | 挂钩点 BEFORE/AFTER 执行，与标准逻辑同事务 |
| 典型场景 | 定时任务、PDF/送货单打印模板、Excel 导入、消息/邮件提醒、OCR/外部 API 配置 | ERP/WMS/OA 对接、报文字段映射、回调推送、单据前/后处理 |

## 结论口径

排查租户二开时，按执行链、task_code 和场景信号选择独立脚本或适配器脚本；第一候选未命中或信号冲突时再查另一套。任一命中即以脚本实际逻辑为准，报告中给出 script_id、task_code 与解码后的关键逻辑；标准库仅在核实脚本入参、返回结构、平台入口或默认行为确有必要时作为对照。
