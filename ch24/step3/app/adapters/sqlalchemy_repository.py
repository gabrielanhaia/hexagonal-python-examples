from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.booking import Booking, BookingId, BookingStatus
from app.domain.room import OpeningHours, Room, RoomId
from app.domain.values import Money, TimeSlot
from app.models import BookingRow, RoomRow


def to_room(row: RoomRow) -> Room:
    return Room(
        id=row.id,
        name=row.name,
        hourly_rate=Money(
            amount=row.hourly_rate_cents, currency=row.currency
        ),
        hours=OpeningHours(
            opens=row.opens_at, closes=row.closes_at
        ),
    )


def to_booking(row: BookingRow) -> Booking:
    fee = row.cancellation_fee_cents
    return Booking(
        id=row.id,
        room_id=row.room_id,
        member_id=row.member_id,
        slot=TimeSlot(start=row.starts_at, end=row.ends_at),
        price=Money(amount=row.price_cents, currency=row.currency),
        created_at=row.created_at,
        status=BookingStatus(row.status),
        payment_id=row.payment_id,
        fee=None
        if fee is None
        else Money(amount=fee, currency=row.currency),
    )


def to_row(booking: Booking) -> BookingRow:
    return BookingRow(
        id=booking.id,
        room_id=booking.room_id,
        member_id=booking.member_id,
        starts_at=booking.slot.start,
        ends_at=booking.slot.end,
        status=booking.status.value,
        price_cents=booking.price.amount,
        currency=booking.price.currency,
        payment_id=booking.payment_id,
        cancellation_fee_cents=None
        if booking.fee is None
        else booking.fee.amount,
        created_at=booking.created_at,
    )


class SqlAlchemyRoomRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, room_id: RoomId) -> Room | None:
        row = await self._session.get(RoomRow, room_id)
        return None if row is None else to_room(row)


class SqlAlchemyBookingRepository:
    """Commits on save; a Unit of Work comes later (chapter 19)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, booking_id: BookingId) -> Booking | None:
        row = await self._session.get(BookingRow, booking_id)
        return None if row is None else to_booking(row)

    async def save(self, booking: Booking) -> None:
        await self._session.merge(to_row(booking))
        await self._session.commit()

    async def overlapping(
        self, room_id: RoomId, slot: TimeSlot
    ) -> list[Booking]:
        rows = await self._session.scalars(
            select(BookingRow).where(
                BookingRow.room_id == room_id,
                BookingRow.status.in_(["HELD", "CONFIRMED"]),
                BookingRow.starts_at < slot.end,
                BookingRow.ends_at > slot.start,
            )
        )
        return [to_booking(row) for row in rows]
