# Marmot 需求开发设计门禁模板

这份模板用于需求目录内的 `design-gates.md`。只填写当前需求已经确认的事实；公共模板不预置租户、对象、字段、状态、服务编码或异常策略。未知项写 `TBD + 核实方式 + 阻塞影响`，不适用项写 `N/A + 理由`。

## 1. 需求与产物关系

```text
触发入口
  └─ 产物 A：输入范围 → 数据访问/关联 → 处理 → 输出/副作用
       └─ 产物 B：复用或消费 A 的结果
```

按实际需求填写每个产物的编码、角色、触发时机、调用关系、数据范围和副作用。

## 2. 字段来源和关联关系

| 目标字段/参数 | 来源类型 | 来源对象/变量 | 来源字段/表达式 | 类型 | 关联/转换条件 | 空值语义 | 证据与状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<target>` | 页面/API/数据库/平台对象/中间变量/固定配置 | `<source>` | `<field>` | `<type>` | `<join/transform>` | `<normal/error/skip>` | `<source/TBD>` |

要求：

- 同名字段在不同层出现时分行记录，不能把页面字段、数据库字段、中间变量和服务参数混为一项。
- 数据库关联通过实时字段结构和少量只读样例核实；可调用 `inspect_object_relation`。
- 字段不存在或关联未确认时停止相关映射代码，不创建隐含假设。

## 3. 外部服务契约

| 项目 | 当前需求确认值 | 证据 |
| --- | --- | --- |
| 服务编码 | `<code>` | `<doc/script/issue>` |
| 必填参数 | `<list>` | `<source>` |
| 禁止参数 | `<list>` | `<source>` |
| 对象参数结构 | `<parameter -> nested fields>` | `<source>` |
| 固定参数 | `<parameter -> value>` | `<source>` |
| 返回取值路径 | `<path>` | `<source>` |
| 顶层失败策略 | `<policy>` | `<source>` |
| 空结果策略 | `<policy>` | `<source>` |

契约由开发者根据当前需求、服务文档或已核实脚本人工核对，不沉淀为公共 MCP 规则。

## 4. 关键日志点

从下表选择当前脚本实际经过的阶段，不经过的阶段写 `N/A`。

| 阶段 | 建议记录 |
| --- | --- |
| 入口 | trace 上下文、业务 Key、状态、输入数量 |
| 数据访问 | 查询对象、关联字段、返回数量 |
| 关联补全 | 成功数量、失败数量、未匹配 Key |
| 请求构建 | 外部能力编码、参数数量、业务 Key |
| 外部响应 | 顶层状态、返回数量、空数据数量 |
| 字段映射 | 来源 Key、目标 Key、最终字段状态 |
| 持久化 | 更新数量、聚合或头级结果 |
| 分支结果 | 分支名称、跳过/继续/阻断原因 |

默认不记录完整业务对象和敏感报文。真实报文只能在显式联调开关打开时临时打印，并在联调后关闭。

## 5. 正常空值与异常场景

| 场景 | 前置条件 | 处理 | 是否阻断 | 日志阶段 | 证据 |
| --- | --- | --- | --- | --- | --- |
| `<scenario>` | `<condition>` | `<action>` | `<yes/no>` | `<stage>` | `<source>` |

必须区分“业务允许的空结果”和“调用/数据异常”，但具体语义由当前需求或契约决定。

## 6. 产物差异与数据范围

| 产物 | 触发时机 | 状态范围 | 数据范围 | 分页策略 | 聚合/头级重算 | 失败策略 |
| --- | --- | --- | --- | --- | --- | --- |
| `<code>` | `<trigger>` | `<states>` | `<current result/current page/all>` | `<strategy>` | `<yes/no/N/A>` | `<policy>` |

不得把一个产物的数据范围、状态集合或失败策略复制为其它产物的默认规则。

## 7. 静态检查规则与结果

根据本次门禁生成 `check_marmot_script_static.rules_json`，只放已确认规则：

```json
{
  "numeric_id_fields": [],
  "forbidden_direct_fields": [],
  "forbidden_service_parameters": [],
  "required_object_parameters": {},
  "required_constants": {},
  "required_log_stages": ["entry"],
  "full_scope_required": false
}
```

记录：

```text
- check_marmot_script_static：pass/warn/fail，源码 SHA-256：...
- 外部服务契约人工核对：pass/fail/N/A
- node --check：pass/fail
- 真实 trace：已验证/待补 traceId + from_time/to_time/N/A
- query_script_trace 关键阶段：...
- 未验证项：Marmot 运行时、数据库、事务、权限、远程服务（按实际填写）
```
