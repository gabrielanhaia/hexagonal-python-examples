from pydantic import BaseModel


class CancelBookingRequest(BaseModel):
    booking_id: str
