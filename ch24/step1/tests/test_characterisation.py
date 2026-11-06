"""Pin what the HTTP API does today, before anything moves.

This file runs unchanged against every step in ch24/. The tests
use the real clock, like the app: TODAY's 08:00-09:00 slot is
always less than 24 hours away, IN_THREE_DAYS is always more.
"""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Protocol

import httpx2

TODAY = datetime.now(UTC).replace(second=0, microsecond=0)
IN_THREE_DAYS = TODAY + timedelta(days=3)
BOOKING_KEYS = {
    "id",
    "room_id",
    "member_id",
    "starts_at",
    "ends_at",
    "status",
    "price_cents",
    "currency",
}

type AgeHold = Callable[[str, int], Awaitable[None]]


class Tillpoint(Protocol):
    declines: bool

    @property
    def charges(self) -> list[object]: ...


def at(day: datetime, clock: str) -> str:
    hour, minute = map(int, clock.split(":"))
    return day.replace(hour=hour, minute=minute).isoformat()


async def hold(
    client: httpx2.AsyncClient,
    start: str,
    end: str,
    *,
    day: datetime = IN_THREE_DAYS,
    room: str = "atlas",
) -> httpx2.Response:
    return await client.post(
        f"/rooms/{room}/holds",
        json={
            "member_id": "m-1",
            "start": at(day, start),
            "end": at(day, end),
        },
    )


async def held(
    client: httpx2.AsyncClient,
    start: str,
    end: str,
    *,
    day: datetime = IN_THREE_DAYS,
) -> str:
    response = await hold(client, start, end, day=day)
    assert response.status_code == 201
    booking_id: str = response.json()["id"]
    return booking_id


async def test_hold_returns_the_booking(
    client: httpx2.AsyncClient,
) -> None:
    response = await hold(client, "10:00", "11:30")

    assert response.status_code == 201
    body = response.json()
    assert set(body) == BOOKING_KEYS
    assert body["status"] == "HELD"
    assert body["price_cents"] == 3600
    assert body["currency"] == "EUR"
    assert datetime.fromisoformat(body["starts_at"]) == (
        datetime.fromisoformat(at(IN_THREE_DAYS, "10:00"))
    )


async def test_hold_of_an_unknown_room_is_404(
    client: httpx2.AsyncClient,
) -> None:
    response = await hold(client, "10:00", "11:00", room="nowhere")

    assert response.status_code == 404


async def test_hold_off_the_quarter_hour_is_422(
    client: httpx2.AsyncClient,
) -> None:
    response = await hold(client, "10:10", "11:00")

    assert response.status_code == 422


async def test_hold_ending_before_it_starts_is_422(
    client: httpx2.AsyncClient,
) -> None:
    response = await hold(client, "11:00", "10:00")

    assert response.status_code == 422


async def test_hold_outside_opening_hours_is_422(
    client: httpx2.AsyncClient,
) -> None:
    response = await hold(client, "19:00", "21:00")

    assert response.status_code == 422


async def test_hold_over_another_hold_is_409(
    client: httpx2.AsyncClient,
) -> None:
    await held(client, "10:00", "12:00")

    response = await hold(client, "11:00", "13:00")

    assert response.status_code == 409


async def test_hold_over_an_expired_hold_is_allowed(
    client: httpx2.AsyncClient, age_hold: AgeHold
) -> None:
    await age_hold(await held(client, "10:00", "12:00"), 16)

    response = await hold(client, "11:00", "13:00")

    assert response.status_code == 201


async def test_hold_next_to_another_is_allowed(
    client: httpx2.AsyncClient,
) -> None:
    await held(client, "10:00", "11:00")

    response = await hold(client, "11:00", "12:00")

    assert response.status_code == 201


async def test_confirm_charges_tillpoint_and_confirms(
    client: httpx2.AsyncClient, tillpoint: Tillpoint
) -> None:
    booking_id = await held(client, "10:00", "11:00")

    response = await client.post(f"/bookings/{booking_id}/confirm")

    assert response.status_code == 200
    assert set(response.json()) == BOOKING_KEYS
    assert response.json()["status"] == "CONFIRMED"
    assert tillpoint.charges == [
        {"amount": 2400, "currency": "EUR", "reference": booking_id}
    ]


async def test_a_declined_payment_is_402_and_keeps_the_hold(
    client: httpx2.AsyncClient, tillpoint: Tillpoint
) -> None:
    booking_id = await held(client, "10:00", "11:00")
    tillpoint.declines = True

    declined = await client.post(f"/bookings/{booking_id}/confirm")
    tillpoint.declines = False
    retried = await client.post(f"/bookings/{booking_id}/confirm")

    assert declined.status_code == 402
    assert retried.status_code == 200


async def test_confirming_an_expired_hold_is_409_and_expires_it(
    client: httpx2.AsyncClient, age_hold: AgeHold
) -> None:
    booking_id = await held(client, "10:00", "11:00")
    await age_hold(booking_id, 16)

    confirm = await client.post(f"/bookings/{booking_id}/confirm")
    cancel = await client.post(f"/bookings/{booking_id}/cancel")

    assert confirm.status_code == 409
    assert cancel.status_code == 409
    assert cancel.json()["detail"] == "Booking is EXPIRED"


async def test_confirming_twice_is_409(
    client: httpx2.AsyncClient,
) -> None:
    booking_id = await held(client, "10:00", "11:00")
    await client.post(f"/bookings/{booking_id}/confirm")

    response = await client.post(f"/bookings/{booking_id}/confirm")

    assert response.status_code == 409


async def test_confirming_an_unknown_booking_is_404(
    client: httpx2.AsyncClient,
) -> None:
    response = await client.post("/bookings/nope/confirm")

    assert response.status_code == 404


async def test_cancelling_three_days_ahead_is_free(
    client: httpx2.AsyncClient,
) -> None:
    booking_id = await held(client, "10:00", "11:00")

    response = await client.post(f"/bookings/{booking_id}/cancel")

    assert response.status_code == 200
    assert response.json() == {
        "booking_id": booking_id,
        "status": "CANCELLED",
        "fee_cents": 0,
        "currency": "EUR",
    }


async def test_cancelling_late_costs_half(
    client: httpx2.AsyncClient,
) -> None:
    booking_id = await held(client, "08:00", "09:00", day=TODAY)

    response = await client.post(f"/bookings/{booking_id}/cancel")

    assert response.status_code == 200
    assert response.json()["fee_cents"] == 1200


async def test_cancelling_twice_is_409(
    client: httpx2.AsyncClient,
) -> None:
    booking_id = await held(client, "10:00", "11:00")
    await client.post(f"/bookings/{booking_id}/cancel")

    response = await client.post(f"/bookings/{booking_id}/cancel")

    assert response.status_code == 409


async def test_cancelling_an_unknown_booking_is_404(
    client: httpx2.AsyncClient,
) -> None:
    response = await client.post("/bookings/nope/cancel")

    assert response.status_code == 404
