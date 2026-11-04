-- Grain: one store, selected method, historical holdout only.
-- WAPE is a ratio of sums; averaging item percentages would distort it.
SELECT d.store_id,
       COUNT(DISTINCT s.series_id) AS series_count,
       SUM(s.units) AS actual_units,
       SUM(f.units) AS predicted_units,
       SUM(ABS(s.units - f.units)) / NULLIF(SUM(s.units), 0) AS wape,
       SUM(f.units - s.units) / NULLIF(SUM(s.units), 0) AS bias
FROM fact_sales s
JOIN dim_series d USING (series_id)
JOIN fact_forecast f ON f.series_id = s.series_id AND f.forecast_date = s.sales_date
WHERE f.period = 'holdout' AND f.forecast_kind = 'selected'
GROUP BY d.store_id
ORDER BY wape DESC, d.store_id;
