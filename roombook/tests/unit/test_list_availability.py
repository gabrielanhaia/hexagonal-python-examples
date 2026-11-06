from datetime import date

import pytest

from roombook.application.hold_room import HoldRoom, HoldRoomCommand
from roombook.application.list_availability import (
    AvailabilityQuery,
    ListAvailability,
)
from roombook.domain.errors import RoomNotFound
from roombook.domain.ids import RoomId
from tests.support import ADA, DAY, at, slot


async def test_a_hold_takes_its_slot_out_of_the_day(
    hold_room: HoldRoom, list_availability: ListAvailability
) -> None:
    await hold_room(
        HoldRoomCommand(
            room_id=RoomId("atlas"),
            member_id=ADA,
            start=at("10:00"),
            end=at("11:00"),
        )
    )

    found = await list_availability(
        AvailabilityQuery(
            room_id=RoomId("atlas"), day=date.fromisoformat(DAY)
        )
    )

    assert found.free == (
        slot("08:00", "10:00"),
        slot("11:00", "20:00"),
    )


async def test_an_unknown_room_has_no_availability(
    list_availability: ListAvailability,
) -> None:
    with pytest.raises(RoomNotFound):
        await list_availability(
            AvailabilityQuery(
                room_id=RoomId("nowhere"),
                day=date.fromisoformat(DAY),
            )
        )
