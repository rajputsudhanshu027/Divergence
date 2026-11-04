-- LAG compares complete weeks only. Removing partial boundary weeks avoids a false trend.
WITH weekly AS (
    SELECT d.store_id, c.week_start,
           COUNT(DISTINCT c.sales_date) AS days_observed,
           SUM(s.units) AS units
    FROM fact_sales s
    JOIN dim_series d USING (series_id)
    JOIN dim_date c ON c.sales_date = s.sales_date
    GROUP BY d.store_id, c.week_start
    HAVING COUNT(DISTINCT c.sales_date) = 7
), changes AS (
    SELECT *, LAG(units) OVER (PARTITION BY store_id ORDER BY week_start) AS previous_week_units
    FROM weekly
)
SELECT *, (units - previous_week_units) / NULLIF(previous_week_units, 0) AS wow_change
FROM changes
ORDER BY store_id, week_start;
