"""A driven adapter: the HTTP shape lives here, not in the core."""

import httpx2

from model import BookingId, Money, PaymentDeclined, PaymentId


class CoinwrenPayments:
    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def charge(
        self, booking_id: BookingId, amount: Money
    ) -> PaymentId:
        response = await self._client.post(
            "/v1/charges",
            json={
                "amount": amount.amount,
                "currency": amount.currency,
                "reference": booking_id,
            },
        )
        if response.status_code != 201:
            raise PaymentDeclined(booking_id)
        payment_id: PaymentId = response.json()["id"]
        return payment_id
