"""
Domenemodeller.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

# Et varsel regnes som utdatert når det er eldre enn dette.
STALE_AFTER = timedelta(minutes=60)


@dataclass(frozen=True)
class NewLocation:
    """En lokasjon som skal registreres (uten id ennå)."""
    name: str
    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("navn kan ikke være tomt")
        if not -90.0 <= self.lat <= 90.0:
            raise ValueError("breddegrad må være mellom -90 og 90")
        if not -180.0 <= self.lon <= 180.0:
            raise ValueError("lengdegrad må være mellom -180 og 180")


@dataclass(frozen=True)
class Location:
    """En registrert lokasjon."""
    id: int
    name: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Forecast:
    """Ett værvarsel hentet for en lokasjon."""
    location_id: int
    fetched_at: datetime
    air_temperature: float | None
    id: int | None = None

    def is_stale(self, now: datetime) -> bool:
        """Sant hvis varselet ble hentet for mer enn STALE_AFTER minutter siden."""
        return now - self.fetched_at > STALE_AFTER
