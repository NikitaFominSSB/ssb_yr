from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from repositories import InMemoryForecastRepository, InMemoryLocationRepository
from weather import FakeWeatherForecastClient
from main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Ferske repositorier per test ved å sette app.state på nytt."""
    app.state.locations = InMemoryLocationRepository()
    app.state.forecasts = InMemoryForecastRepository()
    app.state.weather = FakeWeatherForecastClient(temperature=18.0)
    with TestClient(app) as c:
        yield c


def _create_oslo(client: TestClient) -> int:
    resp = client.post("/locations", json={"name": "Oslo", "lat": 59.9139, "lon": 10.7522})
    assert resp.status_code == 201
    location_id: int = resp.json()["location"]["id"]
    return location_id


def test_create_and_list_location(client: TestClient) -> None:
    _create_oslo(client)
    resp = client.get("/locations")
    assert resp.status_code == 200
    locations = resp.json()["locations"]
    assert len(locations) == 1
    assert locations[0]["name"] == "Oslo"


def test_create_location_rejects_bad_coordinates(client: TestClient) -> None:
    resp = client.post("/locations", json={"name": "Oslo", "lat": 999, "lon": 10.0})
    assert resp.status_code == 422


def test_delete_unknown_location_returns_404(client: TestClient) -> None:
    resp = client.delete("/locations/999")
    assert resp.status_code == 404


def test_fetch_returns_updated_count(client: TestClient) -> None:
    _create_oslo(client)
    resp = client.post("/fetch")
    assert resp.status_code == 200
    body = resp.json()
    assert body["updated"] == 1
    assert body["failed"] == 0


def test_forecasts_listed_after_fetch(client: TestClient) -> None:
    location_id = _create_oslo(client)
    client.post("/fetch")
    resp = client.get("/forecasts")
    assert resp.status_code == 200
    forecasts = resp.json()["forecasts"]
    assert len(forecasts) == 1
    assert forecasts[0]["location_id"] == location_id
    assert forecasts[0]["air_temperature"] == 18.0
    assert forecasts[0]["stale"] is False


def test_latest_is_empty_when_nothing_fetched(client: TestClient) -> None:
    resp = client.get("/forecasts/latest")
    assert resp.status_code == 200
    assert resp.json()["forecasts"] == []


def test_latest_returns_one_per_location(client: TestClient) -> None:
    client.post("/locations", json={"name": "Oslo", "lat": 59.9, "lon": 10.7})
    client.post("/locations", json={"name": "Bergen", "lat": 60.4, "lon": 5.3})
    client.post("/fetch")
    resp = client.get("/forecasts/latest")
    assert resp.status_code == 200
    latest = resp.json()["forecasts"]
    assert len(latest) == 2
    assert {f["location_id"] for f in latest} == {1, 2}


def test_history_is_newest_first(client: TestClient) -> None:
    location_id = _create_oslo(client)
    client.post("/fetch")
    client.post("/fetch")
    resp = client.get(f"/forecasts/{location_id}/history")
    assert resp.status_code == 200
    history = resp.json()["forecasts"]
    assert len(history) == 2
    assert history[0]["id"] > history[1]["id"]


def test_delete_location_cascades_forecasts(client: TestClient) -> None:
    location_id = _create_oslo(client)
    client.post("/fetch")
    assert len(client.get("/forecasts").json()["forecasts"]) == 1

    resp = client.delete(f"/locations/{location_id}")
    assert resp.status_code == 200
    assert client.get("/forecasts").json()["forecasts"] == []
