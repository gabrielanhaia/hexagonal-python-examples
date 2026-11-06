"""Each context on its own, with no HTTP and no other context."""

from datetime import UTC, datetime

from roombook.billing.adapters.memory import InMemoryInvoices
from roombook.billing.application import IssueCancellationInvoice
from roombook.contracts.events import BookingCancelled
from roombook.platform.bus import EventBus

LATE = BookingCancelled(
    booking_id="b-1",
    member_id="m-1",
    fee_amount=1200,
    currency="EUR",
    occurred_at=datetime(2026, 11, 9, 9, 0, tzinfo=UTC),
)


async def test_billing_invoices_a_booking_once() -> None:
    invoices = InMemoryInvoices()
    issue = IssueCancellationInvoice(invoices)

    await issue(LATE)
    await issue(LATE)  # delivered twice

    assert len(await invoices.for_member("m-1")) == 1


async def test_the_bus_delivers_to_every_subscriber() -> None:
    bus = EventBus()
    seen: list[str] = []

    async def first(event: BookingCancelled) -> None:
        seen.append(f"first {event.booking_id}")

    async def second(event: BookingCancelled) -> None:
        seen.append(f"second {event.booking_id}")

    bus.subscribe(BookingCancelled, first)
    bus.subscribe(BookingCancelled, second)
    await bus.publish(LATE)

    assert seen == ["first b-1", "second b-1"]
