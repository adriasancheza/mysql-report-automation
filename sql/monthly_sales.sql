-- Sales aggregated by region and product for a date range.
-- Parameters: start_date, end_date (see reports.example.yml)
SELECT
    region,
    product,
    SUM(units) AS units,
    SUM(revenue) AS revenue,
    COUNT(*) AS orders
FROM orders
WHERE order_date BETWEEN :start_date AND :end_date
GROUP BY region, product
ORDER BY region, product;
