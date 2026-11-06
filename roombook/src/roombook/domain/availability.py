"""Free time is what the open window has left over."""

from collections.abc import Iterable
from datetime import datetime, tzinfo

from roombook.domain.time_slot import TimeSlot


def free_slots(
    window: TimeSlot, taken: Iterable[TimeSlot]
) -> list[TimeSlot]:
    """The parts of `window` no taken slot covers, in its zone."""
    zone = window.start.tzinfo
    free: list[TimeSlot] = []
    cursor = window.start
    for slot in sorted(taken, key=lambda slot: slot.start):
        if slot.start > cursor:
            end = min(slot.start, window.end)
            free.append(_slot_in(zone, cursor, end))
        cursor = max(cursor, slot.end)
        if cursor >= window.end:
            return free
    free.append(_slot_in(zone, cursor, window.end))
    return free


def _slot_in(
    zone: tzinfo | None, start: datetime, end: datetime
) -> TimeSlot:
    return TimeSlot(start.astimezone(zone), end.astimezone(zone))
