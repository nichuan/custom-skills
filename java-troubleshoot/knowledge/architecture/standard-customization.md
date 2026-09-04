# 标准 vs 二开的调查规则

> 行为层（Skill 调用本知识时的判定口径），但仓库/分支等动态事实见 `srm-repository-topology.md`。
> 存库脚本分两套体系：适配器埋点脚本（`adapter-js.md`）与独立脚本（`standalone-script.md`），**互不隶属，都要查**。

## 四种二开方式（排障确定二开时必须依次走完）

| 顺序 | 二开方式 | 怎么查 |
|---|---|---|
| 1（最新，优先） | 适配器埋点脚本（存库，挂钩点执行） | `search_adapter_scripts` 系列查 `sada_adaptor_task_*`，有 `enabled_flag=1` 即命中 |
| 2（最新，与 1 并列） | 独立脚本（Marmot 脚本库，rel-table 宽表） | `search_standalone_scripts` 系列查 `spfm_rel_table_record`（`table_code='marmot_script_library'`，租户在 value2） |
| 3 | 其他配置表（虚拟表） | 物理库找不到目标表时，用 `table_code` 查 `spfm_rel_table_definition` / `spfm_rel_table_record`（或租户分表 `spfm_rel_table_record_srm_{租户}`） |
| 4（较老） | Git 二开仓库 `operation-srm-{租户}/srm-{模块}-{租户}` | 在本地 `PG_ROOT` 用 `search_repo` 检索；只有仓库/分支/路径已知时才精确读取 GitLab |
| 5 | 无二开 | 以上都查不到 → 走标准逻辑 |

## 两套存库脚本的精确路由信号

| 信号 | 适配器埋点脚本 | 独立脚本 |
|---|---|---|
| task_code 形态 | 含挂钩点：`*_BEFORE_HANDLE` / `*_AFTER_HANDLE` / `*_HANDLE`，或 ERP/WMS 对接映射 | `SCUX_*` / `STD_*` 业务命名，无 BEFORE/AFTER 挂钩点后缀 |
| 典型场景 | 报文映射、回调、推送、单据前/后处理、外部系统对接 | 定时任务、打印/PDF 模板、Excel 导入、消息/邮件提醒、OCR/外部 API 配置 |
| 前端/日志接口 | `/sada/v1/adaptor-script/*`（埋点管理） | `/sada/v1/rel-table-records/marmot_script_library/*`；编辑器 `/sada/v1/adaptor-script/auto-model|auto-prompt` |
| 日志特征 | 适配器执行链（task_code 挂钩点命中） | `JdbcUtils rel-table sql executed, args:[["<租户编码>"]]`、`marmot_script_library` |
| 存储位置 | `sada_adaptor_task_header/_line`（物理表，apply_tenant_num） | `spfm_rel_table_record`（宽表，value2=租户编码，tenant_id 恒为 0） |

**拿不准时两套都查**（先适配器后独立）；任一套命中启用脚本即以脚本逻辑为准。

## 判定口径

- 适配器或独立脚本存在且启用 → **以脚本逻辑为准**，标准库代码只作为对照；报告给出脚本 id、task_code 与解码后的关键逻辑，并注明属于哪套体系。
- 二开库中存在同名类/方法 → **以二开实现为准**，说明二者差异。
- 仅标准库存在且两套存库脚本、虚拟表、已纳入 PG_ROOT 的二开仓均排除后，结论才可基于标准实现；本地仓库不完整时不能断言租户没有二开。
- 各来源都没命中 → 不要臆断，明确写出已覆盖的数据源及能力边界。

## 多种二开方式并存

同一租户可能同时使用适配器脚本、独立脚本和 Git 二开仓（部分老租户三种都有）；存库脚本（方式 1/2）必须优先于老 Git 二开库排查。
