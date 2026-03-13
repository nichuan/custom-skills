# SQL通用模板

本文件提供常用的SQL查询模板,用于快速生成符合规范的SQL语句。

---

## 时间范围过滤模板

### 按天过滤
```sql
-- 最近N天
WHERE create_time >= DATE_SUB(NOW(), INTERVAL {days} DAY)

-- 指定日期区间
WHERE create_time BETWEEN '{start_date}' AND '{end_date}'

-- 今天
WHERE DATE(create_time) = CURDATE()

-- 昨天
WHERE DATE(create_time) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)

-- 本周
WHERE YEARWEEK(create_time, 1) = YEARWEEK(CURDATE(), 1)

-- 本月
WHERE DATE_FORMAT(create_time, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')
```

### 按小时过滤
```sql
-- 最近N小时
WHERE create_time >= DATE_SUB(NOW(), INTERVAL {hours} HOUR)
```

---

## 表关联模板

### INNER JOIN (内连接)
```sql
-- 基础内连接
SELECT a.field1, a.field2, b.field1
FROM table_a a
INNER JOIN table_b b ON a.join_key = b.join_key

-- 多表内连接
SELECT a.field1, b.field1, c.field1
FROM table_a a
INNER JOIN table_b b ON a.key1 = b.key1
INNER JOIN table_c c ON b.key2 = c.key2
```

### LEFT JOIN (左连接)
```sql
-- 基础左连接(保留左表所有记录)
SELECT a.field1, b.field1
FROM table_a a
LEFT JOIN table_b b ON a.join_key = b.join_key
WHERE b.join_key IS NULL  -- 查找左表有但右表没有的记录
```

### RIGHT JOIN (右连接)
```sql
-- 基础右连接(保留右表所有记录)
SELECT a.field1, b.field1
FROM table_a a
RIGHT JOIN table_b b ON a.join_key = b.join_key
```

---

## 聚合统计模板

### 基础聚合函数
```sql
-- 计数
SELECT COUNT(*) AS total_count FROM table_name WHERE condition;

-- 求和
SELECT SUM(amount) AS total_amount FROM table_name WHERE condition;

-- 平均值
SELECT AVG(price) AS avg_price FROM table_name WHERE condition;

-- 最大值/最小值
SELECT MAX(price) AS max_price, MIN(price) AS min_price
FROM table_name WHERE condition;
```

### GROUP BY 聚合
```sql
-- 单字段分组
SELECT category_id, COUNT(*) AS count, SUM(amount) AS total
FROM table_name
GROUP BY category_id;

-- 多字段分组
SELECT category_id, create_date, COUNT(*) AS count
FROM table_name
GROUP BY category_id, create_date;

-- 分组后过滤(HAVING)
SELECT user_id, COUNT(*) AS order_count
FROM order
GROUP BY user_id
HAVING COUNT(*) > 5;  -- 订单数大于5的用户
```

### 时间窗口聚合
```sql
-- 按天统计
SELECT DATE(create_time) AS date, COUNT(*) AS count
FROM table_name
WHERE create_time >= DATE_SUB(NOW(), INTERVAL {days} DAY)
GROUP BY DATE(create_time)
ORDER BY date;

-- 按月统计
SELECT DATE_FORMAT(create_time, '%Y-%m') AS month, SUM(amount) AS total
FROM table_name
WHERE create_time >= DATE_SUB(NOW(), INTERVAL {months} MONTH)
GROUP BY DATE_FORMAT(create_time, '%Y-%m')
ORDER BY month;
```

---

## 条件过滤模板

### 基础条件
```sql
-- AND 条件
WHERE condition1 AND condition2 AND condition3

-- OR 条件
WHERE condition1 OR condition2 OR condition3

-- 混合条件(使用括号)
WHERE (condition1 AND condition2) OR (condition3 AND condition4)

-- NOT 条件
WHERE NOT condition

-- IN 条件
WHERE field IN ('value1', 'value2', 'value3')

-- NOT IN 条件
WHERE field NOT IN ('value1', 'value2')

-- BETWEEN 条件
WHERE field BETWEEN min_value AND max_value

-- LIKE 模糊查询
WHERE field LIKE '%keyword%'        -- 包含关键词
WHERE field LIKE 'keyword%'         -- 以关键词开头
WHERE field LIKE '%keyword'         -- 以关键词结尾
```

### NULL 值处理
```sql
-- IS NULL
WHERE field IS NULL

-- IS NOT NULL
WHERE field IS NOT NULL

-- NULL 转换
SELECT IFNULL(field, 0) AS value FROM table_name;
SELECT COALESCE(field1, field2, 0) AS value FROM table_name;
```

---

## 排序和分页模板

### 排序
```sql
-- 单字段升序
ORDER BY field ASC

-- 单字段降序
ORDER BY field DESC

-- 多字段排序
ORDER BY field1 ASC, field2 DESC

-- 聚合排序
ORDER BY COUNT(*) DESC
ORDER BY SUM(amount) DESC
```

### 分页
```sql
-- MySQL 分页
SELECT * FROM table_name
LIMIT {page_size} OFFSET {offset};

-- MySQL 简化分页
SELECT * FROM table_name
LIMIT {page_size} OFFSET ({page_num} - 1) * {page_size};

-- 获取分页总数
SELECT COUNT(*) AS total FROM table_name;
```

---

## 窗口函数模板

### ROW_NUMBER 排名
```sql
-- 按某字段排序并生成排名
SELECT field1, field2,
       ROW_NUMBER() OVER (ORDER BY field2 DESC) AS ranking
FROM table_name;

-- 分组内排名
SELECT user_id, amount,
       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY amount DESC) AS ranking
FROM table_name;
```

### LAG/LEAD 窗口函数
```sql
-- 获取前一行数据
SELECT field1,
       LAG(field1, 1) OVER (ORDER BY create_time) AS prev_value
FROM table_name;

-- 获取后一行数据
SELECT field1,
       LEAD(field1, 1) OVER (ORDER BY create_time) AS next_value
FROM table_name;
```

---

## CASE WHEN 模板

### 基础条件判断
```sql
-- 简单判断
SELECT
    field1,
    CASE
        WHEN amount > 1000 THEN '高'
        WHEN amount > 500 THEN '中'
        ELSE '低'
    END AS level
FROM table_name;

-- 多条件判断
SELECT
    field1,
    CASE
        WHEN status = 1 THEN '待支付'
        WHEN status = 2 THEN '已支付'
        WHEN status = 3 THEN '已完成'
        WHEN status = 4 THEN '已取消'
        ELSE '未知状态'
    END AS status_text
FROM table_name;
```

---

## UNION 合并查询

### UNION ALL (保留重复)
```sql
-- 合并两个查询结果(保留所有记录)
SELECT field1, field2 FROM table_a
UNION ALL
SELECT field1, field2 FROM table_b;
```

### UNION (去重)
```sql
-- 合并两个查询结果(去重)
SELECT field1, field2 FROM table_a
UNION
SELECT field1, field2 FROM table_b;
```

---

## 使用说明

### 模板占位符说明
- `{days}`: 天数,如: 7、30
- `{hours}`: 小时数,如: 24、48
- `{start_date}` / `{end_date}`: 日期,如: '2026-01-01'
- `{page_size}`: 每页记录数,如: 10、20
- `{offset}`: 偏移量,如: 0、20
- `{page_num}`: 页码,如: 1、2

### 组合使用
- 可以将多个模板组合使用
- 注意字段名称和表名称需要替换为实际名称
- 复杂查询建议分步验证

### 最佳实践
- 时间过滤使用索引字段
- 聚合统计注意 GROUP BY 字段完整性
- 多表关联使用清晰的表别名
- 大数据量查询使用 LIMIT 分页
