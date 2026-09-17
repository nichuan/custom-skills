# 标准 vs 二开的调查规则

> 本文给出排障时的实现载体判定口径；仓库/分支等动态事实见 `srm-repository-topology.md`。
> 存库脚本分为适配器埋点脚本（`adapter-js.md`）与独立脚本（`standalone-script.md`），两者互不隶属，但排障时应按现有证据精确路由，不机械地把两套源码全部读取一遍。

## 实现载体判定

| 状态 | 判定证据 | 下一动作 |
|---|---|---|
| 二开 `custom` | 用户明确指出独立脚本、适配器、API 前/后置挂载、租户定制或外部接口对接；或者执行链中出现相应调用 | 按二开优先级查 `srm-script-container` 日志或目标脚本 |
| 标准 `standard` | 执行链证据已覆盖故障区段，且没有适配器或 API 前/后置挂载调用 | 可默认定向检索标准仓库 |
| 未知 `unknown` | 没有足够执行链，也没有可定位脚本的信息 | 保持未知并追问 traceId/脚本编码等；不得先扫标准仓库 |

“脚本工具未命中”“本地代码看起来有相关类”或“异常像标准 Java 报错”都不能单独把问题判为标准 Bug。

## 二开载体的定向定位

| 优先信号 | 二开方式 | 怎么查 |
|---|---|---|
| 挂钩点、BEFORE/AFTER、报文映射、回调/推送 | 适配器埋点脚本 | Pangu `search_adapter_scripts` 只发现身份，`adapter_get` 读取平台当前态 |
| 独立任务、打印/导入、API 配置、`SCUX_*` / `STD_*` | 独立脚本 | Pangu `search_standalone_scripts` 只发现身份，`independent_script_get` 读取平台当前态 |
| 物理表不存在且日志/脚本指向配置表 | 其他配置表（虚拟表） | 用 `table_code` 查 `spfm_rel_table_definition` / `spfm_rel_table_record`（或租户分表 `spfm_rel_table_record_srm_{租户}`） |
| 证据明确指向老租户 Git 二开类 | Git 二开仓库 `operation-srm-{租户}/srm-{模块}-{租户}` | 仅按已知类/接口定向用本地 `search_repo`；只有仓库/分支/路径已知时才精确读取 GitLab |

载体不明确但租户、服务或接口信息足以查询时，先按最强信号查一套脚本元信息；未命中或信号冲突再查另一套。无 traceId、无日志关键字且无任何脚本定位信息时，直接追问，不以本地代码搜索代替缺失信息。

## 两套存库脚本的精确路由信号

| 信号 | 适配器埋点脚本 | 独立脚本 |
|---|---|---|
| task_code 形态 | 含挂钩点：`*_BEFORE_HANDLE` / `*_AFTER_HANDLE` / `*_HANDLE`，或 ERP/WMS 对接映射 | `SCUX_*` / `STD_*` 业务命名，无 BEFORE/AFTER 挂钩点后缀 |
| 典型场景 | 报文映射、回调、推送、单据前/后处理、外部系统对接 | 定时任务、打印/PDF 模板、Excel 导入、消息/邮件提醒、OCR/外部 API 配置 |
| 前端/日志接口 | `/sada/v1/adaptor-script/*`（埋点管理） | `/sada/v1/rel-table-records/marmot_script_library/*`；编辑器 `/sada/v1/adaptor-script/auto-model|auto-prompt` |
| 日志特征 | 适配器执行链（task_code 挂钩点命中） | `JdbcUtils rel-table sql executed, args:[["<租户编码>"]]`、`marmot_script_library` |
| 存储位置 | `sada_adaptor_task_header/_line`（物理表，apply_tenant_num） | `spfm_rel_table_record`（宽表，value2=租户编码，tenant_id 恒为 0） |

拿不准但具备脚本定位条件时，先查最可能的一套，未命中再查另一套；任一套命中启用脚本即以脚本逻辑为准。

## 判定口径

- 适配器或独立脚本存在且启用 → **以脚本逻辑为准**；仅在核实脚本入参、返回结构、平台入口或默认行为确有必要时，标准库代码才作为对照。报告给出脚本 id、task_code 与解码后的关键逻辑，并注明属于哪套体系。
- 二开库中存在同名类/方法 → **以二开实现为准**，说明二者差异。
- 只有执行链证据覆盖故障区段且没有适配器或 API 前/后置挂载调用，才能把该次执行判为完全走标准代码；本地仓库不完整时不能断言租户没有二开。
- 各来源都没命中 → 不要臆断，明确写出已覆盖的数据源及能力边界。

## 多种二开方式并存

同一租户可能同时使用适配器脚本、独立脚本和 Git 二开仓。按当前执行链与任务编码选择目标载体；只有信号冲突或第一候选未命中时才扩大到另一类脚本，标准仓库始终放在二开契约核实的最后阶段。
