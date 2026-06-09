import json
from pathlib import Path

import httpx
import pytest

from weather import (
    FakeWeatherForecastClient,
    WeatherClientError,
    YrWeatherForecastClient,
)

# Ekte svar fra Yr lagret til fil, slik at parsingen testes mot reelt format.
_REAL_SAMPLE = json.loads(
    (Path(__file__).parent / "fixtures" / "yr_compact_oslo.json").read_text()
)

# Forenklet utdrag av Yr sitt compact-svar (kun feltene som leses).
_SAMPLE = {
    "properties": {
        "timeseries": [
            {"data": {"instant": {"details": {"air_temperature": 12.3}}}},
        ]
    }
}


def _client_with(handler: object) -> YrWeatherForecastClient:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    return YrWeatherForecastClient(user_agent="test-agent/1.0 me@example.com", transport=transport)


class TestFakeWeatherForecastClient:
    @pytest.mark.asyncio
    async def test_returns_configured_temperature(self) -> None:
        client = FakeWeatherForecastClient(temperature=7.5)
        assert await client.fetch_temperature(59.9, 10.7) == 7.5

    @pytest.mark.asyncio
    async def test_default_temperature(self) -> None:
        client = FakeWeatherForecastClient()
        assert await client.fetch_temperature(0.0, 0.0) == 18.0

    @pytest.mark.asyncio
    async def test_raises_configured_error(self) -> None:
        client = FakeWeatherForecastClient(error=RuntimeError("Kilden er nede"))
        with pytest.raises(RuntimeError, match="Kilden er nede"):
            await client.fetch_temperature(59.9, 10.7)


class TestYrWeatherForecastClient:
    @pytest.mark.asyncio
    async def test_parses_temperature_from_sample(self) -> None:
        client = _client_with(lambda request: httpx.Response(200, json=_SAMPLE))
        assert await client.fetch_temperature(59.9, 10.7) == 12.3

    @pytest.mark.asyncio
    async def test_parses_temperature_from_real_yr_response(self) -> None:
        client = _client_with(lambda request: httpx.Response(200, json=_REAL_SAMPLE))
        assert await client.fetch_temperature(59.9139, 10.7522) == 14.6

    @pytest.mark.asyncio
    async def test_sends_required_user_agent_and_coordinates(self) -> None:
        captured: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["user_agent"] = request.headers["user-agent"]
            captured["query"] = str(request.url.query, "utf-8")
            return httpx.Response(200, json=_SAMPLE)

        await _client_with(handler).fetch_temperature(59.9, 10.7)
        assert captured["user_agent"] == "test-agent/1.0 me@example.com"
        assert "lat=59.9" in captured["query"]
        assert "lon=10.7" in captured["query"]

    @pytest.mark.asyncio
    async def test_non_200_raises_weather_client_error(self) -> None:
        client = _client_with(lambda request: httpx.Response(503))
        with pytest.raises(WeatherClientError):
            await client.fetch_temperature(59.9, 10.7)

    @pytest.mark.asyncio
    async def test_malformed_response_raises_weather_client_error(self) -> None:
        client = _client_with(lambda request: httpx.Response(200, json={"unexpected": 1}))
        with pytest.raises(WeatherClientError):
            await client.fetch_temperature(59.9, 10.7)

    @pytest.mark.asyncio
    async def test_network_error_raises_weather_client_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("nede")

        with pytest.raises(WeatherClientError):
            await _client_with(handler).fetch_temperature(59.9, 10.7)
