-- 业务场景: 用户订单分析
-- 说明: 查询用户在指定时间范围内的订单情况,包括订单数、总金额、平均订单金额
-- 涉及表: user, order
-- 关联关系: user.id ↔ order.user_id (1:N)
-- 核心字段: user_id, order_no, order_amount, order_status, create_time

SELECT
    u.id AS user_id,
    u.user_name,
    COUNT(o.id) AS order_count,
    SUM(o.order_amount) AS total_amount,
    AVG(o.order_amount) AS avg_amount,
    MAX(o.create_time) AS last_order_time
FROM user u
INNER JOIN `order` o ON u.id = o.user_id
WHERE o.create_time >= DATE_SUB(NOW(), INTERVAL {days} DAY)
  AND o.order_status IN (2, 3)
GROUP BY u.id, u.user_name
ORDER BY total_amount DESC;
