from roombook.adapters.outbound.outbox.messages import (
    BOOKINGS_TOPIC,
    to_message,
)
from roombook.domain.events import BookingCancelled
from roombook.domain.ids import BookingId
from roombook.domain.money import Money
from tests.support import ADA, NOW


def test_an_event_becomes_a_keyed_json_message() -> None:
    event = BookingCancelled(
        booking_id=BookingId("b-1"),
        member_id=ADA,
        fee=Money(2000, "EUR"),
        refund=Money(2000, "EUR"),
        occurred_at=NOW,
    )

    message = to_message(event)

    assert (message.topic, message.key) == (BOOKINGS_TOPIC, "b-1")
    assert message.type == "BookingCancelled"
    assert message.payload == {
        "booking_id": "b-1",
        "member_id": "member-ada",
        "fee": {"amount": 2000, "currency": "EUR"},
        "refund": {"amount": 2000, "currency": "EUR"},
        "occurred_at": "2026-11-30T09:00:00+00:00",
    }
