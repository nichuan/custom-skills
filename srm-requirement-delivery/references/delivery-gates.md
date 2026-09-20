# Marmot 需求设计门禁模板

用于新增脚本、契约级修改、平台绑定或多产物需求的 `design-gates.md`。不适用于已有脚本的明确局部修改，也不要求标准 Java 需求创建这份文件。

只填写当前需求已确认且适用的事实。未知项写 `TBD + 核实方式 + 阻塞影响`；不适用项写 `N/A + 理由`。任何阻止正确编码的 `TBD` 必须先解决，非阻塞未知可以保留为未验证项。

## 1. 模式与产物身份

| 产物 | 角色 | tenant | 主编码 | 子身份 | quickType/阶段 | 当前状态 |
| --- | --- | --- | --- | --- | --- | --- |
| `<artifact>` | Adapter/Independent/CodeBlock/QueryBlock/Constant/API 关系/其它配置资源 | `<tenant>` | `<taskCode/scriptCode/resourceCode>` | `<runningService/lineId/recordId>` | `<平台原始 quickType 或独立阶段>` | `<existing/new/TBD>` |

记录事实源：需求/评论、标准源码位置、平台 `get` 版本与源码哈希、平台资源版本、本地路径。Independent 的原始 `quickType` 与 API 前/后置阶段分列；每个真实平台对象单独一行。

## 2. 需求与产物关系

```text
标准入口或发布入口
  ├─ 脚本源码：输入 → 处理 → 输出/副作用
  └─ 平台关系：apiCode/事件 → 阶段 → scriptCode → 绑定或发布资源
```

按实际需求写明产物依赖、执行顺序和验收条件。脚本源码、Adapter Header/Line、API 改写绑定和 API 发布资源分别列项。

## 3. 触发、输入与输出契约

| 项目 | 已确认值 | 证据 | 状态 |
| --- | --- | --- | --- |
| 标准入口/HTTP 路由 | `<class#method or METHOD /path>` | `<source>` | `<confirmed/TBD>` |
| 触发时机与调用次数 | `<before/after/publish; once/per-item/batch>` | `<source>` | `<status>` |
| 输入根对象与类型 | `<DTO/HTTP Context/Map/List>` | `<source/fixture>` | `<status>` |
| 可读/可写范围 | `<fields and mutation rules>` | `<source>` | `<status>` |
| 返回根对象与消费方 | `<type/path/consumed or ignored>` | `<source>` | `<status>` |
| 缺失脚本/空结果 | `<skip/original/error/...>` | `<source>` | `<status>` |
| 异常与事务 | `<propagate/swallow/rollback/independent>` | `<source>` | `<status>` |

Adapter、API 前置、API 后置和 API 发布必须分别填写，不能复制同一契约。

## 4. 字段来源和关联关系

| 目标字段/参数 | 来源类型 | 来源对象/变量 | 来源字段/表达式 | 类型 | 关联/转换条件 | 空值语义 | 证据与状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<target>` | 页面/API/数据库/平台对象/中间变量/固定配置 | `<source>` | `<field>` | `<type>` | `<join/transform>` | `<normal/error/skip>` | `<source/TBD>` |

- 同名字段在不同层出现时分行记录，不能把页面字段、数据库字段、中间变量和服务参数混成一项。
- 数据库关联只在正确实现需要时通过真实结构和少量只读样例核实；可使用 `inspect_object_relation`。
- 字段不存在、类型或关联未确认时停止对应映射，不按名称猜测。

## 5. 平台关系与版本

| 关系 | 来源 | 目标 | 阶段/quickType | 当前版本 | 预期动作 | 回读状态 |
| --- | --- | --- | --- | --- | --- | --- |
| Adapter Event/Header/Line | `<taskCode>` | `<runningService + lineId>` | `<event>` | `<version>` | `<none/create/deploy>` | `<status>` |
| API Rewrite | `<apiCode>` | `<scriptCode>` | `<pre/post>` | `<version>` | `<none/create/update>` | `<status>` |
| API Publish | `<route/code>` | `<scriptCode>` | `<平台原始 quickType>` | `<version>` | `<none/create/update>` | `<status>` |
| Block 引用 | `<caller>` | `<blockCode>` | `<relation>` | `<version>` | `<action>` | `<status>` |
| Constant 引用 | `<caller>` | `<constantCode>` | `N/A` | `<version>` | `<none/create/update>` | `<status>` |
| Consumer/Scheduler | `<topic/jobCode>` | `<scriptCode/CodeBlock>` | `<quickType>` | `<version>` | `<none/create/update>` | `<status>` |

脚本存在不代表绑定或发布生效。新对象尚未创建时版本写 `N/A`，不要伪造平台 ID。

## 6. 数据、外部服务与副作用

### 数据库/平台写入

| 写入目标 | 租户/业务过滤 | 更新字段 | 调用次数 | 幂等/重复处理 | 事务与回滚 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| `<target>` | `<filters>` | `<fields>` | `<count>` | `<policy>` | `<policy>` | `<source>` |

### 外部服务

| 项目 | 当前需求确认值 | 证据 |
| --- | --- | --- |
| 服务编码/接口 | `<code>` | `<source>` |
| 必填/禁止参数 | `<lists>` | `<source>` |
| 对象参数与固定值 | `<shape/values>` | `<source>` |
| 返回取值路径 | `<path>` | `<source>` |
| 超时/失败/空结果策略 | `<policy>` | `<source>` |

没有数据库或外部服务时写 `N/A + 理由`，不创建空洞规则。

## 7. 数据范围、状态与分页

| 产物 | 状态范围 | 数据范围 | 分页策略 | 聚合/头级重算 | 重复触发语义 | 失败策略 |
| --- | --- | --- | --- | --- | --- | --- |
| `<code>` | `<states>` | `<current/current page/all>` | `<strategy>` | `<yes/no/N/A>` | `<policy>` | `<policy>` |

具体状态和范围只能来自当前需求或已核实契约，不把一个产物的设置当作其它产物的默认值。

## 8. 日志、安全与场景矩阵

按实际逻辑选择入口、数据访问、关联补全、请求构建、外部响应、字段映射、持久化和分支结果等日志阶段。默认只记录数量、ID、业务 Key 和状态；不记录 Token、凭据、完整敏感对象或报文。真实报文只在显式联调开关下临时输出，并在交付前关闭。

| 场景 | 前置条件 | 处理 | 是否阻断 | 事务/副作用 | 日志阶段 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| 正常 | `<condition>` | `<action>` | `<yes/no>` | `<effect>` | `<stage>` | `<source>` |
| 空值/空集合 | `<condition>` | `<action>` | `<yes/no>` | `<effect>` | `<stage>` | `<source>` |
| 重复调用 | `<condition>` | `<action>` | `<yes/no>` | `<effect>` | `<stage>` | `<source>` |
| 下游失败 | `<condition>` | `<action>` | `<yes/no>` | `<effect>` | `<stage>` | `<source>` |

按需求补权限、非法输入、部分成功、分页边界等场景；不强制制造不适用用例。

## 9. 静态规则与验证记录

根据已确认事实生成 `check_marmot_script_static.rules_json`，只放适用规则：

```json
{
  "numeric_id_fields": [],
  "forbidden_direct_fields": [],
  "forbidden_service_parameters": [],
  "required_object_parameters": {},
  "required_constants": {},
  "required_log_stages": [],
  "full_scope_required": false
}
```

记录最终结果：

```text
- node --check：pass/fail/N/A
- check_marmot_script_static：pass/warn/fail；最终源码 SHA-256：...
- CodeBlock 检查：pass/fail/N/A；引用关系：已核实/未核实
- QueryBlock 检查：pass/fail/N/A
- Constant/配置资源：身份与版本已核实/未核实；秘密值：不进入本地产物
- DEV Debug：pass/fail/NO_VALID_FIXTURE/未要求；Input 来源：...
- 真实 trace：已验证/待补时间范围/N/A
- 平台源码：仅本地/平台未改/待确认计划/已写入并回读
- API Rewrite / API Publish / Adapter 状态：逐项填写
- 未验证项：GraalJS、数据库、权限、事务、网关、远程服务（只保留实际未验证项）
```
