USE DATABASE SKIMS_DROP_INTELLIGENCE;
USE SCHEMA RAW;

SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM CUSTOMERS
UNION ALL SELECT 'products', COUNT(*) FROM PRODUCTS
UNION ALL SELECT 'orders', COUNT(*) FROM ORDERS
UNION ALL SELECT 'order_items', COUNT(*) FROM ORDER_ITEMS
UNION ALL SELECT 'waitlist_signups', COUNT(*) FROM WAITLIST_SIGNUPS
UNION ALL SELECT 'engagement_events', COUNT(*) FROM ENGAGEMENT_EVENTS
UNION ALL SELECT 'marketing_touches', COUNT(*) FROM MARKETING_TOUCHES;

-- customer tier distribution (60/30/10)
SELECT rewards_tier, COUNT(*) AS customers,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM CUSTOMERS
GROUP BY rewards_tier
ORDER BY customers DESC;

-- avg order per customer by tier (onyx >> others)
SELECT c.rewards_tier,
       COUNT(DISTINCT c.customer_id) AS customers,
       COUNT(o.order_id) AS total_orders,
       ROUND(COUNT(o.order_id) * 1.0 / COUNT(DISTINCT c.customer_id), 2) AS avg_orders_per_customer
FROM CUSTOMERS c
LEFT JOIN ORDERS o ON c.customer_id = o.customer_id
GROUP BY c.rewards_tier
ORDER BY avg_orders_per_customer DESC;

-- return rate by category (sculpt/ swim highest)
SELECT p.category,
       COUNT(oi.order_id) AS items_sold,
       SUM(CASE WHEN oi.returned_flag THEN 1 ELSE 0 END) AS items_returned,
       ROUND(100.0 * SUM(CASE WHEN oi.returned_flag THEN 1 ELSE 0 END) / COUNT(oi.order_id), 1) AS return_rate_pct
FROM ORDER_ITEMS oi
JOIN PRODUCTS p ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY return_rate_pct DESC;