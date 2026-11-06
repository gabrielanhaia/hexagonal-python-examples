"""Explicit mappers between ORM records and domain objects."""

from datetime import datetime

from sqlalchemy.dialects.postgresql import Range

from roombook.adapters.outbound.sqlalchemy.records import (
    BookingRecord,
    RoomRecord,
)
from roombook.domain.booking import Booking, BookingStatus
from roombook.domain.ids import BookingId, MemberId, RoomId
from roombook.domain.money import Money
from roombook.domain.room import OpeningHours, Room
from roombook.domain.time_slot import TimeSlot


def room_from_record(record: RoomRecord) -> Room:
    return Room(
        id=RoomId(record.id),
        name=record.name,
        capacity=record.capacity,
        hourly_rate=Money(record.hourly_rate, record.currency),
        opening_hours=OpeningHours(
            opens=record.opens,
            closes=record.closes,
            timezone=record.timezone,
        ),
    )


def room_to_record(room: Room) -> RoomRecord:
    return RoomRecord(
        id=room.id,
        name=room.name,
        capacity=room.capacity,
        hourly_rate=room.hourly_rate.amount,
        currency=room.hourly_rate.currency,
        opens=room.opening_hours.opens,
        closes=room.opening_hours.closes,
        timezone=room.opening_hours.timezone,
    )


def booking_from_record(record: BookingRecord) -> Booking:
    return Booking(
        id=BookingId(record.id),
        room_id=RoomId(record.room_id),
        member_id=MemberId(record.member_id),
        slot=slot_from_range(record.slot),
        price=Money(record.price, record.currency),
        status=BookingStatus(record.status),
        held_at=record.held_at,
        payment_id=record.payment_id,
    )


def booking_to_record(booking: Booking) -> BookingRecord:
    return BookingRecord(
        id=booking.id,
        room_id=booking.room_id,
        member_id=booking.member_id,
        slot=slot_to_range(booking.slot),
        price=booking.price.amount,
        currency=booking.price.currency,
        status=booking.status,
        held_at=booking.held_at,
        payment_id=booking.payment_id,
    )


def update_record(record: BookingRecord, booking: Booking) -> None:
    """Copy the fields a booking may change after it is held."""
    record.status = booking.status
    record.payment_id = booking.payment_id


def slot_to_range(slot: TimeSlot) -> Range[datetime]:
    return Range(slot.start, slot.end, bounds="[)")


def slot_from_range(value: Range[datetime]) -> TimeSlot:
    if value.lower is None or value.upper is None:
        raise ValueError(f"a booking slot must be bounded: {value}")
    return TimeSlot(value.lower, value.upper)
