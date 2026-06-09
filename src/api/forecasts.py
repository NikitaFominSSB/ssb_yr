"""Router for /forecasts."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Query, Request

from api import contracts
from domain.models import Forecast
from repositories import ForecastRepository

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


def _to_forecast(forecast: Forecast, now: datetime) -> contracts.Forecast:
    assert forecast.id is not None, "lagrede varsler har alltid id"
    return contracts.Forecast(
        id=forecast.id,
        location_id=forecast.location_id,
        stale=forecast.is_stale(now),
        air_temperature=forecast.air_temperature,
    )


@router.get("")
async def list_forecasts(
    request: Request,
    query: Annotated[contracts.GetForecastsRequest, Query()],
) -> contracts.GetForecastsResponse:
    forecasts: ForecastRepository = request.app.state.forecasts
    now = datetime.now(UTC)
    items = await forecasts.list_all(query.location_id)
    if query.fresh:
        # Ferske varsler filtreres i applikasjonen i stedet for via en egen
        # list_fresh-spørring. Men det kan være bedre å ha det i repoet slik at
        # dababasen får ansvar for å sjekke om varslene er ferske.
        items = [f for f in items if not f.is_stale(now)]
    return contracts.GetForecastsResponse(forecasts=[_to_forecast(f, now) for f in items])


@router.get("/latest")
async def latest_forecasts(request: Request) -> contracts.GetForecastsResponse:
    """Nyeste lagrede varsel per lokasjon."""
    forecasts: ForecastRepository = request.app.state.forecasts
    now = datetime.now(UTC)
    items = await forecasts.latest_per_location()
    return contracts.GetForecastsResponse(forecasts=[_to_forecast(f, now) for f in items])


@router.get("/{location_id}/history")
async def forecast_history(
    location_id: int, request: Request
) -> contracts.GetForecastsResponse:
    forecasts: ForecastRepository = request.app.state.forecasts
    now = datetime.now(UTC)
    items = await forecasts.list_all(location_id)
    return contracts.GetForecastsResponse(forecasts=[_to_forecast(f, now) for f in items])
