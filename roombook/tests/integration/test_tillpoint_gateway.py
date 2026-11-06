"""The Tillpoint adapter against a scripted HTTP transport."""

import json
from collections.abc import Callable

import httpx2
import pytest

from roombook.adapters.outbound.payments.tillpoint import (
    TillpointPaymentGateway,
)
from roombook.application.ports import Checkout, PaymentUnavailable
from roombook.domain.ids import BookingId
from roombook.domain.money import Money

type Handler = Callable[[httpx2.Request], httpx2.Response]

BOOKING = BookingId("b-1")
PRICE = Money(4000, "EUR")


def gateway(handler: Handler) -> TillpointPaymentGateway:
    client = httpx2.AsyncClient(
        transport=httpx2.MockTransport(handler),
        base_url="https://api.tillpoint.test",
    )
    return TillpointPaymentGateway(client)


async def test_opens_a_checkout_keyed_by_the_booking() -> None:
    seen: list[httpx2.Request] = []

    def tillpoint(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        body = {"id": "chk_9", "url": "https://pay.test/chk_9"}
        return httpx2.Response(201, json=body)

    checkout = await gateway(tillpoint).start_checkout(
        BOOKING, PRICE
    )

    assert checkout == Checkout(
        id="chk_9", url="https://pay.test/chk_9"
    )
    [request] = seen
    assert request.url.path == "/v1/checkouts"
    assert request.headers["Idempotency-Key"] == "b-1"
    assert json.loads(request.content) == {
        "reference": "b-1",
        "amount": 4000,
        "currency": "EUR",
    }


def server_error(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(503, json={"error": "maintenance"})


def wrong_shape(request: httpx2.Request) -> httpx2.Response:
    return httpx2.Response(201, json={"checkout": "chk_9"})


def unreachable(request: httpx2.Request) -> httpx2.Response:
    raise httpx2.ConnectError("connection refused", request=request)


@pytest.mark.parametrize(
    "tillpoint", [server_error, wrong_shape, unreachable]
)
async def test_provider_failures_become_payment_unavailable(
    tillpoint: Handler,
) -> None:
    with pytest.raises(PaymentUnavailable, match="Tillpoint"):
        await gateway(tillpoint).start_checkout(BOOKING, PRICE)
