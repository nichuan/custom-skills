# 适配器 JS 脚本（最新二开方式，存库非 Git）

> 企业事实层。标准代码内置「适配器（Adapter）」处理，核心是执行一段 **JS 脚本**扩展/覆盖标准逻辑。脚本内容存在数据库（不放在仓库），以 **Base64** 编码存储。适配器脚本内的数据库事务与标准逻辑是同一事务。

## 定位脚本的两张表（都在 `srm` 库，注意这两张表【没有 `tenant_id`】，租户维度是 `apply_tenant_num`）

| 表 | 说明 | 关键字段 |
|---|---|---|
| `sada_adaptor_task_header` | 脚本任务头 | `id`、`task_code`、`description`、`apply_tenant_num`（租户编码，如 `SRM-SOJO`）、`running_service`（服务名，如 `srm-source`）、`enabled_flag`（1=启用）、`trustful`、`script_version` |
| `sada_adaptor_task_line` | 脚本行 | `header_id`、`script_content`（Base64）、`script_type`（仅 `JS`）、`filter`、`priority` |

## 标准查询流程（先租户、再服务、再取脚本）

```sql
-- ① 按租户编码 + 运行服务，定位该租户在该服务下有哪些二开脚本头
SELECT id, task_code, description, enabled_flag, trustful, script_version
FROM sada_adaptor_task_header
WHERE apply_tenant_num = '<租户编码>' AND running_service = 'srm-<模块>'
  AND enabled_flag = 1
ORDER BY id;

-- ② 用命中头的 id，查脚本正文（script_content 为 Base64）
SELECT id, header_id, script_type, filter, priority, script_content
FROM sada_adaptor_task_line
WHERE header_id = <上一步的 id>
ORDER BY priority;
```

## 约束与细节（违反即不得下结论）

- 两张表都没有 `tenant_id`，租户过滤必须用 `apply_tenant_num`（tenant_id 约束对这两张表不适用）。
- 头表唯一键是 `(task_code, apply_tenant_num)`；行表走 `header_id` 索引，天然高效。
- 只看 `enabled_flag = 1`（启用才真正生效）；`script_version` 取**最新**的。
- `task_code` 命名含挂钩点信息，如 `SSRC_RFX_RELEASE_BEFORE_HANDLE`（发布前）、`..._AFTER_HANDLE`（后执行）；`BEFORE_/AFTER_/` 后缀说明在标准逻辑的前/后执行，据此判断该二开是否影响当前排障点。

## 脚本正文解码

`script_content` 是 `Base64(UTF-16BE)` 双重编码：
1. `Base64 解码` → 得到 UTF-16BE 字节流（每字符 2 字节，`\x00` 在前、字符在后）
2. 若字节数为奇数，先去掉末尾 1 个字节
3. `UTF-16BE 解码` → JS 源码文本（函数形如 `function process(input) { ... }`）

Python 验证：`base64.b64decode(script_content).decode('utf-16-be')`（需先截成偶数长度）；**不要用 `utf-16-le`**（会乱码）。

## 结论口径

发现该租户存在启用中的适配器脚本时，必须以脚本逻辑为准，并在报告中给出脚本 id、task_code 与解码后的关键逻辑；标准库代码只作为对照。
