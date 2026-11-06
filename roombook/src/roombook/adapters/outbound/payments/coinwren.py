"""PaymentGateway over Coinwren's checkout API (fictional)."""

import httpx2
from pydantic import BaseModel, ValidationError

from roombook.application.ports import Checkout, PaymentUnavailable
from roombook.domain.ids import BookingId
from roombook.domain.money import Money


class _CheckoutCreated(BaseModel):
    id: str
    url: str


def coinwren_client(
    base_url: str, api_key: str, timeout_seconds: float = 5.0
) -> httpx2.AsyncClient:
    return httpx2.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=timeout_seconds,
    )


class CoinwrenPaymentGateway:
    def __init__(self, client: httpx2.AsyncClient) -> None:
        self._client = client

    async def start_checkout(
        self, booking_id: BookingId, amount: Money
    ) -> Checkout:
        try:
            response = await self._client.post(
                "/v1/checkouts",
                json={
                    "reference": booking_id,
                    "amount": amount.amount,
                    "currency": amount.currency,
                },
                headers={"Idempotency-Key": booking_id},
            )
            response.raise_for_status()
            created = _CheckoutCreated.model_validate_json(
                response.content
            )
        except (httpx2.HTTPError, ValidationError) as error:
            raise PaymentUnavailable(
                f"Coinwren: {error}"
            ) from error
        return Checkout(id=created.id, url=created.url)
