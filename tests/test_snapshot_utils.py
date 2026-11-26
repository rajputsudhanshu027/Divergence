from datetime import datetime, timedelta, timezone

from snapshot_utils import is_snapshot_stale, snapshot_age_days


def test_snapshot_age_threshold_is_explicit_and_utc_safe():
    now = datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc)
    at_threshold = (now - timedelta(days=45)).isoformat()
    past_threshold = (now - timedelta(days=46)).isoformat()

    assert snapshot_age_days(at_threshold, now) == 45
    assert not is_snapshot_stale(at_threshold, now)
    assert is_snapshot_stale(past_threshold, now)
    assert snapshot_age_days("invalid timestamp", now) is None
