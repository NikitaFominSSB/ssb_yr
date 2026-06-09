"""Router for /locations."""

from fastapi import APIRouter, HTTPException, Request, status

from api import contracts
from domain.models import Location, NewLocation
from repositories import ForecastRepository, LocationRepository

router = APIRouter(prefix="/locations", tags=["locations"])


def _to_location(location: Location) -> contracts.Location:
    return contracts.Location(
        id=location.id, name=location.name, lat=location.lat, lon=location.lon
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_location(
    payload: contracts.CreateLocationRequest, request: Request
) -> contracts.CreateLocationResponse:
    locations: LocationRepository = request.app.state.locations
    location = await locations.add(
        NewLocation(name=payload.name, lat=payload.lat, lon=payload.lon)
    )
    return contracts.CreateLocationResponse(location=_to_location(location))


@router.get("")
async def list_locations(request: Request) -> contracts.GetLocationsResponse:
    locations: LocationRepository = request.app.state.locations
    items = await locations.list_all()
    return contracts.GetLocationsResponse(locations=[_to_location(loc) for loc in items])


@router.delete("/{location_id}")
async def delete_location(
    location_id: int, request: Request
) -> contracts.DeleteLocationsResponse:
    locations: LocationRepository = request.app.state.locations
    forecasts: ForecastRepository = request.app.state.forecasts
    # Er det et problem at vi ikke har transaksjonskontroll her?
    # Det er et sted hvor service lag ville hjelpe. Eller unit of work mønster.
    deleted = await locations.delete(location_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Lokasjon finnes ikke")
    await forecasts.delete_for_location(location_id)
    return contracts.DeleteLocationsResponse(location=_to_location(deleted))
