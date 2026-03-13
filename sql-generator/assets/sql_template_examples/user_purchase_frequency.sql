-- 业务场景: 用户购买频次分析
-- 说明: 统计用户在指定时间范围内的购买频次,识别高频用户
-- 涉及表: user, order, payment
-- 关联关系:
--   - user.id ↔ order.user_id (1:N)
--   - order.id ↔ payment.order_id (1:1)
-- 核心字段: user_id, payment_time, payment_status, amount

SELECT
    u.id AS user_id,
    u.user_name,
    u.phone,
    COUNT(p.id) AS purchase_count,
    SUM(p.amount) AS total_amount,
    AVG(p.amount) AS avg_amount,
    MIN(p.payment_time) AS first_purchase_time,
    MAX(p.payment_time) AS last_purchase_time,
    DATEDIFF(MAX(p.payment_time), MIN(p.payment_time)) AS days_range,
    CASE
        WHEN COUNT(p.id) >= 10 THEN '超高频用户'
        WHEN COUNT(p.id) >= 5 THEN '高频用户'
        WHEN COUNT(p.id) >= 2 THEN '中频用户'
        ELSE '低频用户'
    END AS user_type
FROM user u
INNER JOIN `order` o ON u.id = o.user_id
INNER JOIN payment p ON o.id = p.order_id
WHERE p.payment_time BETWEEN '{start_date}' AND '{end_date}'
  AND p.payment_status = 1
GROUP BY u.id, u.user_name, u.phone
HAVING COUNT(p.id) >= {min_purchase_count}
ORDER BY purchase_count DESC, total_amount DESC;
