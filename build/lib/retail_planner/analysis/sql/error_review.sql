-- Large absolute errors identify review candidates; they do not prove a root cause.
SELECT s.series_id, d.store_id, d.category,
       SUM(s.units) AS actual_units,
       SUM(f.units) AS predicted_units,
       SUM(ABS(s.units - f.units)) AS absolute_error_units,
       SUM(f.units - s.units) AS signed_error_units,
       SUM(ABS(s.units - f.units)) / NULLIF(SUM(s.units), 0) AS wape
FROM fact_sales s
JOIN dim_series d USING (series_id)
JOIN fact_forecast f ON f.series_id = s.series_id AND f.forecast_date = s.sales_date
WHERE f.period = 'holdout' AND f.forecast_kind = 'selected'
GROUP BY s.series_id, d.store_id, d.category
ORDER BY absolute_error_units DESC, s.series_id;
