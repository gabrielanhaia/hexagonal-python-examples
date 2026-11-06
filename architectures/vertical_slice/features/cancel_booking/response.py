from pydantic import BaseModel


class Fee(BaseModel):
    amount: int
    currency: str


class CancelBookingResponse(BaseModel):
    booking_id: str
    status: str
    fee: Fee
