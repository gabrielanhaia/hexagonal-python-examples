from pydantic import BaseModel


class Price(BaseModel):
    amount: int
    currency: str


class HoldRoomResponse(BaseModel):
    booking_id: str
    status: str
    price: Price
