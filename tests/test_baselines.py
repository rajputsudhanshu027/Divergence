import pytest

from retail_planner.forecasting.baselines import METHODS, forecast


@pytest.mark.parametrize("method", METHODS)
def test_baselines_return_nonnegative_horizon_without_future_data(method):
    history = tuple(float(index % 7 == 0) * 4 for index in range(84))
    predicted = forecast(history, 28, method)
    changed_future = history + (999.0,) * 28

    assert len(predicted) == 28
    assert all(value >= 0 for value in predicted)
    assert predicted == forecast(changed_future[:84], 28, method)


def test_moving_average_and_croston_are_distinct_statistical_baselines():
    history = (0.0,) * 20 + (8.0,) + (0.0,) * 20 + (4.0,) + (0.0,) * 42

    moving = forecast(history, 2, "moving_average_28")
    croston = forecast(history, 2, "croston")

    assert moving == [sum(history[-28:]) / 28] * 2
    assert croston[0] > 0
    assert croston != moving


def test_unknown_method_is_rejected():
    with pytest.raises(ValueError, match="Unknown method"):
        forecast((1.0,) * 60, 28, "oracle")
