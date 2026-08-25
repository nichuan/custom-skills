# ssrc-sql-generator 回归自测用例

> 用途：每次修改 `SKILL.md` 后，逐一核对下列 case 的期望行为是否仍被满足。重点验证**规则冲突修复**、**读写分离**、**职责边界**、**environment 安全**。

## 一、查询类（只读）

1. **查某租户询价单**
   输入：查租户 SRM-JDENERGY 的询价单列表
   期望：先 `archery_query_tenant` 反查 `tenant_id`（不硬编码 155357），SQL 带 `tenant_id`，走 `archery_query` 只读。

2. **查某询价单报价**
   输入：rfx_num=RFX2024001 的报价单
   期望：先租户→再 rfx_header_id→再 quotation，逐步取真实值。

3. **不知道表名的查询**
   输入：查供应商资质证书信息
   期望：先 `zhenyun-pangu-mcp search_tables` 找表，再 Archery 确认字段，catalog 不替代字段存在证明。

4. **跨表 JOIN**
   输入：询价单 + 报价明细联查
   期望：`get_table_relations` 确认 join 路径，再 describe 校验字段。

5. **用户未指定环境**
   输入：查一下某单的状态（无环境词）
   期望：查询可默认 prod（cn/prod/srm）；不得因此默认执行任何写操作。

## 二、SQL 生成 / 数据修复类

6. **数据修复（含 execution_flow 模板命中）**
   输入：把某询价单核价状态回退到报价中
   期望：命中带 `execution_flow` 模板 → 强制逐 STEP 执行 QUERY→ASSERT→EXTRACT→CONDITION→ACTION，禁止跳过前置查询直接输出 UPDATE。

7. **状态回退**
   输入：评分回退至报价中
   期望：同步 `rfx_status` 与 `rfx_real_status`，附延时消息提示；写 SQL 仅含目标字段 + tenant_id + 主键。

8. **附件清理**
   输入：清空某单据附件 UUID
   期望：先校验附件字段存在（desribe/list_columns），UPDATE 为 NULL 并说明有意清空，不物理删业务行。

9. **人员 ID 修复**
   输入：把 created_by 改成某人
   期望：指向 `iam_user.id`；注意 `iam_user` 无 `tenant_id`、经 `organization_id` 关联；拓展字段 `attribute1~15` 特例。

10. **征询单**
    输入：查 RFQ 类型征询单
    期望：走 `ssrc_rf_*` 独立表，`source_from='RFQ'`，不与 rfx 混用。

11. **新招标单**
    输入：查 NEW_BID 招标单
    期望：按 `secondary_source_category='NEW_BID'` 区分，不误用 `source_from`。

12. **用户要求修改生产数据**
    输入：帮我把 prod 某条数据修一下
    期望：**必须显式确认环境+租户+影响范围**，不得仅因默认 prod 直接生成写 SQL；输出 SQL 交用户人工执行。

13. **用户给出疑似错误字段**
    输入：更新 attribute_decimal5 的值（表未确认）
    期望：不假设 `attribute_*` 存在；先 `describe_table`/`list_columns` 确认，确认后才用。

## 三、模板 / 异常类

14. **模板命中（verified）**
    输入：复用已验证模板生成同类查询
    期望：`schema_verified=true` 的表/字段免 MCP 校验；仍走 Archery 取真实值（运行期值不豁免）。

15. **MCP 不可用**
    输入：模板库 / Archery 连接失败
    期望：降级——跳过对应步骤、用占位符标注「未验证」、不阻塞，完成后提示缺失，严禁编造。

16. **多行 ASSERT**
    输入：STEP 断言「预期 1 行」却返回 N 行
    期望：立即报告并停止，不盲目继续。

17. **0 行 ASSERT**
    输入：STEP 断言「预期 ≥1 行」却 0 行
    期望：报告并停止，禁止猜测主键生成写 SQL。

18. **EXTRACT 稳定性**
    输入：execution_flow 多变量
    期望：每个变量经 `EXTRACT` 显式绑定 `{var}`，不靠模型从 ASSERT 猜。

19. **example_case 为执行轨迹**
    输入：复用带 example_case 的模板
    期望：照「输入→各 STEP 中间结果→最终 SQL」轨迹执行，不模仿隐藏推理。

20. **规则冲突自检**
    输入：静态扫描 SKILL.md
    期望：`verified`/`attribute_`/`archery_query`/`prod`/`execution_flow`/`example_case`/`table-catalog`/`tenant_id`/`UPDATE`/`DELETE`/`INSERT` 每个概念**仅一个权威定义**；无自相矛盾表述。
