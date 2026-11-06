"""The same scenarios, byte for byte, in all five variants.

conftest.py fixes the clock at 2026-11-09 09:00 UTC. Room "atlas"
is open 08:00-20:00 UTC and costs 2400 EUR minor units an hour.
"""

import httpx2
from fastapi.testclient import TestClient

TODAY = "2026-11-09"
TOMORROW = "2026-11-10"


def hold(
    client: TestClient, start: str, end: str, room: str = "atlas"
) -> httpx2.Response:
    return client.post(
        f"/rooms/{room}/holds",
        json={"member_id": "m-1", "start": start, "end": end},
    )


def cancel(client: TestClient, booking_id: str) -> httpx2.Response:
    return client.post(f"/bookings/{booking_id}/cancel")


def held_id(client: TestClient, start: str, end: str) -> str:
    response = hold(client, start, end)
    assert response.status_code == 201
    booking_id: str = response.json()["booking_id"]
    return booking_id


def test_hold_creates_a_held_booking_priced_by_the_hour(
    client: TestClient,
) -> None:
    response = hold(
        client, f"{TOMORROW}T10:00:00Z", f"{TOMORROW}T11:30:00Z"
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "HELD"
    assert body["price"] == {"amount": 3600, "currency": "EUR"}


def test_rejects_a_slot_off_the_quarter_hour_grid(
    client: TestClient,
) -> None:
    response = hold(
        client, f"{TOMORROW}T10:10:00Z", f"{TOMORROW}T11:00:00Z"
    )

    assert response.status_code == 422


def test_rejects_a_slot_that_ends_before_it_starts(
    client: TestClient,
) -> None:
    response = hold(
        client, f"{TOMORROW}T11:00:00Z", f"{TOMORROW}T10:00:00Z"
    )

    assert response.status_code == 422


def test_rejects_a_slot_outside_opening_hours(
    client: TestClient,
) -> None:
    response = hold(
        client, f"{TOMORROW}T19:00:00Z", f"{TOMORROW}T21:00:00Z"
    )

    assert response.status_code == 422


def test_rejects_an_unknown_room(client: TestClient) -> None:
    response = hold(
        client,
        f"{TOMORROW}T10:00:00Z",
        f"{TOMORROW}T11:00:00Z",
        room="nowhere",
    )

    assert response.status_code == 404


def test_rejects_a_hold_that_overlaps_another(
    client: TestClient,
) -> None:
    held_id(
        client, f"{TOMORROW}T10:00:00Z", f"{TOMORROW}T12:00:00Z"
    )

    response = hold(
        client, f"{TOMORROW}T11:00:00Z", f"{TOMORROW}T13:00:00Z"
    )

    assert response.status_code == 409


def test_accepts_a_slot_that_starts_when_another_ends(
    client: TestClient,
) -> None:
    held_id(
        client, f"{TOMORROW}T10:00:00Z", f"{TOMORROW}T11:00:00Z"
    )

    response = hold(
        client, f"{TOMORROW}T11:00:00Z", f"{TOMORROW}T12:00:00Z"
    )

    assert response.status_code == 201


def test_cancelling_24_hours_ahead_is_free(
    client: TestClient,
) -> None:
    booking_id = held_id(
        client, f"{TOMORROW}T10:00:00Z", f"{TOMORROW}T11:00:00Z"
    )

    response = cancel(client, booking_id)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CANCELLED"
    assert body["fee"] == {"amount": 0, "currency": "EUR"}


def test_cancelling_late_costs_half_the_price(
    client: TestClient,
) -> None:
    booking_id = held_id(
        client, f"{TODAY}T18:00:00Z", f"{TODAY}T19:00:00Z"
    )

    response = cancel(client, booking_id)

    assert response.status_code == 200
    assert response.json()["fee"] == {
        "amount": 1200,
        "currency": "EUR",
    }


def test_cancelling_an_unknown_booking_is_not_found(
    client: TestClient,
) -> None:
    response = cancel(client, "no-such-booking")

    assert response.status_code == 404


def test_cancelling_twice_is_a_conflict(client: TestClient) -> None:
    booking_id = held_id(
        client, f"{TOMORROW}T10:00:00Z", f"{TOMORROW}T11:00:00Z"
    )
    cancel(client, booking_id)

    response = cancel(client, booking_id)

    assert response.status_code == 409


def test_a_cancelled_slot_can_be_held_again(
    client: TestClient,
) -> None:
    booking_id = held_id(
        client, f"{TOMORROW}T10:00:00Z", f"{TOMORROW}T11:00:00Z"
    )
    cancel(client, booking_id)

    response = hold(
        client, f"{TOMORROW}T10:00:00Z", f"{TOMORROW}T11:00:00Z"
    )

    assert response.status_code == 201


def test_rejects_a_booking_longer_than_four_hours(
    client: TestClient,
) -> None:
    response = hold(
        client, f"{TOMORROW}T10:00:00Z", f"{TOMORROW}T14:15:00Z"
    )

    assert response.status_code == 422


def test_accepts_a_booking_of_exactly_four_hours(
    client: TestClient,
) -> None:
    response = hold(
        client, f"{TOMORROW}T10:00:00Z", f"{TOMORROW}T14:00:00Z"
    )

    assert response.status_code == 201
    assert response.json()["price"] == {
        "amount": 9600,
        "currency": "EUR",
    }
