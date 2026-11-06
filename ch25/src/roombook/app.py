"""One deployable, two contexts, wired in one place."""

from datetime import UTC, datetime, time

from fastapi import FastAPI

from roombook.billing.adapters import http as billing_http
from roombook.billing.adapters.memory import InMemoryInvoices
from roombook.billing.application import (
    IssueCancellationInvoice,
    ListInvoices,
)
from roombook.booking.adapters import http as booking_http
from roombook.booking.adapters.memory import (
    InMemoryBookings,
    InMemoryRooms,
)
from roombook.booking.application import (
    CancelBooking,
    Clock,
    HoldRoom,
)
from roombook.booking.domain import Money, Room
from roombook.contracts.events import BookingCancelled
from roombook.platform.bus import EventBus

ATLAS = Room(
    id="atlas",
    hourly_rate=Money(amount=2400, currency="EUR"),
    opens=time(8),
    closes=time(20),
)


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def create_app(*, clock: Clock | None = None) -> FastAPI:
    bus = EventBus()
    bookings = InMemoryBookings()
    invoices = InMemoryInvoices()
    bus.subscribe(
        BookingCancelled, IssueCancellationInvoice(invoices)
    )

    app = FastAPI(title="roombook, modular monolith")
    app.state.hold_room = HoldRoom(
        rooms=InMemoryRooms([ATLAS]), bookings=bookings
    )
    app.state.cancel_booking = CancelBooking(
        bookings=bookings, clock=clock or SystemClock(), events=bus
    )
    app.state.list_invoices = ListInvoices(invoices)
    app.include_router(booking_http.router)
    app.include_router(billing_http.router)
    return app
