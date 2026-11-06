"""A room and the maintenance windows it owns."""

from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import NewType

from roombook.domain.errors import (
    BlackoutOverlaps,
    RoomBlackedOut,
    UnknownBlackout,
)
from roombook.domain.time_slot import TimeSlot

RoomId = NewType("RoomId", str)
BlackoutId = NewType("BlackoutId", str)


@dataclass(frozen=True, slots=True, kw_only=True)
class BlackoutPeriod:
    id: BlackoutId
    slot: TimeSlot
    reason: str


class Room:
    """The aggregate root. Blackouts change only through it."""

    def __init__(
        self,
        id: RoomId,
        name: str,
        blackouts: Iterable[BlackoutPeriod] = (),
    ) -> None:
        self.id = id
        self.name = name
        self._blackouts = {b.id: b for b in blackouts}

    @property
    def blackouts(self) -> list[BlackoutPeriod]:
        values = self._blackouts.values()
        return sorted(values, key=lambda b: b.slot.start)

    def add_blackout(self, blackout: BlackoutPeriod) -> None:
        self._refuse_overlap(blackout)
        self._blackouts[blackout.id] = blackout

    def reschedule_blackout(
        self, blackout_id: BlackoutId, slot: TimeSlot
    ) -> None:
        moved = replace(self._get(blackout_id), slot=slot)
        self._refuse_overlap(moved)
        self._blackouts[blackout_id] = moved

    def remove_blackout(self, blackout_id: BlackoutId) -> None:
        del self._blackouts[self._get(blackout_id).id]

    def check_bookable(self, slot: TimeSlot) -> None:
        for blackout in self._blackouts.values():
            if blackout.slot.overlaps(slot):
                raise RoomBlackedOut(
                    f"{self.name} is closed for "
                    f"{blackout.reason} during {blackout.slot}"
                )

    def _get(self, blackout_id: BlackoutId) -> BlackoutPeriod:
        try:
            return self._blackouts[blackout_id]
        except KeyError:
            raise UnknownBlackout(blackout_id) from None

    def _refuse_overlap(self, blackout: BlackoutPeriod) -> None:
        for other in self._blackouts.values():
            if other.id != blackout.id and other.slot.overlaps(
                blackout.slot
            ):
                raise BlackoutOverlaps(
                    f"{blackout.id} overlaps {other.id}"
                )
