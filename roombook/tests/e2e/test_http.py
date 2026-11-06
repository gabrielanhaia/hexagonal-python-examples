"""HTTP in, in-memory adapters out: the whole hexagon."""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager

import httpx2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from structlog.contextvars import merge_contextvars
from structlog.testing import capture_logs

from roombook.adapters.inbound.http.app import State, create_app
from roombook.adapters.inbound.http.problems import OPAQUE_DETAIL
from roombook.adapters.outbound.memory.fakes import (
    FixedClock,
    RecordingNotifier,
    SequentialIds,
)
from roombook.adapters.outbound.memory.unit_of_work import (
    InMemoryStore,
)
from roombook.adapters.outbound.payments.tillpoint import (
    TillpointPaymentGateway,
)
from roombook.composition import build_roombook
from tests.memory_wiring import memory_roombook
from tests.support import NOW, atlas

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


def test_a_refusal_keeps_the_rule_s_own_sentence(
    client: TestClient,
) -> None:
    response = client.post(
        "/holds",
        json={**TEN_TO_ELEVEN, "room_id": "nowhere"},
        headers=ADA,
    )

    assert response.json()["detail"] == "no room nowhere"


def bad_gateway(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(502)


@pytest.fixture
def tillpoint_down() -> Iterator[TestClient]:
    """The real Tillpoint adapter, answering every call with 502."""
    room = atlas()
    store = InMemoryStore(rooms={room.id: room})
    tillpoint = httpx2.AsyncClient(
        transport=httpx2.MockTransport(bad_gateway),
        base_url="https://api.tillpoint.test",
    )
    roombook = build_roombook(
        unit_of_work=store.unit_of_work,
        payments=TillpointPaymentGateway(tillpoint),
        notifier=RecordingNotifier(),
        clock=FixedClock(NOW),
        ids=SequentialIds(),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[State]:
        yield {"use_cases": roombook}

    with TestClient(create_app(lifespan)) as test_client:
        yield test_client


def test_a_provider_outage_tells_the_client_nothing_about_it(
    tillpoint_down: TestClient,
) -> None:
    sent = {**ADA, "X-Correlation-ID": "req-43"}

    with capture_logs(processors=[merge_contextvars]) as logs:
        response = tillpoint_down.post(
            "/holds", json=TEN_TO_ELEVEN, headers=sent
        )

    assert response.status_code == 503
    problem = response.json()
    assert problem["type"].endswith("/payment-unavailable")
    assert problem["detail"] == OPAQUE_DETAIL
    for leak in ("tillpoint", "502", "/v1/checkouts"):
        assert leak not in response.text.lower()
    [failed] = [e for e in logs if e["event"] == "request failed"]
    assert failed["correlation_id"] == "req-43"
    assert failed["log_level"] == "error"
    assert "api.tillpoint.test" in failed["cause"]
