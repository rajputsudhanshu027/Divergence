"""Snapshot freshness helpers shared by the app and its verification tests."""

from __future__ import annotations

from datetime import datetime, timezone


SNAPSHOT_STALE_AFTER_DAYS = 45


def snapshot_age_days(retrieved_at: str | None, now: datetime | None = None) -> int | None:
    """Return non-negative whole days since retrieval, or None for invalid metadata."""
    if not retrieved_at:
        return None
    try:
        retrieved = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        return None
    if retrieved.tzinfo is None:
        retrieved = retrieved.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age = int((current.astimezone(timezone.utc) - retrieved.astimezone(timezone.utc)).total_seconds() // 86400)
    return max(0, age)


def is_snapshot_stale(retrieved_at: str | None, now: datetime | None = None) -> bool:
    age = snapshot_age_days(retrieved_at, now)
    return age is not None and age > SNAPSHOT_STALE_AFTER_DAYS
