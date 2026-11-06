import json
from datetime import UTC, datetime, timedelta

import httpx2


def at(day: datetime, hour: int, minute: int = 0) -> str:
    return day.replace(hour=hour, minute=minute).isoformat()


TODAY = datetime.now(UTC).replace(second=0, microsecond=0)
IN_THREE_DAYS = TODAY + timedelta(days=3)


async def test_hold_room_creates_a_held_booking(
    client: httpx2.AsyncClient,
) -> None:
    response = await client.post(
        "/rooms/atlas/holds",
        json={
            "member_id": "m-1",
            "start": at(IN_THREE_DAYS, 10),
            "end": at(IN_THREE_DAYS, 11, 30),
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "HELD"
    assert response.json()["price_cents"] == 3600


async def test_overlapping_hold_is_rejected(
    client: httpx2.AsyncClient,
) -> None:
    first = {
        "member_id": "m-1",
        "start": at(IN_THREE_DAYS, 10),
        "end": at(IN_THREE_DAYS, 12),
    }
    await client.post("/rooms/atlas/holds", json=first)

    response = await client.post(
        "/rooms/atlas/holds",
        json=first | {"member_id": "m-2"},
    )

    assert response.status_code == 409


async def test_late_cancellation_costs_half(
    client: httpx2.AsyncClient,
) -> None:
    held = await client.post(
        "/rooms/atlas/holds",
        json={
            "member_id": "m-1",
            "start": at(TODAY, 8),
            "end": at(TODAY, 9),
        },
    )

    response = await client.post(
        f"/bookings/{held.json()['id']}/cancel"
    )

    assert response.status_code == 200
    assert response.json()["fee_cents"] == 1200


async def test_confirm_charges_coinwren(
    client: httpx2.AsyncClient, charges: list[httpx2.Request]
) -> None:
    held = await client.post(
        "/rooms/atlas/holds",
        json={
            "member_id": "m-1",
            "start": at(IN_THREE_DAYS, 10),
            "end": at(IN_THREE_DAYS, 11),
        },
    )

    response = await client.post(
        f"/bookings/{held.json()['id']}/confirm"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"
    assert json.loads(charges[0].content)["amount"] == 2400
