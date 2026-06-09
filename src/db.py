"""
PostgreSQL-lagring med asyncpg og rå SQL.

Repository-implementasjoner som arver de abstrakte baseklassene i repositories.py.
"""

import asyncpg

from domain.models import Forecast, Location, NewLocation
from repositories import ForecastRepository, LocationRepository

_SCHEMA = """
CREATE TABLE IF NOT EXISTS locations (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    lat  DOUBLE PRECISION NOT NULL,
    lon  DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS forecasts (
    id              SERIAL PRIMARY KEY,
    location_id     INTEGER NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL,
    air_temperature DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_forecasts_location ON forecasts(location_id);
"""


def _to_location(row: asyncpg.Record) -> Location:
    return Location(id=row["id"], name=row["name"], lat=row["lat"], lon=row["lon"])


def _to_forecast(row: asyncpg.Record) -> Forecast:
    return Forecast(
        id=row["id"],
        location_id=row["location_id"],
        fetched_at=row["fetched_at"],
        air_temperature=row["air_temperature"],
    )


async def create_schema(pool: asyncpg.Pool) -> None:
    await pool.execute(_SCHEMA)


class PostgresLocationRepository(LocationRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def add(self, new: NewLocation) -> Location:
        row = await self._pool.fetchrow(
            "INSERT INTO locations (name, lat, lon) VALUES ($1, $2, $3) "
            "RETURNING id, name, lat, lon",
            new.name,
            new.lat,
            new.lon,
        )
        return _to_location(row)

    async def list_all(self) -> list[Location]:
        rows = await self._pool.fetch("SELECT id, name, lat, lon FROM locations ORDER BY id")
        return [_to_location(row) for row in rows]

    async def delete(self, location_id: int) -> Location | None:
        row = await self._pool.fetchrow(
            "DELETE FROM locations WHERE id = $1 RETURNING id, name, lat, lon",
            location_id,
        )
        return _to_location(row) if row is not None else None


class PostgresForecastRepository(ForecastRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def add(self, forecast: Forecast) -> Forecast:
        row = await self._pool.fetchrow(
            "INSERT INTO forecasts (location_id, fetched_at, air_temperature) "
            "VALUES ($1, $2, $3) RETURNING id, location_id, fetched_at, air_temperature",
            forecast.location_id,
            forecast.fetched_at,
            forecast.air_temperature,
        )
        return _to_forecast(row)

    async def list_all(self, location_id: int | None = None) -> list[Forecast]:
        if location_id is None:
            rows = await self._pool.fetch(
                "SELECT id, location_id, fetched_at, air_temperature FROM forecasts "
                "ORDER BY fetched_at DESC"
            )
        else:
            rows = await self._pool.fetch(
                "SELECT id, location_id, fetched_at, air_temperature FROM forecasts "
                "WHERE location_id = $1 ORDER BY fetched_at DESC",
                location_id,
            )
        return [_to_forecast(row) for row in rows]

    async def latest_per_location(self) -> list[Forecast]:
        rows = await self._pool.fetch(
            "SELECT DISTINCT ON (location_id) "
            "id, location_id, fetched_at, air_temperature FROM forecasts "
            "ORDER BY location_id, fetched_at DESC"
        )
        return [_to_forecast(row) for row in rows]

    async def delete_for_location(self, location_id: int) -> None:
        await self._pool.execute("DELETE FROM forecasts WHERE location_id = $1", location_id)
