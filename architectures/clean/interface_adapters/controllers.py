from datetime import datetime

from use_cases.cancel_booking import (
    CancelBookingInputBoundary,
    CancelBookingRequest,
)
from use_cases.hold_room import (
    HoldRoomInputBoundary,
    HoldRoomRequest,
)


class HoldRoomController:
    def __init__(self, use_case: HoldRoomInputBoundary) -> None:
        self._use_case = use_case

    async def hold(
        self,
        *,
        room_id: str,
        member_id: str,
        start: datetime,
        end: datetime,
    ) -> None:
        await self._use_case.hold(
            HoldRoomRequest(
                room_id=room_id,
                member_id=member_id,
                start=start,
                end=end,
            )
        )


class CancelBookingController:
    def __init__(
        self, use_case: CancelBookingInputBoundary
    ) -> None:
        self._use_case = use_case

    async def cancel(self, *, booking_id: str) -> None:
        await self._use_case.cancel(
            CancelBookingRequest(booking_id=booking_id)
        )
