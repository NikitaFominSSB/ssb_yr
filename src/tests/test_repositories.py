from datetime import UTC, datetime, timedelta

import pytest

from domain.models import Forecast, NewLocation
from repositories import InMemoryForecastRepository, InMemoryLocationRepository

_NOW = datetime(2026, 6, 8, 12, 0, tzinfo=UTC)


def _forecast(location_id: int, minutes_ago: int = 0, temp: float = 18.0) -> Forecast:
    return Forecast(
        location_id=location_id,
        fetched_at=_NOW - timedelta(minutes=minutes_ago),
        air_temperature=temp,
    )


class TestInMemoryLocationRepository:
    @pytest.mark.asyncio
    async def test_add_assigns_incrementing_ids(self) -> None:
        repo = InMemoryLocationRepository()
        a = await repo.add(NewLocation("Oslo", 59.9, 10.7))
        b = await repo.add(NewLocation("Bergen", 60.4, 5.3))
        assert (a.id, b.id) == (1, 2)


    @pytest.mark.asyncio
    async def test_list_all_locations_returns_added(self) -> None:
        repo = InMemoryLocationRepository()
        await repo.add(NewLocation("Oslo", 59.9, 10.7))
        assert [loc.name for loc in await repo.list_all()] == ["Oslo"]


    @pytest.mark.asyncio
    async def test_delete_location_removes_and_returns_it(self) -> None:
        repo = InMemoryLocationRepository()
        loc = await repo.add(NewLocation("Oslo", 59.9, 10.7))
        assert await repo.delete(loc.id) == loc
        assert await repo.list_all() == []


    @pytest.mark.asyncio
    async def test_delete_unknown_location_returns_none(self) -> None:
        repo = InMemoryLocationRepository()
        assert await repo.delete(999) is None


class TestInMemoryForecastRepository:
    @pytest.mark.asyncio
    async def test_add_forecast_assigns_id(self) -> None:
        repo = InMemoryForecastRepository()
        stored = await repo.add(_forecast(location_id=1))
        assert stored.id == 1


    @pytest.mark.asyncio
    async def test_list_all_forecasts_newest_first(self) -> None:
        repo = InMemoryForecastRepository()
        await repo.add(_forecast(location_id=1, minutes_ago=0))
        await repo.add(_forecast(location_id=1, minutes_ago=10))
        items = await repo.list_all()
        assert items[0].fetched_at > items[1].fetched_at


    @pytest.mark.asyncio
    async def test_list_all_forecasts_filters_by_location(self) -> None:
        repo = InMemoryForecastRepository()
        await repo.add(_forecast(location_id=1))
        await repo.add(_forecast(location_id=2))
        assert [f.location_id for f in await repo.list_all(location_id=1)] == [1]


    @pytest.mark.asyncio
    async def test_latest_per_location_returns_newest_for_each(self) -> None:
        repo = InMemoryForecastRepository()
        await repo.add(_forecast(location_id=1, minutes_ago=10))
        newest_loc1 = await repo.add(_forecast(location_id=1, minutes_ago=0))
        newest_loc2 = await repo.add(_forecast(location_id=2, minutes_ago=5))
        latest = await repo.latest_per_location()
        by_location = {f.location_id: f.id for f in latest}
        assert by_location == {1: newest_loc1.id, 2: newest_loc2.id}


    @pytest.mark.asyncio
    async def test_latest_per_location_is_empty_when_no_forecasts(self) -> None:
        repo = InMemoryForecastRepository()
        assert await repo.latest_per_location() == []


    @pytest.mark.asyncio
    async def test_delete_for_location_only_removes_that_location(self) -> None:
        repo = InMemoryForecastRepository()
        await repo.add(_forecast(location_id=1))
        await repo.add(_forecast(location_id=2))
        await repo.delete_for_location(1)
        assert [f.location_id for f in await repo.list_all()] == [2]
