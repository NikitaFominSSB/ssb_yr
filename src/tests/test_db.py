from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta

import asyncpg
import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer

from db import PostgresForecastRepository, PostgresLocationRepository, create_schema
from domain.models import Forecast, NewLocation

_NOW = datetime(2026, 6, 8, 12, 0, tzinfo=UTC)


def _forecast(location_id: int, minutes_ago: int = 0, temp: float = 18.0) -> Forecast:
    return Forecast(
        location_id=location_id,
        fetched_at=_NOW - timedelta(minutes=minutes_ago),
        air_temperature=temp,
    )


@pytest.fixture(scope="module")
def dsn() -> Iterator[str]:
    with PostgresContainer("postgres:16") as postgres:
        yield (
            f"postgresql://{postgres.username}:{postgres.password}"
            f"@{postgres.get_container_host_ip()}:{postgres.get_exposed_port(5432)}"
            f"/{postgres.dbname}"
        )


@pytest_asyncio.fixture
async def pool(dsn: str) -> AsyncIterator[asyncpg.Pool]:
    pool = await asyncpg.create_pool(dsn)
    assert pool is not None
    await create_schema(pool)
    # Tøm tabellene mellom tester og nullstill id-sekvensene.
    await pool.execute("TRUNCATE forecasts, locations RESTART IDENTITY CASCADE")
    yield pool
    await pool.close()


class TestPostgresLocationRepository:
    @pytest.mark.asyncio
    async def test_add_then_list(self, pool: asyncpg.Pool) -> None:
        repo = PostgresLocationRepository(pool)
        created = await repo.add(NewLocation("Oslo", 59.9, 10.7))
        assert created.id == 1
        assert [loc.name for loc in await repo.list_all()] == ["Oslo"]

    @pytest.mark.asyncio
    async def test_delete_returns_and_removes(self, pool: asyncpg.Pool) -> None:
        repo = PostgresLocationRepository(pool)
        created = await repo.add(NewLocation("Oslo", 59.9, 10.7))
        assert await repo.delete(created.id) == created
        assert await repo.list_all() == []

    @pytest.mark.asyncio
    async def test_delete_unknown_returns_none(self, pool: asyncpg.Pool) -> None:
        repo = PostgresLocationRepository(pool)
        assert await repo.delete(999) is None


class TestPostgresForecastRepository:
    @pytest.mark.asyncio
    async def test_list_all_newest_first_and_filter(self, pool: asyncpg.Pool) -> None:
        await PostgresLocationRepository(pool).add(NewLocation("Oslo", 59.9, 10.7))
        repo = PostgresForecastRepository(pool)
        await repo.add(_forecast(location_id=1, minutes_ago=10))
        await repo.add(_forecast(location_id=1, minutes_ago=0))

        all_loc1 = await repo.list_all(location_id=1)
        assert len(all_loc1) == 2
        assert all_loc1[0].fetched_at > all_loc1[1].fetched_at

    @pytest.mark.asyncio
    async def test_latest_per_location(self, pool: asyncpg.Pool) -> None:
        locations = PostgresLocationRepository(pool)
        await locations.add(NewLocation("Oslo", 59.9, 10.7))
        await locations.add(NewLocation("Bergen", 60.4, 5.3))
        repo = PostgresForecastRepository(pool)
        await repo.add(_forecast(location_id=1, minutes_ago=10))
        newest1 = await repo.add(_forecast(location_id=1, minutes_ago=0))
        newest2 = await repo.add(_forecast(location_id=2, minutes_ago=5))

        latest = await repo.latest_per_location()
        assert {f.location_id: f.id for f in latest} == {1: newest1.id, 2: newest2.id}

    @pytest.mark.asyncio
    async def test_delete_for_location(self, pool: asyncpg.Pool) -> None:
        locations = PostgresLocationRepository(pool)
        await locations.add(NewLocation("Oslo", 59.9, 10.7))
        await locations.add(NewLocation("Bergen", 60.4, 5.3))
        repo = PostgresForecastRepository(pool)
        await repo.add(_forecast(location_id=1))
        await repo.add(_forecast(location_id=2))

        await repo.delete_for_location(1)
        assert [f.location_id for f in await repo.list_all()] == [2]
