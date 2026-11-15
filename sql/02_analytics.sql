-- =====================================================================
-- Elektron ticarət — analitik SQL sorğuları
-- Hər sorğu "-- name: <ad>" sətri ilə başlayır (Python bu adlarla oxuyur).
-- Gəlir hesablamalarında yalnız çatdırılmış (delivered) sifarişlər nəzərə alınır.
-- =====================================================================


-- name: q01_category_revenue
-- [JOIN + GROUP BY] Kateqoriyalar üzrə satış həcmi, gəlir və gəlirdəki pay
SELECT c.category_name,
       COUNT(DISTINCT o.order_id)                       AS orders_count,
       SUM(oi.quantity)                                 AS units_sold,
       ROUND(SUM(oi.line_total), 2)                     AS revenue,
       ROUND(100.0 * SUM(oi.line_total)
             / SUM(SUM(oi.line_total)) OVER (), 2)      AS revenue_share_pct
FROM order_items oi
JOIN orders     o ON o.order_id    = oi.order_id
JOIN products   p ON p.product_id  = oi.product_id
JOIN categories c ON c.category_id = p.category_id
WHERE o.status = 'delivered'
GROUP BY c.category_name
ORDER BY revenue DESC;


-- name: q02_monthly_revenue
-- [GROUP BY + tarix funksiyaları] Aylıq gəlir, sifariş sayı və orta çek
SELECT DATE_TRUNC('month', o.order_date)::date AS month,
       COUNT(*)                                AS orders_count,
       ROUND(SUM(o.total_amount), 2)           AS revenue,
       ROUND(AVG(o.total_amount), 2)           AS avg_order_value
FROM orders o
WHERE o.status = 'delivered'
GROUP BY 1
ORDER BY 1;


-- name: q03_loyal_customers_having
-- [JOIN + GROUP BY + HAVING] 8-dən çox çatdırılmış sifarişi və 3000 AZN-dən çox xərci olan müştərilər
SELECT cu.customer_id,
       cu.first_name || ' ' || cu.last_name AS customer_name,
       cu.city,
       COUNT(o.order_id)                    AS orders_count,
       ROUND(SUM(o.total_amount), 2)        AS total_spent,
       ROUND(AVG(o.total_amount), 2)        AS avg_order_value
FROM customers cu
JOIN orders o ON o.customer_id = cu.customer_id
WHERE o.status = 'delivered'
GROUP BY cu.customer_id, customer_name, cu.city
HAVING COUNT(o.order_id) > 8
   AND SUM(o.total_amount) > 3000
ORDER BY total_spent DESC;


-- name: q04_city_payment_having
-- [JOIN + GROUP BY + HAVING] Şəhər və ödəniş üsulu üzrə — 50-dən çox uğurlu ödəniş olan kombinasiyalar
SELECT o.shipping_city,
       p.payment_method,
       COUNT(*)                   AS payments_count,
       ROUND(SUM(p.amount), 2)    AS total_amount
FROM payments p
JOIN orders o ON o.order_id = p.order_id
WHERE p.payment_status = 'completed'
GROUP BY o.shipping_city, p.payment_method
HAVING COUNT(*) > 50
ORDER BY o.shipping_city, total_amount DESC;


-- name: q05_top_customers_cte
-- [CTE] Müştəri seqmentasiyası (RFM-ə bənzər): son alış, tezlik və pul dəyəri
WITH customer_stats AS (
    SELECT o.customer_id,
           MAX(o.order_date)        AS last_order,
           COUNT(*)                 AS frequency,
           SUM(o.total_amount)      AS monetary
    FROM orders o
    WHERE o.status = 'delivered'
    GROUP BY o.customer_id
),
scored AS (
    SELECT cs.*,
           NTILE(4) OVER (ORDER BY last_order, customer_id) AS r_score,
           NTILE(4) OVER (ORDER BY frequency, customer_id)  AS f_score,
           NTILE(4) OVER (ORDER BY monetary, customer_id)   AS m_score
    FROM customer_stats cs
),
segmented AS (
    SELECT *,
           CASE
               WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'VIP'
               WHEN r_score >= 3 AND f_score >= 2                  THEN 'Sadiq'
               WHEN r_score <= 2 AND m_score >= 3                  THEN 'Risk altında'
               WHEN r_score >= 3                                   THEN 'Yeni / aktiv'
               ELSE 'Passiv'
           END AS segment
    FROM scored
)
SELECT segment,
       COUNT(*)                             AS customers,
       ROUND(AVG(frequency), 2)             AS avg_orders,
       ROUND(AVG(monetary), 2)              AS avg_spent,
       ROUND(SUM(monetary), 2)              AS total_revenue,
       ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 2) AS revenue_share_pct
FROM segmented
GROUP BY segment
ORDER BY total_revenue DESC;


-- name: q06_products_above_category_avg
-- [Korrelyasiyalı Subquery] Öz kateqoriyasının orta qiymətindən baha olan və ən azı 20 dəfə satılan məhsullar
SELECT p.product_id,
       p.product_name,
       c.category_name,
       p.unit_price,
       (SELECT ROUND(AVG(p2.unit_price), 2)
          FROM products p2
         WHERE p2.category_id = p.category_id)              AS category_avg_price,
       (SELECT SUM(oi.quantity)
          FROM order_items oi
         WHERE oi.product_id = p.product_id)                AS units_sold
FROM products p
JOIN categories c ON c.category_id = p.category_id
WHERE p.unit_price > (SELECT AVG(p2.unit_price)
                        FROM products p2
                       WHERE p2.category_id = p.category_id)
  AND (SELECT SUM(oi.quantity) FROM order_items oi WHERE oi.product_id = p.product_id) >= 20
ORDER BY units_sold DESC
LIMIT 20;


-- name: q07_customers_above_avg_subquery
-- [Subquery IN / skalyar] Orta müştəri xərcindən 3 dəfə çox xərcləyən müştərilərin şəhər üzrə sayı
SELECT cu.city,
       COUNT(*) AS high_value_customers
FROM customers cu
WHERE cu.customer_id IN (
        SELECT o.customer_id
          FROM orders o
         WHERE o.status = 'delivered'
         GROUP BY o.customer_id
        HAVING SUM(o.total_amount) > 3 * (
                 SELECT AVG(t.spent)
                   FROM (SELECT SUM(total_amount) AS spent
                           FROM orders
                          WHERE status = 'delivered'
                          GROUP BY customer_id) t)
      )
GROUP BY cu.city
ORDER BY high_value_customers DESC, cu.city;


-- name: q08_yoy_growth_cte
-- [CTE + LAG] Kateqoriyalar üzrə illik gəlir və illik artım (YoY) faizi
WITH yearly AS (
    SELECT c.category_name,
           EXTRACT(YEAR FROM o.order_date)::int AS year,
           SUM(oi.line_total)                   AS revenue
    FROM order_items oi
    JOIN orders     o ON o.order_id    = oi.order_id
    JOIN products   p ON p.product_id  = oi.product_id
    JOIN categories c ON c.category_id = p.category_id
    WHERE o.status = 'delivered'
    GROUP BY c.category_name, year
)
SELECT category_name,
       year,
       ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER w) / LAG(revenue) OVER w, 2) AS yoy_growth_pct
FROM yearly
WINDOW w AS (PARTITION BY category_name ORDER BY year)
ORDER BY category_name, year;


-- name: q09_payment_methods
-- [JOIN + GROUP BY] Ödəniş üsulları üzrə uğur, uğursuzluq və geri qaytarma göstəriciləri
SELECT p.payment_method,
       COUNT(*)                                                         AS total_payments,
       COUNT(*) FILTER (WHERE p.payment_status = 'completed')           AS completed,
       COUNT(*) FILTER (WHERE p.payment_status = 'failed')              AS failed,
       COUNT(*) FILTER (WHERE p.payment_status = 'refunded')            AS refunded,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p.payment_status = 'completed') / COUNT(*), 2)
                                                                        AS success_rate_pct,
       ROUND(AVG(p.amount), 2)                                          AS avg_amount
FROM payments p
GROUP BY p.payment_method
ORDER BY total_payments DESC;


-- name: q10_top_products_per_category
-- [CTE + ROW_NUMBER] Hər kateqoriyada gəlirə görə ilk 3 məhsul
WITH product_revenue AS (
    SELECT c.category_name,
           p.product_name,
           p.brand,
           SUM(oi.quantity)   AS units_sold,
           SUM(oi.line_total) AS revenue
    FROM order_items oi
    JOIN orders     o ON o.order_id    = oi.order_id
    JOIN products   p ON p.product_id  = oi.product_id
    JOIN categories c ON c.category_id = p.category_id
    WHERE o.status = 'delivered'
    GROUP BY c.category_name, p.product_name, p.brand
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY category_name ORDER BY revenue DESC) AS rn
    FROM product_revenue
)
SELECT category_name, rn AS rank, product_name, brand, units_sold, ROUND(revenue, 2) AS revenue
FROM ranked
WHERE rn <= 3
ORDER BY category_name, rn;


-- name: q11_cancellation_by_category
-- [LEFT JOIN + GROUP BY + HAVING + Subquery] Ləğv/geri qaytarma nisbəti ümumi orta nisbətdən yüksək olan kateqoriyalar
SELECT c.category_name,
       COUNT(DISTINCT o.order_id)                                                AS orders_count,
       COUNT(DISTINCT o.order_id) FILTER (WHERE o.status IN ('cancelled','returned')) AS lost_orders,
       ROUND(100.0 * COUNT(DISTINCT o.order_id) FILTER (WHERE o.status IN ('cancelled','returned'))
             / COUNT(DISTINCT o.order_id), 2)                                    AS lost_rate_pct,
       (SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE status IN ('cancelled','returned'))
                     / COUNT(*), 2) FROM orders)                                 AS overall_rate_pct
FROM categories c
LEFT JOIN products    p  ON p.category_id = c.category_id
LEFT JOIN order_items oi ON oi.product_id = p.product_id
LEFT JOIN orders      o  ON o.order_id    = oi.order_id
GROUP BY c.category_name
HAVING 100.0 * COUNT(DISTINCT o.order_id) FILTER (WHERE o.status IN ('cancelled','returned'))
       / NULLIF(COUNT(DISTINCT o.order_id), 0)
       > (SELECT 100.0 * COUNT(*) FILTER (WHERE status IN ('cancelled','returned')) / COUNT(*)
            FROM orders)
ORDER BY lost_rate_pct DESC;


-- name: q12_age_group_analysis
-- [CTE + CASE] Yaş qrupları və cins üzrə alış davranışı
WITH customer_age AS (
    SELECT customer_id,
           gender,
           CASE
               WHEN DATE_PART('year', AGE(DATE '2025-12-31', birth_date)) < 25 THEN '18-24'
               WHEN DATE_PART('year', AGE(DATE '2025-12-31', birth_date)) < 35 THEN '25-34'
               WHEN DATE_PART('year', AGE(DATE '2025-12-31', birth_date)) < 45 THEN '35-44'
               WHEN DATE_PART('year', AGE(DATE '2025-12-31', birth_date)) < 55 THEN '45-54'
               ELSE '55+'
           END AS age_group
    FROM customers
)
SELECT ca.age_group,
       ca.gender,
       COUNT(DISTINCT ca.customer_id)  AS customers,
       COUNT(o.order_id)               AS orders_count,
       ROUND(AVG(o.total_amount), 2)   AS avg_order_value,
       ROUND(SUM(o.total_amount), 2)   AS revenue
FROM customer_age ca
JOIN orders o ON o.customer_id = ca.customer_id AND o.status = 'delivered'
GROUP BY ca.age_group, ca.gender
ORDER BY ca.age_group, ca.gender;
