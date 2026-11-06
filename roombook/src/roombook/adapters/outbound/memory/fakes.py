"""Fakes for the small ports: clock, ids, payments, notifier."""

from collections.abc import Sequence
from datetime import datetime, timedelta

from roombook.application.ports import Checkout
from roombook.domain.events import BookingEvent
from roombook.domain.ids import BookingId
from roombook.domain.money import Money


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


class SequentialIds:
    """UUID-shaped ids that count up: easy to read in a test."""

    def __init__(self) -> None:
        self._next = 1

    def new_booking_id(self) -> BookingId:
        number, self._next = self._next, self._next + 1
        return BookingId(f"00000000-0000-7000-8000-{number:012d}")


class FakePaymentGateway:
    """Opens checkouts on a pretend Tillpoint; charges nothing."""

    def __init__(self) -> None:
        self.checkouts: dict[BookingId, Money] = {}

    async def start_checkout(
        self, booking_id: BookingId, amount: Money
    ) -> Checkout:
        self.checkouts[booking_id] = amount
        checkout_id = f"chk_{len(self.checkouts)}"
        return Checkout(
            id=checkout_id,
            url=f"https://pay.tillpoint.example/{checkout_id}",
        )


class RecordingNotifier:
    def __init__(self) -> None:
        self.sent: list[BookingEvent] = []

    async def notify(self, events: Sequence[BookingEvent]) -> None:
        self.sent.extend(events)


class InMemoryProcessedMessages:
    def __init__(self) -> None:
        self._ids: set[str] = set()

    async def seen(self, message_id: str) -> bool:
        return message_id in self._ids

    async def remember(self, message_id: str) -> None:
        self._ids.add(message_id)
