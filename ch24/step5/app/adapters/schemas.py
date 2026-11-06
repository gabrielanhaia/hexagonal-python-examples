from datetime import datetime

from pydantic import AwareDatetime, BaseModel

from app.domain.booking import Booking


class HoldIn(BaseModel):
    member_id: str
    start: AwareDatetime
    end: AwareDatetime


class BookingOut(BaseModel):
    id: str
    room_id: str
    member_id: str
    starts_at: datetime
    ends_at: datetime
    status: str
    price_cents: int
    currency: str

    @classmethod
    def of(cls, booking: Booking) -> BookingOut:
        return cls(
            id=booking.id,
            room_id=booking.room_id,
            member_id=booking.member_id,
            starts_at=booking.slot.start,
            ends_at=booking.slot.end,
            status=booking.status,
            price_cents=booking.price.amount,
            currency=booking.price.currency,
        )


class CancellationOut(BaseModel):
    booking_id: str
    status: str
    fee_cents: int
    currency: str
