import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

from api import fetch, forecasts, locations
from db import PostgresForecastRepository, PostgresLocationRepository, create_schema
from repositories import InMemoryForecastRepository, InMemoryLocationRepository
from weather import YrWeatherForecastClient

# Yr krever User-Agent med kontaktinformasjon. Overstyres via miljøvariabel.
_DEFAULT_USER_AGENT = "ssb-yr/1.0 nikita.s.fomin@gmail.com"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Bruk Postgres når DATABASE_URL er satt, ellers in-memory (lokal kjøring/tester).
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        pool = await asyncpg.create_pool(database_url)
        await create_schema(pool)
        app.state.locations = PostgresLocationRepository(pool)
        app.state.forecasts = PostgresForecastRepository(pool)
        try:
            yield
        finally:
            await pool.close()
    else:
        app.state.locations = InMemoryLocationRepository()
        app.state.forecasts = InMemoryForecastRepository()
        yield


def create_app() -> FastAPI:
    app = FastAPI(title="ssb-yr", description="Værdata-innhenter", lifespan=lifespan)

    # Komposisjonsrot: konkrete implementasjoner leses via app.state. Repositoriene settes
    # i lifespan; værklienten er uavhengig av lagring og settes her.
    app.state.weather = YrWeatherForecastClient(
        user_agent=os.environ.get("YR_USER_AGENT", _DEFAULT_USER_AGENT)
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(locations.router)
    app.include_router(forecasts.router)
    app.include_router(fetch.router)
    return app


app = create_app()
