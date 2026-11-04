-- Monday=0, Sunday=6. These are descriptive associations, not causal effects.
SELECT c.weekday,
       COUNT(*) AS item_days,
       AVG(s.units) AS mean_units_per_item_day,
       SUM(CASE WHEN s.units = 0 THEN 1.0 ELSE 0 END) / COUNT(*) AS zero_sales_share
FROM fact_sales s
JOIN dim_date c ON c.sales_date = s.sales_date
GROUP BY c.weekday
ORDER BY c.weekday;
