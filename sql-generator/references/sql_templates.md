# 寻源常用的数据修复场景SQL模板

***前置重要查询***

```sql
#租户查询，其他的查询都要先查出租户ID，租户ID作为其它SQL的必要条件
select tenant_id,tenant_name from hpfm_tenant where tenant_num = 'SRM-SINOFUSE';
```

1.修复报价方向

```sql
#先使用租户查询，查到tenant_id，然后使用tenant_Id+rfx_num查出询价单信息，然后进一步根据tenant_id+询价单id修复auction_direction
select * from ssrc_rfx_header where tenant_id = 51070 and rfx_num = 'BID2026030200004';
update ssrc_rfx_header set auction_direction = 'NONE' where tenant_id = 51070 and rfx_header_id = 5889091; 
```

2.删除专家

```sql
#查询专家信息
select 
    see.evaluate_expert_id,
    iu.login_name,
    iu.real_name,
    see.team,
    see.sequence_num,
    see.expert_user_id,
    see.expert_status,
    see.scored_status
from ssrc_evaluate_expert see join iam_user iu on see.expert_user_id = iu.id
where see.source_header_id = 5763857 and see.source_from = 'RFX' and see.tenant_id = 417088;
#查询要素信息
select * from ssrc_evaluate_insdic_assign where tenant_id = 417088 and source_header_id = 5763857 and evaluate_expert_id = 520399;
#删除专家和这个专家的分配要素
delete from ssrc_evaluate_indic_assign where tenant_id  = 417088 and indic_assgin_id in ();

```

3.询价单修复采购员

    #先查询出单据信息
    select * from ssrc_rfx_header where tenant_id = 51070 and rfx_num = 'BID2026030200004';
    #查出要修复成哪个采购员
    select * from 
    update ssrc_rfx_header set auction_direction = 'NONE' where tenant_id = 51070 and rfx_header_id = 5889091;

4.修复评分要素最高分

```sql
--1、查询租户id
SELECT tenant_id FROM hpfm_tenant WHERE tenant_num = 'SRM-ANQIJIAOMU'
--2、查询需要修复的要素数据
SELECT 
    h.rfx_header_id,
    h.rfx_num,
    i.evaluate_indic_id,
    h.tenant_id,sq
    i.indicate_name,
    i.weight,
    i.min_score,
    i.max_score
FROM ssrc_rfx_header h
LEFT JOIN ssrc_evaluate_indic i ON i.tenant_id = h.tenant_id and h.rfx_header_id = i.source_header_id and i.source_from  = 'RFX'
WHERE h.tenant_id = 3546
AND h.rfx_num = 'BID2026020400001';
--3、修复评分要素最高分SQL模板
UPDATE ssrc_evaluate_indic 
SET max_score = 4.00 
WHERE evaluate_indic_id = 647869 AND tenant_id = 3546;
```

5.征询单待确定供应商，退回至评分中

```sql
--先查租户
select * from hpfm_tenant where tenant_num = 'SRM-COMAC01';
--查单据
select * from ssrc_rf_header where rf_num = 'RFI2025102900001' and tenant_id = 36466;
--查征询专家表
select * from ssrc_rf_expert where rf_header_id = 35139;
--查询真实专家表
select * from ssrc_evaluate_expert where source_header_id = 35139;
--修复单据状态为评分中
update ssrc_rf_header set display_rf_status ='SCORING' where rf_header_id = 35139 and tenant_id = 36466;
--修复专家状态为未评分
update ssrc_evaluate_expert set scored_status = 'NEW' where tenant_id = 36466 and evaluate_expert_id in (492160,492158,492159);
```

6.寻源结果被占用了，释放寻源结果

```sql
--查询当前寻源结果的数据
select result_id,receipts_status,occupation_quantity,source_result_execute_status,result_execution_strategy,quantity,item_num,source_num from ssrc_source_result where tenant_id =1 and source_num='RFX2025051300005';
--查询寻源结果的历史占用
select  history_id from ssrc_source_result_change_history where tenant_id=1 and source_result_id in (1537);
--删除占用历史
DELETE from ssrc_source_result_change_history where history_id = 3302;
--更新寻源结果
UPDATE ssrc_source_result set receipts_status = NULL,occupation_quantity = 0, source_result_execute_status ='UNEXECUTED',result_execution_strategy = 'BLANK'  where result_id = 1321
```






