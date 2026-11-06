from model import (
    BookingNotFound,
    IllegalTransition,
    PaymentDeclined,
)
from provider_shaped.ports import Database, HttpClient


class ConfirmBooking:
    def __init__(self, *, db: Database, http: HttpClient) -> None:
        self._db = db
        self._http = http

    async def __call__(self, booking_id: str) -> None:
        row = await self._db.fetch_one(
            "SELECT status, price_cents, currency"
            " FROM bookings WHERE id = %(id)s",
            {"id": booking_id},
        )
        if row is None:
            raise BookingNotFound(booking_id)
        if row["status"] != "HELD":
            raise IllegalTransition(f"booking is {row['status']}")
        response = await self._http.post(
            "/v1/charges",
            json={
                "amount": row["price_cents"],
                "currency": row["currency"],
                "reference": booking_id,
            },
        )
        if response.status_code != 201:
            raise PaymentDeclined(booking_id)
        await self._db.execute(
            "UPDATE bookings SET status = 'CONFIRMED',"
            " payment_id = %(payment_id)s WHERE id = %(id)s",
            {"payment_id": response.json()["id"], "id": booking_id},
        )
