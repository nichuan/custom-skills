-- 业务场景: 商品销量分析
-- 说明: 统计商品在指定时间范围内的销量和销售额,按分类分组
-- 涉及表: product, order, order_item, category
-- 关联关系:
--   - order.id ↔ order_item.order_id (1:N)
--   - product.id ↔ order_item.product_id (1:N)
--   - category.id ↔ product.category_id (N:1)
-- 核心字段: product_id, product_name, category_id, quantity, total_amount, create_time

SELECT
    c.category_id,
    c.category_name,
    p.product_id,
    p.product_name,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.total_amount) AS total_amount,
    COUNT(DISTINCT o.id) AS order_count,
    AVG(oi.price) AS avg_price
FROM order_item oi
INNER JOIN `order` o ON oi.order_id = o.id
INNER JOIN product p ON oi.product_id = p.id
INNER JOIN category c ON p.category_id = c.id
WHERE o.create_time BETWEEN '{start_date}' AND '{end_date}'
  AND o.order_status IN (2, 3)
  AND p.status = 1
GROUP BY c.category_id, c.category_name, p.product_id, p.product_name
ORDER BY c.category_id, total_quantity DESC;
