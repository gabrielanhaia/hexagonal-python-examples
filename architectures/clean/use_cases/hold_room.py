from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, override
from uuid import uuid4

from entities.booking import Booking
from entities.errors import (
    DomainError,
    RoomNotFound,
    SlotUnavailable,
)
from entities.values import TimeSlot
from use_cases.failures import Failure, failure_from
from use_cases.gateways import BookingGateway, RoomGateway


@dataclass(frozen=True, slots=True, kw_only=True)
class HoldRoomRequest:
    room_id: str
    member_id: str
    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class HoldRoomResponse:
    booking_id: str
    status: str
    price_amount: int
    currency: str


class HoldRoomInputBoundary(Protocol):
    async def hold(self, request: HoldRoomRequest) -> None: ...


class HoldRoomOutputBoundary(Protocol):
    def present(self, response: HoldRoomResponse) -> None: ...

    def present_failure(self, failure: Failure) -> None: ...


class HoldRoomInteractor(HoldRoomInputBoundary):
    def __init__(
        self,
        *,
        rooms: RoomGateway,
        bookings: BookingGateway,
        output: HoldRoomOutputBoundary,
    ) -> None:
        self._rooms = rooms
        self._bookings = bookings
        self._output = output

    @override
    async def hold(self, request: HoldRoomRequest) -> None:
        try:
            booking = await self._hold(request)
        except DomainError as error:
            self._output.present_failure(failure_from(error))
            return
        self._output.present(
            HoldRoomResponse(
                booking_id=booking.id,
                status=booking.status,
                price_amount=booking.price.amount,
                currency=booking.price.currency,
            )
        )

    async def _hold(self, request: HoldRoomRequest) -> Booking:
        slot = TimeSlot(start=request.start, end=request.end)
        room = await self._rooms.get(request.room_id)
        if room is None:
            raise RoomNotFound(request.room_id)
        booking = Booking.hold(
            id=uuid4().hex,
            room=room,
            member_id=request.member_id,
            slot=slot,
        )
        if await self._bookings.overlapping(room.id, slot):
            raise SlotUnavailable(f"{room.name} is taken then")
        await self._bookings.save(booking)
        return booking
