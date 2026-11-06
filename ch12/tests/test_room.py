import pytest
from conftest import blackout, slot

from roombook.domain.errors import (
    BlackoutOverlaps,
    RoomBlackedOut,
    UnknownBlackout,
)
from roombook.domain.room import BlackoutId, Room, RoomId


def test_a_room_cannot_be_booked_during_a_blackout() -> None:
    room = Room(RoomId("atlas"), "Atlas", [blackout("paint", 1)])

    with pytest.raises(RoomBlackedOut, match="maintenance"):
        room.check_bookable(slot(1, 11, 13))
    room.check_bookable(slot(1, 12, 13))


def test_add_blackout_rejects_an_overlap() -> None:
    room = Room(RoomId("atlas"), "Atlas", [blackout("paint", 1)])

    with pytest.raises(BlackoutOverlaps, match="carpet"):
        room.add_blackout(blackout("carpet", 1))
    assert [b.id for b in room.blackouts] == ["paint"]


def test_rescheduling_checks_the_other_blackouts() -> None:
    room = Room(
        RoomId("atlas"),
        "Atlas",
        [blackout("paint", 1), blackout("carpet", 2)],
    )

    with pytest.raises(BlackoutOverlaps):
        room.reschedule_blackout(
            BlackoutId("carpet"), slot(1, 9, 10)
        )
    room.reschedule_blackout(BlackoutId("carpet"), slot(1, 12, 14))
    assert room.blackouts[1].slot == slot(1, 12, 14)


def test_removing_an_unknown_blackout_fails() -> None:
    room = Room(RoomId("atlas"), "Atlas")

    with pytest.raises(UnknownBlackout):
        room.remove_blackout(BlackoutId("paint"))
