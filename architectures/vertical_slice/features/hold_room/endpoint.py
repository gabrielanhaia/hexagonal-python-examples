from fastapi import APIRouter

from features.hold_room.handler import hold_room
from features.hold_room.request import HoldRoomRequest
from features.hold_room.response import HoldRoomResponse
from features.hold_room.store import HoldRoomStore
from kernel.dependencies import DatabaseDep

router = APIRouter()


@router.post("/rooms/{room_id}/holds", status_code=201)
async def post_hold(
    room_id: str, request: HoldRoomRequest, database: DatabaseDep
) -> HoldRoomResponse:
    return await hold_room(
        room_id, request, HoldRoomStore(database)
    )
