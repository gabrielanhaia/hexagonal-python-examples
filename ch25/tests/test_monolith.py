"""Booking publishes, billing reacts, through the in-process bus."""

from fastapi.testclient import TestClient


def hold_and_cancel(
    client: TestClient, start: str, end: str
) -> str:
    held = client.post(
        "/rooms/atlas/holds",
        json={"member_id": "m-1", "start": start, "end": end},
    )
    assert held.status_code == 201
    booking_id: str = held.json()["booking_id"]
    assert client.post(f"/bookings/{booking_id}/cancel").is_success
    return booking_id


def test_a_late_cancellation_is_invoiced(
    client: TestClient,
) -> None:
    booking_id = hold_and_cancel(
        client, "2026-11-09T18:00:00Z", "2026-11-09T19:00:00Z"
    )

    invoices = client.get("/members/m-1/invoices").json()

    assert invoices == [
        {
            "booking_id": booking_id,
            "amount": 1200,
            "currency": "EUR",
            "reason": "late cancellation",
        }
    ]


def test_a_free_cancellation_is_not(client: TestClient) -> None:
    hold_and_cancel(
        client, "2026-11-12T10:00:00Z", "2026-11-12T11:00:00Z"
    )

    assert client.get("/members/m-1/invoices").json() == []


def test_booking_rules_still_hold(client: TestClient) -> None:
    body = {
        "member_id": "m-1",
        "start": "2026-11-12T10:00:00Z",
        "end": "2026-11-12T12:00:00Z",
    }
    client.post("/rooms/atlas/holds", json=body)

    clash = client.post("/rooms/atlas/holds", json=body)

    assert clash.status_code == 409
