"""
Pydantic request/response- odeller — HTTP-kontrakten.
Disse lever kun i API-grensesnittet: validering og (de)serialisering.
"""

from pydantic import BaseModel, Field


class Location(BaseModel):
    """En registrert lokasjon."""
    id: int
    name: str
    lat: float
    lon: float


class CreateLocationRequest(BaseModel):
    name: str = Field(min_length=1, examples=["Oslo"])
    lat: float = Field(ge=-90.0, le=90.0, examples=[59.9139])
    lon: float = Field(ge=-180.0, le=180.0, examples=[10.7522])


class CreateLocationResponse(BaseModel):
    location: Location


class GetLocationsResponse(BaseModel):
    locations: list[Location]


class DeleteLocationsResponse(BaseModel):
    location: Location


class Forecast(BaseModel):
    """Ett lagret værvarsel for en lokasjon."""
    id: int
    location_id: int
    stale: bool = Field(description="True hvis hentet for mer enn 60 minutter siden")
    air_temperature: float | None = Field(default=None, description="grader Celsius")


class GetForecastsRequest(BaseModel):
    location_id: int | None = None
    fresh: bool = False


class GetForecastResponse(BaseModel):
    forecast: Forecast


class GetForecastsResponse(BaseModel):
    forecasts: list[Forecast]


class FetchFailure(BaseModel):
    """En lokasjon der værvarselet ikke kunne hentes."""
    location_id: int
    name: str
    error: str


class FetchResponse(BaseModel):
    updated: int = Field(description="Antall lokasjoner som ble oppdatert")
    failed: int = Field(default=0, description="Antall lokasjoner som feilet")
    failures: list[FetchFailure] = Field(
        default_factory=list,
        description="Detaljer om feil",
    )
