-- ============================================================
-- OLIST E-COMMERCE ANALYSIS (SQLite)
-- Definitions used everywhere:
--   * Only orders with order_status = 'delivered' are analysed.
--   * Revenue = sum of item price (freight/shipping is NOT included).
--   * A late order = delivered after the estimated delivery date.
-- Each query starts with a "-- name:" line so run_queries.py can run them all.
-- ============================================================

-- name: q1_monthly_revenue_growth
-- Business question: How is revenue changing month to month?
-- Techniques: JOIN, GROUP BY, CTE, LAG() window function
WITH monthly AS (
    SELECT o.order_month,
           ROUND(SUM(i.price), 2)        AS revenue,
           COUNT(DISTINCT o.order_id)    AS orders
    FROM orders o
    JOIN order_items i ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY o.order_month
)
SELECT order_month, revenue, orders,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY order_month))
             / LAG(revenue) OVER (ORDER BY order_month), 1) AS mom_growth_pct
FROM monthly
ORDER BY order_month;

-- name: q2_top_categories
-- Business question: Which product categories earn the most, and how concentrated is revenue?
-- Techniques: JOIN, LEFT JOIN, CTE, SUM() OVER (share and cumulative share), RANK()
WITH cat AS (
    SELECT COALESCE(p.category_english, 'unknown') AS category,
           SUM(i.price)                            AS revenue,
           COUNT(DISTINCT o.order_id)              AS orders
    FROM orders o
    JOIN order_items i   ON i.order_id = o.order_id
    LEFT JOIN products p ON p.product_id = i.product_id
    WHERE o.order_status = 'delivered'
    GROUP BY category
)
SELECT RANK() OVER (ORDER BY revenue DESC)                                    AS rank,
       category,
       ROUND(revenue, 2)                                                      AS revenue,
       orders,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 1)                       AS share_pct,
       ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC)
             / SUM(revenue) OVER (), 1)                                       AS cumulative_share_pct
FROM cat
ORDER BY revenue DESC
LIMIT 10;

-- name: q3_late_delivery_vs_reviews
-- Business question: Does late delivery hurt customer satisfaction?
-- Techniques: JOIN, CTE, CASE, GROUP BY, AVG
WITH delivered AS (
    SELECT o.order_id, o.is_late, r.review_score
    FROM orders o
    JOIN reviews r ON r.order_id = o.order_id
    WHERE o.order_status = 'delivered' AND o.is_late IS NOT NULL
)
SELECT CASE WHEN is_late = 1 THEN 'Late' ELSE 'On time' END AS delivery,
       COUNT(*)                                             AS orders,
       ROUND(AVG(review_score), 2)                          AS avg_review_score,
       ROUND(100.0 * SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_low_reviews
FROM delivered
GROUP BY is_late
ORDER BY is_late;

-- name: q4_payment_methods
-- Business question: How do customers pay?
-- Techniques: JOIN, GROUP BY, SUM() OVER () for share
SELECT p.payment_type,
       COUNT(DISTINCT p.order_id)                                   AS orders,
       ROUND(SUM(p.payment_value), 2)                               AS total_paid,
       ROUND(100.0 * COUNT(DISTINCT p.order_id)
             / SUM(COUNT(DISTINCT p.order_id)) OVER (), 1)          AS pct_of_orders
FROM payments p
JOIN orders o ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY p.payment_type
ORDER BY orders DESC;

-- name: q5_revenue_by_state
-- Business question: Which regions drive revenue, and is it concentrated?
-- Techniques: 3-table JOIN, GROUP BY, RANK(), share of total
SELECT RANK() OVER (ORDER BY SUM(i.price) DESC)               AS rank,
       c.customer_state                                       AS state,
       ROUND(SUM(i.price), 2)                                 AS revenue,
       COUNT(DISTINCT o.order_id)                             AS orders,
       ROUND(100.0 * SUM(i.price) / SUM(SUM(i.price)) OVER (), 1) AS share_pct
FROM orders o
JOIN customers c   ON c.customer_id = o.customer_id
JOIN order_items i ON i.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY revenue DESC
LIMIT 10;

-- name: q6_repeat_customers
-- Business question: What share of customers buy more than once?
-- Note: customer_id changes on every order; customer_unique_id identifies the real person.
-- Techniques: JOIN, CTE, CASE, conditional aggregation
WITH cust AS (
    SELECT c.customer_unique_id, COUNT(DISTINCT o.order_id) AS n_orders
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT COUNT(*)                                                         AS customers,
       SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END)                    AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_rate_pct
FROM cust;

-- name: q7_running_revenue_by_year
-- Business question: How does cumulative revenue build up within each year?
-- Techniques: CTE, SUM() OVER (PARTITION BY ... ORDER BY ...)
WITH m AS (
    SELECT SUBSTR(o.order_month, 1, 4) AS year,
           o.order_month,
           SUM(i.price)                AS revenue
    FROM orders o
    JOIN order_items i ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY o.order_month
)
SELECT year, order_month,
       ROUND(revenue, 2) AS revenue,
       ROUND(SUM(revenue) OVER (PARTITION BY year ORDER BY order_month), 2) AS year_to_date_revenue
FROM m
ORDER BY order_month;

-- name: q8_top3_categories_per_year
-- Business question: Do the best-selling categories change from year to year?
-- Techniques: 2 CTEs, RANK() OVER (PARTITION BY ...)
WITH yearly AS (
    SELECT SUBSTR(o.order_month, 1, 4)         AS year,
           COALESCE(p.category_english, 'unknown') AS category,
           SUM(i.price)                        AS revenue
    FROM orders o
    JOIN order_items i   ON i.order_id = o.order_id
    LEFT JOIN products p ON p.product_id = i.product_id
    WHERE o.order_status = 'delivered'
    GROUP BY year, category
),
ranked AS (
    SELECT year, category, ROUND(revenue, 2) AS revenue,
           RANK() OVER (PARTITION BY year ORDER BY revenue DESC) AS rank_in_year
    FROM yearly
)
SELECT * FROM ranked
WHERE rank_in_year <= 3
ORDER BY year, rank_in_year;
