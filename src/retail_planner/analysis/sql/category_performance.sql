-- Compare the two methods on identical observed item-days.
SELECT d.category,
       COUNT(DISTINCT s.series_id) AS series_count,
       SUM(s.units) AS actual_units,
       SUM(ABS(s.units - f.units)) / NULLIF(SUM(s.units), 0) AS selected_wape,
       SUM(ABS(s.units - b.units)) / NULLIF(SUM(s.units), 0) AS baseline_wape,
       SUM(f.units - s.units) / NULLIF(SUM(s.units), 0) AS selected_bias
FROM fact_sales s
JOIN dim_series d USING (series_id)
JOIN fact_forecast f ON f.series_id = s.series_id AND f.forecast_date = s.sales_date
JOIN fact_forecast b ON b.series_id = s.series_id AND b.forecast_date = s.sales_date
WHERE f.period = 'holdout' AND f.forecast_kind = 'selected'
  AND b.period = 'holdout' AND b.forecast_kind = 'seasonal_28'
GROUP BY d.category
ORDER BY selected_wape DESC, d.category;
