from datetime import datetime, timedelta
from typing import Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    field_validator,
    model_validator,
)

MAX_BOOKING_LENGTH = timedelta(hours=4)


class HoldRoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    member_id: str
    start: AwareDatetime
    end: AwareDatetime

    @field_validator("start", "end")
    @classmethod
    def on_the_quarter_hour(cls, moment: datetime) -> datetime:
        if (
            moment.minute % 15
            or moment.second
            or moment.microsecond
        ):
            raise ValueError("slots move in 15-minute steps")
        return moment

    @model_validator(mode="after")
    def start_before_end(self) -> Self:
        if self.start >= self.end:
            raise ValueError("start must be before end")
        return self

    @model_validator(mode="after")
    def at_most_four_hours(self) -> Self:
        if self.end - self.start > MAX_BOOKING_LENGTH:
            raise ValueError("bookings last at most 4 hours")
        return self
