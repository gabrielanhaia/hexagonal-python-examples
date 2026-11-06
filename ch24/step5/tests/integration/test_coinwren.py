import json

import httpx2
import pytest

from app.adapters.coinwren import CoinwrenPayments
from app.domain.errors import PaymentDeclined
from app.domain.values import Money

PRICE = Money(amount=2400, currency="EUR")


def coinwren(status: int) -> httpx2.AsyncClient:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert json.loads(request.content) == {
            "amount": 2400,
            "currency": "EUR",
            "reference": "b-1",
        }
        return httpx2.Response(status, json={"id": "ch_9"})

    return httpx2.AsyncClient(
        transport=httpx2.MockTransport(handler),
        base_url="https://coinwren.test",
    )


async def test_a_201_returns_the_payment_id() -> None:
    async with coinwren(201) as client:
        payment = await CoinwrenPayments(client).charge(
            "b-1", PRICE
        )

    assert payment == "ch_9"


async def test_anything_else_is_a_decline() -> None:
    async with coinwren(402) as client:
        with pytest.raises(PaymentDeclined):
            await CoinwrenPayments(client).charge("b-1", PRICE)
