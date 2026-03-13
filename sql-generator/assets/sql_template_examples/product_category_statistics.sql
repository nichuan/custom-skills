-- 业务场景: 商品分类统计
-- 说明: 统计各商品分类的商品数量、销量和销售额
-- 涉及表: category, product, order, order_item
-- 关联关系:
--   - category.id ↔ product.category_id (N:1)
--   - product.id ↔ order_item.product_id (1:N)
--   - order.id ↔ order_item.order_id (1:N)
-- 核心字段: category_id, category_name, level, product_id, quantity, total_amount, create_time

SELECT
    c.id AS category_id,
    c.category_name,
    c.level,
    COUNT(DISTINCT p.id) AS product_count,
    COUNT(DISTINCT CASE WHEN p.status = 1 THEN p.id END) AS active_product_count,
    COALESCE(SUM(oi.quantity), 0) AS total_sales_quantity,
    COALESCE(SUM(oi.total_amount), 0) AS total_sales_amount,
    COALESCE(AVG(p.price), 0) AS avg_price
FROM category c
LEFT JOIN product p ON c.id = p.category_id
LEFT JOIN order_item oi ON p.id = oi.product_id
LEFT JOIN `order` o ON oi.order_id = o.id
    AND o.create_time BETWEEN '{start_date}' AND '{end_date}'
    AND o.order_status IN (2, 3)
WHERE c.status = 1
GROUP BY c.id, c.category_name, c.level
ORDER BY c.level, c.sort_order, total_sales_amount DESC;
