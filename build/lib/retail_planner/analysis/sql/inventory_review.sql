-- Future stock needs and historical simulated costs have separate columns.
SELECT d.series_id, d.store_id, d.category,
       i.future_order_units, i.future_on_hand_assumed,
       i.holdout_actual_units, i.holdout_selected_cost, i.holdout_baseline_cost,
       i.holdout_baseline_cost - i.holdout_selected_cost AS simulated_cost_reduction
FROM fact_inventory i
JOIN dim_series d USING (series_id)
ORDER BY simulated_cost_reduction DESC, d.series_id;
