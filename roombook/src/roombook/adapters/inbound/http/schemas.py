"""Pydantic models: the HTTP contract, translated at the edge."""

from datetime import date, datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict

from roombook.application.hold_room import (
    HoldReceipt,
    HoldRoomCommand,
)
from roombook.application.list_availability import Availability
from roombook.domain.cancellation import CancellationTerms
from roombook.domain.ids import MemberId, RoomId
from roombook.domain.money import Money
from roombook.domain.time_slot import TimeSlot


class HoldRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    room_id: str
    start: AwareDatetime
    end: AwareDatetime

    def to_command(self, member_id: MemberId) -> HoldRoomCommand:
        return HoldRoomCommand(
            room_id=RoomId(self.room_id),
            member_id=member_id,
            start=self.start,
            end=self.end,
        )


class MoneyOut(BaseModel):
    amount: int
    currency: str

    @classmethod
    def of(cls, money: Money) -> MoneyOut:
        return cls(amount=money.amount, currency=money.currency)


class HoldResponse(BaseModel):
    booking_id: str
    price: MoneyOut
    expires_at: datetime
    checkout_url: str

    @classmethod
    def of(cls, receipt: HoldReceipt) -> HoldResponse:
        return cls(
            booking_id=receipt.booking_id,
            price=MoneyOut.of(receipt.price),
            expires_at=receipt.expires_at,
            checkout_url=receipt.checkout_url,
        )


class CancellationResponse(BaseModel):
    fee: MoneyOut
    refund: MoneyOut

    @classmethod
    def of(cls, terms: CancellationTerms) -> CancellationResponse:
        return cls(
            fee=MoneyOut.of(terms.fee),
            refund=MoneyOut.of(terms.refund),
        )


class SlotOut(BaseModel):
    start: datetime
    end: datetime

    @classmethod
    def of(cls, slot: TimeSlot) -> SlotOut:
        return cls(start=slot.start, end=slot.end)


class AvailabilityResponse(BaseModel):
    room_id: str
    day: date
    free: list[SlotOut]

    @classmethod
    def of(cls, availability: Availability) -> AvailabilityResponse:
        return cls(
            room_id=availability.room_id,
            day=availability.day,
            free=[SlotOut.of(slot) for slot in availability.free],
        )
