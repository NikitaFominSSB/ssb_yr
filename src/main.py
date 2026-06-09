from fastapi import FastAPI

from api import fetch, forecasts, locations
from repositories import InMemoryForecastRepository, InMemoryLocationRepository
from weather import FakeWeatherForecastClient


def create_app() -> FastAPI:
    app = FastAPI(title="ssb-yr", description="Værdata-innhenter")

    # Komposisjonsrot: konkrete implementasjoner kobles på her og leses via app.state.
    # Byttes ut med database-repositorier i et senere steg.
    # Ikke den beste løsningen, det er bedre å injisere via Depends
    app.state.locations = InMemoryLocationRepository()
    app.state.forecasts = InMemoryForecastRepository()
    app.state.weather = FakeWeatherForecastClient()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(locations.router)
    app.include_router(forecasts.router)
    app.include_router(fetch.router)
    return app


app = create_app()
