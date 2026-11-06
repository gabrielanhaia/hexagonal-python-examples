from datetime import datetime
from typing import Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    field_validator,
    model_validator,
)


class HoldIn(BaseModel):
    member_id: str
    start: AwareDatetime
    end: AwareDatetime

    @field_validator("start", "end")
    @classmethod
    def quarter_hours(cls, value: datetime) -> datetime:
        if value.minute % 15 or value.second or value.microsecond:
            raise ValueError("bookings start and end on 15 minutes")
        return value

    @model_validator(mode="after")
    def start_before_end(self) -> Self:
        if self.start >= self.end:
            raise ValueError("start must be before end")
        return self


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    room_id: str
    member_id: str
    starts_at: datetime
    ends_at: datetime
    status: str
    price_cents: int
    currency: str


class CancellationOut(BaseModel):
    booking_id: str
    status: str
    fee_cents: int
    currency: str
