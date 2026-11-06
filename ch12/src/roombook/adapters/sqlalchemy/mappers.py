"""Explicit mappers between the Room aggregate and its records."""

from collections.abc import Sequence

from roombook.adapters.sqlalchemy.records import (
    BlackoutRecord,
    RoomRecord,
)
from roombook.domain.room import (
    BlackoutId,
    BlackoutPeriod,
    Room,
    RoomId,
)
from roombook.domain.time_slot import TimeSlot


def to_domain(record: RoomRecord) -> Room:
    return Room(
        id=RoomId(record.id),
        name=record.name,
        blackouts=[blackout_to_domain(b) for b in record.blackouts],
    )


def to_record(room: Room) -> RoomRecord:
    return RoomRecord(
        id=room.id,
        name=room.name,
        blackouts=[blackout_to_record(b) for b in room.blackouts],
    )


def blackout_to_domain(record: BlackoutRecord) -> BlackoutPeriod:
    return BlackoutPeriod(
        id=BlackoutId(record.id),
        slot=TimeSlot(record.starts_at, record.ends_at),
        reason=record.reason,
    )


def blackout_to_record(blackout: BlackoutPeriod) -> BlackoutRecord:
    record = BlackoutRecord(id=blackout.id)
    update_blackout(record, blackout)
    return record


def update_blackout(
    record: BlackoutRecord, blackout: BlackoutPeriod
) -> None:
    record.starts_at = blackout.slot.start
    record.ends_at = blackout.slot.end
    record.reason = blackout.reason


def reconcile(
    records: list[BlackoutRecord],
    blackouts: Sequence[BlackoutPeriod],
) -> None:
    """Make the child rows match the domain, matched by id."""
    wanted = {blackout.id: blackout for blackout in blackouts}
    for record in list(records):
        if record.id not in wanted:
            records.remove(record)  # delete-orphan deletes the row
    existing = {record.id: record for record in records}
    for blackout in blackouts:
        if blackout.id in existing:
            update_blackout(existing[blackout.id], blackout)
        else:
            records.append(blackout_to_record(blackout))
