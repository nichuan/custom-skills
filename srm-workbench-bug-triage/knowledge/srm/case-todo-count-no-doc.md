# 案例：/card-search/query 待办 count 有值但无单据（权限维度不匹配）

> 来源：客户本地环境实测排查（租户1，RFX2026081900002，rfxHeaderId=2937；及 SSLM 供应商考察单 documentId=1243）
> 类型：搜索类问题（根因为两段式 ES 查询 + 用户对单据权限维度不匹配）
> 用途：后续遇到"卡片/待办 count 有值、但列表没有单据"时，优先套用本案例的排查思路。

## 1. 现象
用户采购员工作台 `/card-search/query` 查询**待办**时，页面 **count 有值（如 1/2），但列表没有单据**。
待办本身能查到（订阅命中），单据却因为权限被过滤掉。

## 2. 核心机制：两段式 ES 查询 + 两套过滤逻辑（不是 bug）
**待办和单据是分开查两次 ES 的**，过滤逻辑完全不同：

| 步骤 | 方法 | ES 索引 | 过滤条件 | 结果 |
|---|---|---|---|---|
| ① 待办查询 | `EsSearchServiceImpl#buildTodoDataSearchDSL` | `srm_todo_record` | 只按**订阅命中**（subscriptionUser=当前用户 / subscriptionRole=当前角色，minimum_should_match=1）+ tenantId + combineCode + todoCode；**不拼权限、不拼创建人** | 待办能查到 → count 有值 ✅ |
| ② 回查单据 | `handleTodoDataResponse` → `buildDocSearchRequest` → `permissionQueryBuild` | 单据索引（如 `srm_c_srm_ssrc_rfx_header`） | 按权限维度过滤：USER 维度拼 `header.createdBy=当前用户`；BIZ 维度拼 `access.维度=accessGroupId` | 单据可能被过滤 ❌ |

### 关键点 1：待办查询为什么不拼权限
- WORKFLOW 类型待办：`buildTodoDataSearchDSL` 里 `this.permissionQueryBuild(...)` 这行**被注释掉了**，所以不拼权限。
- TODO 类型待办：调用了 `todoPermissionQueryBuild`，但若 `docAccessMap.get(combineCode)` 为空（用户对该单据类型无维度权限），`CollectionUtils.isNotEmpty(docAccessList)` 不成立，同样不拼任何权限。
- 所以待办只按"订阅"过滤 → 订阅命中就能查到。

### 关键点 2：回查单据时会拼权限
`buildDocSearchRequest` 里调用 `permissionQueryBuild`：
```java
for (String docAccess : docAccessList) {
    String[] split = docAccess.split("::");
    if (USER.equals(split[0])) {
        boolQueryBuilder.filter(termQuery(EsUtils.getHeaderField(split[1]),
            DetailsHelper.getUserDetails().getUserId()));   // 如 header.createdBy = 当前用户
    } else if (BIZ.equals(split[0])) {
        boolQueryBuilder.filter(termQuery("access." + split[1], accessGroupId));
    }
}
```

## 3. 权限机制（关键背景，来自用户补充）
- ES 里单据 `access` 块的**字段名**是 `COMPANY` / `PURCHASE_AGENT` / `PURCHASE_ORGANIZATION` 这类**维度类型**（不是数据库字段 `companyId` 驼峰）。
- `access` 块里的**数组值** = `swbh_auth_access.auth_access`，即**权限组 id 集合**（不是业务 id / 单据字段值）。
- 权限体系表：
  - `swbh_access_group`（权限组，access_group_id）
  - `swbh_user_access_group`（用户归属权限组：user_id ↔ access_group_id）
  - `swbh_auth_access`（权限组 id 对应维度值与权限组集合：auth_type_code / auth_value / auth_access）
- **插入 ES 时的逻辑**：先按 `swbh_doc_type_dimension_mapping` 配置的字段，查 `swbh_auth_access` 拿到 `auth_access`（权限组 id 集合），写入单据 ES 的 `access` 块。
- `swbh_doc_type_dimension_mapping`：单据权限维度映射，只在 **BIZ 维度**生效，决定某单据类型哪些 BIZ 维度参与 ES 权限过滤；**USER 维度不经过它**（USER 维度直接放行，需 ruleType=COLUMN）。

## 4. 权限维度的两个来源（`listDocTypeDim` 返回）
`RoleAuthorityRepository#listDocTypeDim`（`hiam_doc_type_auth_dim` + `hiam_role_authority_line` + `hiam_user_authority`）返回用户对某单据类型的生效维度：
- **USER 维度**：`source_match_field` 对应单据字段（如 `created_by`），ruleType=COLUMN，构造为 `USER::createdBy` → 拼 `header.createdBy=当前用户`。
- **BIZ 维度**：`auth_type_code`（如 COMPANY），构造为 `BIZ::COMPANY` → 拼 `access.COMPANY=accessGroupId`。
- 在 `queryDocAccess` 里：USER 维度 `(USER && COLUMN)` 直接放行；BIZ 维度必须命中 `swbh_doc_type_dimension_mapping`。

## 5. 真实案例
### 案例 A：RFX 寻源单
- 待办：`SSRC.RFX_APPROVAL_WFL`（WORKFLOW 类型），订阅用户 `subscriptionUser=[1318309]`，单据 documentId=2937。
- 用户 1318309 对 RFX 单据只有一条生效权限：**USER 维度 `CREATED_BY`（source_match_field=created_by，rule_type=COLUMN）**。
- 单据 RFX2026081900002 的 `createdBy=1318241`（≠1318309）。
- 结果：待办查询只按订阅命中（count=1）；回查单据时 `permissionQueryBuild` 拼 `header.createdBy=1318309` → 单据被过滤 → **count 有值、无单据**。

### 案例 B：SSLM 供应商考察单
- 待办：`SSLM.INVE.FUN_APPROVE` / `SSLM.INVE.FUN_APPROVE_NEW`（TODO 类型，subscriptionUser=-2147483648 即 Integer.MIN_VALUE，按**角色订阅**，subscriptionRole 命中当前角色 1087417）。
- 待办 DSL 只有订阅 + combineCode + tenantId + todoCode，**无权限条件** → count=2。
- 回查单据时若用户对该单据类型无维度权限 → 单据被过滤 → count 有值、无单据。

## 6. 排查路径（按顺序）
1. **捞 `/card-search/query` 请求日志里的两段 DSL**：
   - 第一段（待办 `srm_todo_record`）：只有订阅（subscriptionUser/role）+ combineCode + tenantId + todoCode，**没有 createdBy / access**。
   - 第二段（单据索引）：有 `header.createdBy=当前用户`（USER 维度）或 `access.维度=accessGroupId`（BIZ 维度）。
   - 若待办段能查到、单据段被过滤 → 就是这个根因。
2. **确认用户对该单据类型的权限维度**：
   ```sql
   SELECT hdt.doc_type_code, hdtad.auth_type_code, hdtad.source_match_field,
          hdtd.dimension_type, hral.role_auth_line_id, hral.rule_type
   FROM srm.hiam_doc_type_auth_dim hdtad
   INNER JOIN srm.hiam_doc_type_dimension hdtd ON hdtad.auth_type_code = hdtd.dimension_code
   LEFT JOIN srm.hiam_role_authority hra
          ON hra.auth_doc_type_id = hdtad.doc_type_id AND hra.role_id = #{当前角色}
   LEFT JOIN srm.hiam_role_authority_line hral
          ON hral.role_auth_id = hra.role_auth_id AND hral.auth_type_code = hdtad.auth_type_code
   JOIN srm.hiam_doc_type hdt ON hdt.doc_type_id = hdtad.doc_type_id
   WHERE hdt.doc_type_code = #{单据类型编码}
     AND hral.role_auth_line_id IS NOT NULL;
   ```
   - 若只有 USER 维度（createdBy）→ 用户只能看自己创建的单据。
3. **查单据 ES 的 createdBy / access**：
   ```
   index: 对应单据索引（如 srm_c_srm_ssrc_rfx_header）
   query: header 主键 = documentId
   ```
   - 看 `createdBy` 是否 = 当前用户；或 `access` 块是否含当前用户权限组 id。
4. **查用户权限维度值**（`hiam_user_authority` + `hiam_user_authority_line`）：
   ```sql
   SELECT hua.authority_type_code, hua.include_all_flag, hua.include_null_flag, hual.data_id
   FROM srm.hiam_user_authority hua
   LEFT JOIN srm.hiam_user_authority_line hual ON hua.authority_id = hual.authority_id
   WHERE hua.tenant_id = #{tenantId} AND hua.user_id = #{userId};
   ```
   - `include_all_flag=1` 表示该维度不限制；否则看 data_id 是否命中单据维度。

## 7. 涉及表 / 类
- 权限表：`swbh_access_group`、`swbh_user_access_group`、`swbh_auth_access`、`swbh_doc_type_dimension_mapping`（存在 `srm.spfm_rel_table_record`，table_code='swbh_doc_type_dimension_mapping'）、`hiam_user_authority`、`hiam_user_authority_line`、`hiam_doc_type_auth_dim`、`hiam_doc_type_dimension`、`hiam_role_authority`、`hiam_role_authority_line`、`swbh_todo_definition`
- 代码：
  - `CardSearchServiceImpl#query`（入口）
  - `EsSearchServiceImpl#buildTodoDataSearchDSL`（待办查询，WORKFLOW 的 permissionQueryBuild 被注释）
  - `EsSearchServiceImpl#buildDocSearchRequest` / `permissionQueryBuild`（单据查询，拼权限）
  - `EsSearchServiceImpl#handleTodoDataResponse`（待办命中后回查单据）
  - `RoleAuthorityServiceImpl#queryDocAccess` / `RoleAuthorityRepository#listDocTypeDim`（构造 docAccessMap）

## 8. 修复方向
- 若用户**本不该看**该单据 → 待办订阅配错，修正 `swbh_todo_definition` 里对应 todoCode 的订阅规则（把订阅给真正应该处理的人/角色）。
- 若用户**应该看** → 给该角色增加 BIZ 维度权限（如 PURCHASE_AGENT / COMPANY / PURCHASE_ORGANIZATION），而非只配 USER/CREATED_BY；然后重新触发权限同步。

## 9. 避坑点（沉淀给后续）
- 待办 count 有值 ≠ 单据能显示；待办按订阅、单据按权限，两者独立。
- 待办查询的 DSL 里**没有权限条件**是正常的（WORKFLOW 的 permissionQueryBuild 被注释、TODO 的 todoPermissionQueryBuild 在无维度时为空）。
- 单据查询才会拼 `createdBy`（USER 维度）或 `access`（BIZ 维度）。
- USER 维度（createdBy）不经过 `swbh_doc_type_dimension_mapping`，BIZ 维度才经过。
- ES `access` 块字段名是大写维度类型，值是权限组 id 集合，不是业务 id。
- 优先对比两段 DSL：待办段无权限、单据段有权限 → 基本就是这个根因。
