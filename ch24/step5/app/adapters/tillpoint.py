from collections.abc import AsyncIterator

import httpx2

from app.domain.booking import BookingId
from app.domain.errors import PaymentDeclined
from app.domain.values import Money
from app.settings import settings


async def get_tillpoint() -> AsyncIterator[httpx2.AsyncClient]:
    async with httpx2.AsyncClient(
        base_url=settings.tillpoint_url,
        headers={
            "Authorization": f"Bearer {settings.tillpoint_api_key}"
        },
        timeout=10,
    ) as client:
        yield client


class TillpointPayments:
    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def charge(
        self, booking_id: BookingId, amount: Money
    ) -> str:
        response = await self._client.post(
            "/v1/charges",
            json={
                "amount": amount.amount,
                "currency": amount.currency,
                "reference": booking_id,
            },
        )
        if response.status_code != 201:
            raise PaymentDeclined("Payment declined")
        payment_id: str = response.json()["id"]
        return payment_id
