"""
Klient for værvarsler.
WeatherForecastClient er den abstrakte kontrakten.
"""

from abc import ABC, abstractmethod


class WeatherForecastClient(ABC):
    @abstractmethod
    async def fetch_temperature(self, lat: float, lon: float) -> float | None: ...


class FakeWeatherForecastClient(WeatherForecastClient):
    """Falsk klient som returnerer en fast temperatur.
    Kan konstrueres med en feil som kastes.
    """

    def __init__(self, temperature: float = 18.0, error: Exception | None = None) -> None:
        self._temperature = temperature
        self._error = error

    async def fetch_temperature(self, lat: float, lon: float) -> float | None:
        if self._error is not None:
            raise self._error
        return self._temperature
