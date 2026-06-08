import pytest
from pydantic import ValidationError

from api.contracts import (
    CreateLocationRequest,
    FetchResponse,
)


def test_create_location_accepts_valid_coordinates() -> None:
    req = CreateLocationRequest(name="Oslo", lat=59.9139, lon=10.7522)
    assert req.name == "Oslo"


@pytest.mark.parametrize(
    ("name", "lat", "lon"),
    [
        ("", 59.9, 10.7),
        ("Oslo", 91.0, 10.7),
        ("Oslo", -91.0, 10.7),
        ("Oslo", 59.9, 181.0),
        ("Oslo", 59.9, -181.0),
    ],
)
def test_create_location_rejects_invalid_input(name: str, lat: float, lon: float) -> None:
    with pytest.raises(ValidationError):
        CreateLocationRequest(name=name, lat=lat, lon=lon)


def test_fetch_response_defaults() -> None:
    resp = FetchResponse(updated=3)
    assert resp.failed == 0
    assert resp.failures == []
