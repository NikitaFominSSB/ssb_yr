"""
Klient for værvarsler.
WeatherForecastClient er den abstrakte kontrakten.
"""

from abc import ABC, abstractmethod

import httpx


_COMPACT_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"


class WeatherClientError(Exception):
    """Feil ved henting eller tolkning av værvarsel fra en ekstern kilde."""


class WeatherForecastClient(ABC):
    @abstractmethod
    async def fetch_temperature(self, lat: float, lon: float) -> float | None: ...


class YrWeatherForecastClient(WeatherForecastClient):
    """Henter temperatur fra Yr sitt compact-endepunkt over HTTP.
    Yr krever en User-Agent-header med kontaktinformasjon.
    """

    def __init__(
        self,
        user_agent: str,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._user_agent = user_agent
        self._timeout = timeout
        self._transport = transport

    async def fetch_temperature(self, lat: float, lon: float) -> float | None:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                transport=self._transport,
                headers={"User-Agent": self._user_agent},
            ) as client:
                response = await client.get(_COMPACT_URL, params={"lat": lat, "lon": lon})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise WeatherClientError(f"Henting fra Yr feilet: {exc}") from exc

        try:
            timeseries = response.json()["properties"]["timeseries"]
            details = timeseries[0]["data"]["instant"]["details"]
            return float(details["air_temperature"])
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise WeatherClientError("Uventet svarformat fra Yr") from exc


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
