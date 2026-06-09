import pytest

from weather import FakeWeatherForecastClient


@pytest.mark.asyncio
async def test_returns_configured_temperature() -> None:
    client = FakeWeatherForecastClient(temperature=7.5)
    assert await client.fetch_temperature(59.9, 10.7) == 7.5


@pytest.mark.asyncio
async def test_default_temperature() -> None:
    client = FakeWeatherForecastClient()
    assert await client.fetch_temperature(0.0, 0.0) == 18.0


@pytest.mark.asyncio
async def test_raises_configured_error() -> None:
    client = FakeWeatherForecastClient(error=RuntimeError("Kilden er nede"))
    with pytest.raises(RuntimeError, match="Kilden er nede"):
        await client.fetch_temperature(59.9, 10.7)
