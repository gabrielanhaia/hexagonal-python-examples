"""The road not taken: map the domain class itself.

roombook maps separate records (records.py, mappers.py). This
module shows the alternative, imperative mapping, on the real
Booking class, so its costs can be seen and tested.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Table,
    Text,
    TypeDecorator,
    Uuid,
    event,
)
from sqlalchemy.dialects.postgresql import TSTZRANGE, Range
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import composite, registry

from roombook.adapters.outbound.sqlalchemy.mappers import (
    slot_from_range,
    slot_to_range,
)
from roombook.domain.booking import Booking, BookingStatus
from roombook.domain.money import Money
from roombook.domain.time_slot import TimeSlot

mapper_registry = registry()


class TimeSlotType(TypeDecorator[TimeSlot]):
    """Store a TimeSlot as a tstzrange."""

    impl = TSTZRANGE
    cache_ok = True

    def process_bind_param(
        self, value: TimeSlot | None, dialect: Dialect
    ) -> Range[datetime] | None:
        if value is None:
            return None
        return slot_to_range(value)

    def process_result_value(
        self, value: Range[datetime] | None, dialect: Dialect
    ) -> TimeSlot | None:
        if value is None:
            return None
        return slot_from_range(value)


bookings = Table(
    "bookings",
    mapper_registry.metadata,
    Column("id", Uuid(as_uuid=False), primary_key=True),
    Column("room_id", Text, nullable=False),
    Column("member_id", Text, nullable=False),
    Column("slot", TimeSlotType, nullable=False),
    Column("price", Integer, nullable=False),
    Column("currency", String(3), nullable=False),
    Column(
        "status",
        Enum(BookingStatus, native_enum=False, length=16),
        nullable=False,
    ),
    Column("held_at", DateTime(timezone=True), nullable=False),
    Column("payment_id", Text),
)


def start_mappers() -> None:
    """Instrument Booking in place. Undo with dispose()."""
    mapper_registry.map_imperatively(
        Booking,
        bookings,
        properties={
            "price": composite(
                Money, bookings.c.price, bookings.c.currency
            ),
        },
    )
    event.listen(Booking, "load", _restore_event_list)


def dispose() -> None:
    event.remove(Booking, "load", _restore_event_list)
    mapper_registry.dispose()


def _restore_event_list(booking: Booking, _: object) -> None:
    # Loading skips __init__, so the dataclass default never ran.
    booking._events = []
