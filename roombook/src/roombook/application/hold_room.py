"""Hold a room for fifteen minutes while the member pays."""

from dataclasses import dataclass
from datetime import datetime

from roombook.application.ports import (
    Clock,
    IdGenerator,
    PaymentGateway,
    UnitOfWorkFactory,
)
from roombook.domain.booking import Booking
from roombook.domain.errors import RoomNotFound, SlotUnavailable
from roombook.domain.ids import BookingId, MemberId, RoomId
from roombook.domain.money import Money
from roombook.domain.time_slot import TimeSlot


@dataclass(frozen=True, slots=True, kw_only=True)
class HoldRoomCommand:
    room_id: RoomId
    member_id: MemberId
    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class HoldReceipt:
    booking_id: BookingId
    price: Money
    expires_at: datetime
    checkout_url: str


@dataclass(frozen=True, slots=True, kw_only=True)
class HoldRoom:
    unit_of_work: UnitOfWorkFactory
    payments: PaymentGateway
    clock: Clock
    ids: IdGenerator

    async def __call__(
        self, command: HoldRoomCommand
    ) -> HoldReceipt:
        slot = TimeSlot(command.start, command.end)
        async with self.unit_of_work() as uow:
            room = await uow.rooms.get(command.room_id)
            if room is None:
                raise RoomNotFound(f"no room {command.room_id}")
            if await uow.bookings.overlapping(room.id, slot):
                raise SlotUnavailable(
                    f"room {room.id} is already booked for {slot}"
                )
            booking = Booking.hold(
                booking_id=self.ids.new_booking_id(),
                room=room,
                member_id=command.member_id,
                slot=slot,
                now=self.clock.now(),
            )
            await uow.bookings.add(booking)
            await uow.outbox.put(booking.pull_events())
            await uow.commit()
        checkout = await self.payments.start_checkout(
            booking.id, booking.price
        )
        return HoldReceipt(
            booking_id=booking.id,
            price=booking.price,
            expires_at=booking.expires_at,
            checkout_url=checkout.url,
        )
