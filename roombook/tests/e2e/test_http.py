"""HTTP in, in-memory adapters out: the whole hexagon."""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from roombook.adapters.inbound.http.app import State, create_app
from tests.memory_wiring import memory_roombook

ADA = {"X-Member-Id": "member-ada"}
GRACE = {"X-Member-Id": "member-grace"}
TEN_TO_ELEVEN = {
    "room_id": "atlas",
    "start": "2026-12-01T10:00:00Z",
    "end": "2026-12-01T11:00:00Z",
}


@pytest.fixture
def client() -> Iterator[TestClient]:
    roombook = memory_roombook()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[State]:
        yield {"use_cases": roombook}

    with TestClient(create_app(lifespan)) as test_client:
        yield test_client


def test_a_hold_is_created(client: TestClient) -> None:
    response = client.post(
        "/holds", json=TEN_TO_ELEVEN, headers=ADA
    )

    assert response.status_code == 201
    body = response.json()
    assert body["price"] == {"amount": 4000, "currency": "EUR"}
    assert body["expires_at"] == "2026-11-30T09:15:00Z"


def test_a_conflicting_hold_is_a_409_problem(
    client: TestClient,
) -> None:
    client.post("/holds", json=TEN_TO_ELEVEN, headers=ADA)

    response = client.post(
        "/holds", json=TEN_TO_ELEVEN, headers=GRACE
    )

    assert response.status_code == 409
    assert response.headers["content-type"] == (
        "application/problem+json"
    )
    problem = response.json()
    assert problem["type"].endswith("/slot-unavailable")
    assert problem["status"] == 409
    assert problem["instance"] == "/holds"


def test_the_member_cancels_for_free_before_paying(
    client: TestClient,
) -> None:
    hold = client.post("/holds", json=TEN_TO_ELEVEN, headers=ADA)
    booking_id = hold.json()["booking_id"]

    response = client.post(
        f"/bookings/{booking_id}/cancel", headers=ADA
    )

    assert response.status_code == 200
    assert response.json()["fee"] == {
        "amount": 0,
        "currency": "EUR",
    }


def test_availability_skips_held_time(client: TestClient) -> None:
    client.post("/holds", json=TEN_TO_ELEVEN, headers=ADA)

    response = client.get(
        "/rooms/atlas/availability", params={"day": "2026-12-01"}
    )

    starts = [slot["start"] for slot in response.json()["free"]]
    assert starts == [
        "2026-12-01T08:00:00Z",
        "2026-12-01T11:00:00Z",
    ]


@pytest.mark.parametrize(
    ("body", "status", "problem"),
    [
        (
            {**TEN_TO_ELEVEN, "room_id": "nowhere"},
            404,
            "room-not-found",
        ),
        (
            {**TEN_TO_ELEVEN, "start": "2026-12-01T07:00:00Z"},
            422,
            "outside-opening-hours",
        ),
    ],
)
def test_refusals_map_to_problem_details(
    client: TestClient,
    body: dict[str, str],
    status: int,
    problem: str,
) -> None:
    response = client.post("/holds", json=body, headers=ADA)

    assert response.status_code == status
    assert response.json()["type"].endswith(problem)


def test_every_response_carries_a_correlation_id(
    client: TestClient,
) -> None:
    sent = {"X-Correlation-ID": "req-42"}

    response = client.get(
        "/rooms/atlas/availability",
        params={"day": "2026-12-01"},
        headers=sent,
    )

    assert response.headers["X-Correlation-ID"] == "req-42"
