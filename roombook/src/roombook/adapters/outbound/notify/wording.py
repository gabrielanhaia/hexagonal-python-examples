"""What each event means to the member, in one line."""

from typing import assert_never

from roombook.domain.events import (
    BookingCancelled,
    BookingConfirmed,
    BookingEvent,
    BookingHeld,
    HoldExpired,
)


def headline(event: BookingEvent) -> str:
    match event:
        case BookingHeld():
            until = event.expires_at.isoformat(timespec="minutes")
            return f"Room {event.room_id} is held until {until}"
        case BookingConfirmed():
            return f"Booking {event.booking_id} is confirmed"
        case BookingCancelled():
            return (
                f"Booking {event.booking_id} is cancelled; "
                f"refund {event.refund}"
            )
        case HoldExpired():
            return f"Hold {event.booking_id} has expired"
        case _:
            assert_never(event)
