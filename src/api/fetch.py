"""Router for /fetch."""

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Request

from api import contracts
from domain.models import Forecast, Location
from repositories import ForecastRepository, LocationRepository
from weather import WeatherForecastClient

router = APIRouter(tags=["fetch"])


@router.post("/fetch")
async def fetch_forecasts(request: Request) -> contracts.FetchResponse:
    """Henter værvarsler for alle lokasjoner."""
    locations: LocationRepository = request.app.state.locations
    forecasts: ForecastRepository = request.app.state.forecasts
    weather: WeatherForecastClient = request.app.state.weather

    registered = await locations.list_all()
    results = await asyncio.gather(
        *(weather.fetch_temperature(loc.lat, loc.lon) for loc in registered),
        return_exceptions=True,
    )

    now = datetime.now(UTC)
    updated = 0
    failures: list[contracts.FetchFailure] = []
    for location, result in zip(registered, results, strict=True):
        if isinstance(result, BaseException):
            failures.append(_to_failure(location, result))
            continue
        await forecasts.add(
            Forecast(location_id=location.id, fetched_at=now, air_temperature=result)
        )
        updated += 1
    return contracts.FetchResponse(
        updated=updated, failed=len(failures), failures=failures
    )


def _to_failure(location: Location, error: BaseException) -> contracts.FetchFailure:
    return contracts.FetchFailure(
        location_id=location.id, name=location.name, error=str(error)
    )
