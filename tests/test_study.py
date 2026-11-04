import tempfile
import unittest
from pathlib import Path

from retail_planner.data.m5 import Dataset, Series, load_m5, write_demo
from retail_planner.evaluation.study import run_study
from retail_planner.forecasting.baselines import METHODS, forecast


class ForecastSafetyTests(unittest.TestCase):
    def test_forecasts_cannot_see_future_values(self):
        past = tuple(float(index % 11) for index in range(90))
        future_a = past + (0.0,) * 28
        future_b = past + (999.0,) * 28
        for method in METHODS:
            self.assertEqual(forecast(future_a[:90], 28, method),
                             forecast(future_b[:90], 28, method))

    def test_holdout_does_not_select_model_or_calibrate_interval(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            write_demo(path)
            original = load_m5(path)
            changed_series = tuple(
                Series(item.id, item.item_id, item.dept_id, item.cat_id, item.store_id,
                       item.state_id, item.sales[:-28] + (999.0,) * 28)
                for item in original.series
            )
            altered = Dataset(changed_series, original.dates, original.weeks,
                              original.prices, original.source)
            first = run_study(original)
            second = run_study(altered)
            self.assertEqual(first["selected_method"], second["selected_method"])
            self.assertEqual(first["validation"], second["validation"])
            self.assertNotEqual(first["holdout"]["selected"], second["holdout"]["selected"])

    def test_demo_has_expected_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            write_demo(path)
            data = load_m5(path)
            result = run_study(data)
            self.assertEqual(len(data.series), 24)
            self.assertEqual(len(result["validation_starts"]), 3)
            self.assertEqual(len(result["forecast_dates"]), 28)
            self.assertEqual(result["holdout"]["selected"]["levels_scored"], 12)


if __name__ == "__main__":
    unittest.main()
