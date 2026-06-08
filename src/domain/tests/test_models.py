from datetime import UTC, datetime, timedelta

import pytest

from domain.models import Forecast, NewLocation


def _forecast(fetched_at: datetime) -> Forecast:
    return Forecast(location_id=1, fetched_at=fetched_at, air_temperature=18.2)


def test_new_location_accepts_valid_input() -> None:
    loc = NewLocation(name="Oslo", lat=59.9139, lon=10.7522)
    assert loc.name == "Oslo"


@pytest.mark.parametrize(
    ("name", "lat", "lon"),
    [
        ("   ", 59.9, 10.7),
        ("Oslo", 90.1, 10.7),
        ("Oslo", -90.1, 10.7),
        ("Oslo", 59.9, 180.1),
        ("Oslo", 59.9, -180.1),
    ],
)
def test_new_location_rejects_invalid_input(name: str, lat: float, lon: float) -> None:
    with pytest.raises(ValueError):
        NewLocation(name=name, lat=lat, lon=lon)


def test_forecast_is_fresh_within_60_minutes() -> None:
    now = datetime(2026, 6, 8, 12, 0, tzinfo=UTC)
    forecast = _forecast(now - timedelta(minutes=59))
    assert forecast.is_stale(now) is False


def test_forecast_is_stale_after_60_minutes() -> None:
    now = datetime(2026, 6, 8, 12, 0, tzinfo=UTC)
    forecast = _forecast(now - timedelta(minutes=61))
    assert forecast.is_stale(now) is True


def test_forecast_at_exactly_60_minutes_is_not_stale() -> None:
    now = datetime(2026, 6, 8, 12, 0, tzinfo=UTC)
    forecast = _forecast(now - timedelta(minutes=60))
    assert forecast.is_stale(now) is False
