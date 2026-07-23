-- =============================================================
-- 场景：询价单核价/评分完成后回退至「报价中」（数据修复）
-- 适用：状态被推进过头，需要退回让供应商重新报价或重新核价/评分
-- 涉及表：
--   ssrc_rfx_header          (rfx_status 需回退)
--   ssrc_rfx_header_expand   (rfx_real_status 必须同步，1:1 关联)
--   spfm_pending_message     (插入延时消息触发系统状态刷新)
-- 关键关联：ssrc_rfx_header_expand.rfx_header_id = ssrc_rfx_header.rfx_header_id
-- 占位符：
--   <tenant_id>            租户ID（先 SELECT tenant_id FROM hpfm_tenant WHERE tenant_num='<租户编码>'）
--   <rfx_header_id>        询价单主键（先按 rfx_num 查得）
--   <execute_time>         延时消息执行时间，建议设为当前时间稍后（如 NOW()+INTERVAL 1 MINUTE）
-- 已验证：✅ 已验证（spfm_pending_message 固定字段值经核对正确；表/字段名见 ssrc-sql-generator SKILL 延时消息规则）
-- 注意：
--   1) rfx_status 与 rfx_real_status 必须一起改，否则界面与系统实际状态不一致；
--   2) 必须先 SELECT 确认影响行数（应为 1）再执行；
--   3) spfm_pending_message 的 biz_type/server_name/execute_type/executed_flag/object_version_number
--      为系统固定值，请勿修改。
-- =============================================================

-- 第 1 步：确认目标单据（影响行数应为 1，且 tenant_id 匹配）
SELECT rfx_header_id, rfx_num, rfx_status, tenant_id
FROM ssrc_rfx_header
WHERE rfx_header_id = <rfx_header_id>
  AND tenant_id = <tenant_id>;

-- 第 2 步：回退主表状态为「报价中」(IN_QUOTATION)
UPDATE ssrc_rfx_header
SET rfx_status = 'IN_QUOTATION',
    object_version_number = object_version_number + 1,
    last_update_date = NOW(),
    last_updated_by = <user_id>
WHERE rfx_header_id = <rfx_header_id>
  AND tenant_id = <tenant_id>;

-- 第 3 步：同步扩展表实际状态（1:1 关联）
UPDATE ssrc_rfx_header_expand
SET rfx_real_status = 'IN_QUOTATION',
    object_version_number = object_version_number + 1,
    last_update_date = NOW(),
    last_updated_by = <user_id>
WHERE rfx_header_id = <rfx_header_id>
  AND tenant_id = <tenant_id>;

-- 第 4 步：插入延时消息，触发系统状态刷新
INSERT INTO spfm_pending_message (
    pending_message_id, tenant_id, biz_id, biz_type, server_name,
    execute_type, execute_time, executed_flag, expand_param, adaptor_code,
    object_version_number, creation_date, created_by, last_update_date, last_updated_by
) VALUES (
    <pending_message_id>, <tenant_id>, '<rfx_header_id>', 'RFX', 'srm-source',
    'QUOTATION_END_REFRESH_RFX_STATUS', <execute_time>, '0', NULL, NULL,
    1, NOW(), <user_id>, NOW(), <user_id>
);
