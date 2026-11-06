from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HoldRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    member_id: str
    start: datetime
    end: datetime


class MoneyOut(BaseModel):
    amount: int
    currency: str


class HoldResponse(BaseModel):
    booking_id: str
    status: str
    price: MoneyOut


class CancelResponse(BaseModel):
    booking_id: str
    status: str
    fee: MoneyOut
