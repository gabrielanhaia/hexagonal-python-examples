from typing import Protocol
from uuid import uuid4

from roombook.billing.domain import Invoice
from roombook.contracts.events import BookingCancelled


class Invoices(Protocol):
    async def add(self, invoice: Invoice) -> None: ...

    async def for_booking(
        self, booking_id: str
    ) -> Invoice | None: ...

    async def for_member(self, member_id: str) -> list[Invoice]: ...


class IssueCancellationInvoice:
    """Reacts to booking's event; safe to receive it twice."""

    def __init__(self, invoices: Invoices) -> None:
        self._invoices = invoices

    async def __call__(self, event: BookingCancelled) -> None:
        if event.fee_amount == 0:
            return
        if await self._invoices.for_booking(event.booking_id):
            return
        await self._invoices.add(
            Invoice(
                id=uuid4().hex,
                member_id=event.member_id,
                booking_id=event.booking_id,
                amount=event.fee_amount,
                currency=event.currency,
                reason="late cancellation",
            )
        )


class ListInvoices:
    def __init__(self, invoices: Invoices) -> None:
        self._invoices = invoices

    async def __call__(self, member_id: str) -> list[Invoice]:
        return await self._invoices.for_member(member_id)
