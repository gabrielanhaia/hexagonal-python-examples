import json

import httpx2
import pytest

from app.adapters.tillpoint import TillpointPayments
from app.domain.errors import PaymentDeclined
from app.domain.values import Money

PRICE = Money(amount=2400, currency="EUR")


def tillpoint(status: int) -> httpx2.AsyncClient:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert json.loads(request.content) == {
            "amount": 2400,
            "currency": "EUR",
            "reference": "b-1",
        }
        return httpx2.Response(status, json={"id": "ch_9"})

    return httpx2.AsyncClient(
        transport=httpx2.MockTransport(handler),
        base_url="https://tillpoint.test",
    )


async def test_a_201_returns_the_payment_id() -> None:
    async with tillpoint(201) as client:
        payment = await TillpointPayments(client).charge(
            "b-1", PRICE
        )

    assert payment == "ch_9"


async def test_anything_else_is_a_decline() -> None:
    async with tillpoint(402) as client:
        with pytest.raises(PaymentDeclined):
            await TillpointPayments(client).charge("b-1", PRICE)
