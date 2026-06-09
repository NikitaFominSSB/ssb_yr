"""
Repositorier.
De abstrakte klassene definerer kontrakten routerne avhenger av.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import replace

from domain.models import Forecast, Location, NewLocation


class LocationRepository(ABC):
    @abstractmethod
    async def add(self, new: NewLocation) -> Location: ...

    @abstractmethod
    async def list_all(self) -> list[Location]: ...

    @abstractmethod
    async def delete(self, location_id: int) -> Location | None: ...


class ForecastRepository(ABC):
    @abstractmethod
    async def add(self, forecast: Forecast) -> Forecast: ...

    @abstractmethod
    async def list_all(self, location_id: int | None = None) -> list[Forecast]: ...

    @abstractmethod
    async def latest_per_location(self) -> list[Forecast]: ...

    @abstractmethod
    async def delete_for_location(self, location_id: int) -> None: ...


class InMemoryLocationRepository(LocationRepository):
    def __init__(self) -> None:
        self._items: dict[int, Location] = {}
        self._current_id = 0

    async def add(self, new: NewLocation) -> Location:
        self._current_id += 1
        location = Location(id=self._current_id, name=new.name, lat=new.lat, lon=new.lon)
        self._items[self._current_id] = location
        return location

    async def list_all(self) -> list[Location]:
        return list(self._items.values())

    async def delete(self, location_id: int) -> Location | None:
        return self._items.pop(location_id, None)


class InMemoryForecastRepository(ForecastRepository):
    def __init__(self) -> None:
        self._items: dict[int, Forecast] = {}
        self._current_id = 0

    async def add(self, forecast: Forecast) -> Forecast:
        self._current_id += 1
        stored = replace(forecast, id=self._current_id)
        self._items[self._current_id] = stored
        return stored

    async def list_all(self, location_id: int | None = None) -> list[Forecast]:
        items = list(self._items.values())
        if location_id is not None:
            items = [f for f in items if f.location_id == location_id]
        return self._newest_first(items)

    async def latest_per_location(self) -> list[Forecast]:
        newest: dict[int, Forecast] = {}
        for forecast in self._items.values():
            current = newest.get(forecast.location_id)
            if current is None or forecast.fetched_at > current.fetched_at:
                newest[forecast.location_id] = forecast
        return self._newest_first(newest.values())

    async def delete_for_location(self, location_id: int) -> None:
        for forecast_id in [
            fid for fid, f in self._items.items() if f.location_id == location_id
        ]:
            del self._items[forecast_id]

    @staticmethod
    def _newest_first(items: Iterable[Forecast]) -> list[Forecast]:
        return sorted(items, key=lambda f: f.fetched_at, reverse=True)
