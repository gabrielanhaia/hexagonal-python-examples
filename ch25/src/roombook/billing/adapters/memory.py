from roombook.billing.domain import Invoice


class InMemoryInvoices:
    def __init__(self) -> None:
        self._rows: list[Invoice] = []

    async def add(self, invoice: Invoice) -> None:
        self._rows.append(invoice)

    async def for_booking(self, booking_id: str) -> Invoice | None:
        return next(
            (i for i in self._rows if i.booking_id == booking_id),
            None,
        )

    async def for_member(self, member_id: str) -> list[Invoice]:
        return [i for i in self._rows if i.member_id == member_id]
