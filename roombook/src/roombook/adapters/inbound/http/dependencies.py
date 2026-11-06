"""How a route gets its use case: from lifespan state."""

from typing import Annotated, Protocol

from fastapi import Depends, Header, Request

from roombook.application.cancel_booking import CancelBooking
from roombook.application.hold_room import HoldRoom
from roombook.application.list_availability import ListAvailability
from roombook.domain.ids import MemberId


class UseCases(Protocol):
    """What this adapter needs from the composition root."""

    @property
    def hold_room(self) -> HoldRoom: ...

    @property
    def cancel_booking(self) -> CancelBooking: ...

    @property
    def list_availability(self) -> ListAvailability: ...


def use_cases(request: Request) -> UseCases:
    wired: UseCases = request.state.use_cases
    return wired


UseCasesDep = Annotated[UseCases, Depends(use_cases)]


def hold_room(wired: UseCasesDep) -> HoldRoom:
    return wired.hold_room


def cancel_booking(wired: UseCasesDep) -> CancelBooking:
    return wired.cancel_booking


def list_availability(wired: UseCasesDep) -> ListAvailability:
    return wired.list_availability


def member_id(
    x_member_id: Annotated[str, Header()],
) -> MemberId:
    """Authentication happens upstream; it sends this header."""
    return MemberId(x_member_id)


HoldRoomDep = Annotated[HoldRoom, Depends(hold_room)]
CancelBookingDep = Annotated[CancelBooking, Depends(cancel_booking)]
ListAvailabilityDep = Annotated[
    ListAvailability, Depends(list_availability)
]
MemberIdDep = Annotated[MemberId, Depends(member_id)]
