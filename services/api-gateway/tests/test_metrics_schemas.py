"""Tests for metrics schema validation.

Timestamps are stored naive-UTC in the database; clients send ISO strings
that Pydantic parses into timezone-aware datetimes. MetricsQuery must
normalize them to naive UTC — asyncpg rejects aware datetimes against
naive TIMESTAMP columns, which 500'd every historical metrics query.
"""

from datetime import datetime, timezone

from shared.schemas import MetricsQuery, to_naive_utc


def test_metrics_query_strips_utc_z_suffix():
    query = MetricsQuery(start_time="2026-10-10T00:00:00.000Z")

    assert query.start_time == datetime(2026, 10, 10, 0, 0)
    assert query.start_time.tzinfo is None


def test_metrics_query_converts_offset_to_utc_and_strips_it():
    query = MetricsQuery(start_time="2026-10-10T02:00:00+02:00")

    assert query.start_time == datetime(2026, 10, 10, 0, 0)
    assert query.start_time.tzinfo is None


def test_metrics_query_keeps_naive_values():
    query = MetricsQuery(start_time="2026-10-10T00:00:00")

    assert query.start_time == datetime(2026, 10, 10, 0, 0)
    assert query.start_time.tzinfo is None


def test_metrics_query_end_time_normalized():
    query = MetricsQuery(
        end_time=datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
    )

    assert query.end_time == datetime(2026, 10, 10, 12, 0)
    assert query.end_time.tzinfo is None


def test_to_naive_utc_handles_none():
    assert to_naive_utc(None) is None
