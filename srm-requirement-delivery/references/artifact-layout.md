# Marmot 交付产物分类与目录

用于新增、多产物或需要维护 `artifacts.json` 的完整交付。已有需求目录或用户指定路径按原结构最小修改，不为套目录而搬迁文件。

## 1. 两层分类

先按平台对象类型区分，再只对 Independent Script 使用平台实际 `quickType` 分型：

- 顶层类型：Adapter Line、Independent Script、CodeBlock、QueryBlock、Constant、API Rewrite、API Publish，以及需求实际涉及的 Queue Consumer、Scheduler、OutBound、Data Import。
- Independent 子类型：目录使用平台当前记录或定义返回的原始 `quickType` 经路径规范化后的值。不得把业务角色反推成另一个 `quickType`。
- API 前置/后置首先是 `api_rewrite` 关系中的阶段；脚本 `quickType` 与前置/后置阶段分别记录。历史记录若实际使用 `api_pre`、`api_post` 等值，原样保存在清单中。
- CodeBlock、QueryBlock、Constant 和 API 关系是独立平台资源，不放进 Independent 目录，也不因被脚本引用就降格为脚本附件。

这样区分是因为各类型的精确身份、内容格式、版本、引用关系、验证方式和写入工具不同。目录只负责组织；平台事实仍以精确 `get` 和 `artifacts.json` 为准。

## 2. 新交付的规范目录

```text
<delivery-root>/<issue-or-short-name>/<tenant>/
  request.md
  design-gates.md
  artifacts.json
  artifacts/
    adapter/<task-code>/<running-service>/line-<line-id>/entry.js
    adapter/<task-code>/<running-service>/draft/entry.js       # 平台尚未创建
    independent/<quick-type>/<script-code>/entry.js
    code-block/<block-code>/entry.js
    query-block/<query-block-code>/query.sql
    query-block/<query-block-code>/count.sql                    # 仅存在 countSql 时
    constant/<constant-code>/resource.json
    api-rewrite/<api-code>/<pre-or-post>/resource.json
    api-publish/<publish-code>/resource.json
    queue-consumer/<topic-or-code>/resource.json
    scheduler/<job-code>/resource.json
    outbound-whitelist/<host-key>/resource.json
    data-import/<template-code>/resource.json
  fixtures/<kind>/<identity-key>/*.json                        # 仅真实或明确构造的最小样例
```

固定资源类型目录使用文中给出的 kebab-case；来自平台的 `taskCode`、`scriptCode`、`quickType` 等身份段保留原始大小写和下划线，只把 `/`、`\\`、`<>:\"|?*`、控制字符及 `.`/`..` 路径穿越片段替换为 `_`。原始值仍必须保存在 `artifacts.json`，不能只靠目录名还原。Adapter 已有 Line 始终带 `runningService + lineId`，避免相同 `taskCode` 在不同服务或多 Line 下冲突；新建前可放 `draft`，同一身份有多个草稿时使用 `draft-1`、`draft-2`，取得真实 Line ID 后再改为正式路径。历史 Independent 缺失 `quickType` 时目录用 `unknown` 并在清单标为 `TBD`；新建 Independent 不得在 `quickType` 未确认时继续创建。

只有需求实际涉及的目录才创建，不生成空目录。`resource.json` 保存可审阅的非秘密配置快照；Constant 的 `value`、Token、凭据和其它秘密值不得写入本地产物，Constant 只记录编码、描述、租户、版本和 `value_status: "managed_out_of_band"`。

## 3. 类型与本地内容

| `kind` | 本地内容 | 关键身份/子类型 | 主要验证 |
| --- | --- | --- | --- |
| `adapter_line` | `entry.js` | `taskCode + runningService + lineId` | JS、静态规则、指定 Line Debug/部署 |
| `independent_script` | `entry.js` | `scriptCode + quickType(raw)` | JS、静态规则、Independent Debug/保存 |
| `code_block` | `entry.js` | `blockCode` | JS、调用契约、引用关系 |
| `query_block` | `query.sql`，可选 `count.sql` | `queryBlockCode` | 参数、SQL 意图、结果列、引用关系 |
| `constant` | 无秘密值的 `resource.json` | `constantCode` | 身份、版本、使用方；值走平台外受控流程 |
| `api_rewrite` | `resource.json` | `apiCode + stage + recordId/version` | 前/后置阶段与脚本引用回读 |
| `api_publish` | `resource.json` | 发布编码/路由 + recordId/version | 路由、方法、权限和脚本引用回读 |
| `queue_consumer` | `resource.json` | topic/编码 + recordId/version | 消费关系和脚本/CodeBlock 引用 |
| `scheduler` | `resource.json` | `jobCode + tenantId` | 调度表达式、脚本引用和状态 |
| `outbound_whitelist` | `resource.json` | host + recordId/version | 主机范围；连通性测试另行授权 |
| `data_import` | `resource.json` | `templateCode + recordId/version` | 模板配置和引用回读 |

`adapter_event` 是标准埋点注册事实，`script_log` 是运行证据，二者不是交付产物目录；只在 `artifacts.json` 的证据或依赖字段中引用。

## 4. `artifacts.json` 最小结构

```json
{
  "schema_version": 2,
  "issue": "cro-0000",
  "tenant": "SRM-EXAMPLE",
  "artifacts": [
    {
      "artifact_key": "independent:api-rewrite:SCRIPT_CODE",
      "kind": "independent_script",
      "subtype": {
        "quick_type_raw": "api_rewrite"
      },
      "identity": {
        "code": "SCRIPT_CODE"
      },
      "local": {
        "path": "artifacts/independent/api_rewrite/SCRIPT_CODE/entry.js",
        "sha256": "<sha256>"
      },
      "platform": {
        "id": "<string-or-null>",
        "version": "<string-or-null>",
        "state": "existing_unmodified"
      },
      "relations": [
        {
          "kind": "api_rewrite",
          "artifact_key": "api-rewrite:API_CODE:post",
          "stage": "post"
        }
      ],
      "verification": {
        "status": "passed",
        "checks": []
      }
    },
    {
      "artifact_key": "api-rewrite:API_CODE:post",
      "kind": "api_rewrite",
      "subtype": {
        "stage": "post"
      },
      "identity": {
        "api_code": "API_CODE"
      },
      "local": {
        "path": "artifacts/api-rewrite/API_CODE/post/resource.json"
      },
      "platform": {
        "id": "<string-or-null>",
        "version": "<string-or-null>",
        "state": "existing_unmodified"
      },
      "relations": [
        {
          "kind": "independent_script",
          "artifact_key": "independent:api-rewrite:SCRIPT_CODE"
        }
      ]
    }
  ]
}
```

每个真实平台对象单独一项，不把 Independent 源码与 API Rewrite/API Publish 合并成同一项。`artifact_key` 在当前交付包内唯一且稳定；平台长整型 ID 和版本以字符串保存。`stage` 属于关系资源或关系边，只在实际适用时填写；未知值保持 `null` 或 `TBD`，不能从文件名猜。

`platform.state` 使用能区分真实状态的值，例如 `local_only`、`existing_unmodified`、`plan_pending_confirmation`、`written_verified`。写入完成后更新版本、关系回读和最终校验哈希；没有执行平台写入时不得标成已发布或已部署。

## 5. 兼容旧目录

- 旧的 `srm-adaptor/`、`SCRIPT_LIB/`、`CodeBlock/`、`QueryBlock/` 继续原地维护；快捷修改不改路径、不批量迁移、不统一大小写。
- 完整增量交付若已有 `artifacts.json`，只补全 `schema_version`、`kind`、`subtype`、真实 `local.path` 和关系；除非用户明确要求整理目录，否则不移动现有文件。
- 同一交付包不得同时为同一平台对象维护两份源码。发生新旧路径冲突时，以 `artifacts.json` 指向的文件为候选，再与平台精确 `get` 比对；无法确定时停止覆盖。
- 历史需求号聚合搜索当前只覆盖已经验证支持描述筛选的资源类型。Constant 等未验证支持需求号描述筛选的资源，优先从 `artifacts.json`、需求中的明确编码或已知平台身份定位，不能因聚合搜索零命中判定不存在。
