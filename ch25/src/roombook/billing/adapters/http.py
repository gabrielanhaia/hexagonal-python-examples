from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from roombook.billing.application import ListInvoices

router = APIRouter(tags=["billing"])


class InvoiceOut(BaseModel):
    booking_id: str
    amount: int
    currency: str
    reason: str


def list_invoices(request: Request) -> ListInvoices:
    return cast(ListInvoices, request.app.state.list_invoices)


@router.get("/members/{member_id}/invoices")
async def get_invoices(
    member_id: str,
    invoices: Annotated[ListInvoices, Depends(list_invoices)],
) -> list[InvoiceOut]:
    return [
        InvoiceOut(
            booking_id=invoice.booking_id,
            amount=invoice.amount,
            currency=invoice.currency,
            reason=invoice.reason,
        )
        for invoice in await invoices(member_id)
    ]
