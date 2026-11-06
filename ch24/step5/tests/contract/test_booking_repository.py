"""One suite, two adapters: what any BookingRepository must do."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.memory import InMemoryBookingRepository
from app.adapters.sqlalchemy.repositories import (
    SqlAlchemyBookingRepository,
)
from app.application.ports import BookingRepository
from app.domain.booking import Booking, BookingStatus
from app.domain.values import Money, TimeSlot

NOW = datetime(2026, 11, 9, 9, 0, tzinfo=UTC)


def booking(
    id: str,
    start: int,
    end: int,
    status: BookingStatus = BookingStatus.HELD,
) -> Booking:
    return Booking(
        id=id,
        room_id="atlas",
        member_id="m-1",
        slot=TimeSlot(
            start=datetime(2026, 11, 10, start, tzinfo=UTC),
            end=datetime(2026, 11, 10, end, tzinfo=UTC),
        ),
        price=Money(amount=2400, currency="EUR"),
        created_at=NOW,
        status=status,
    )


@pytest.fixture(params=["memory", "sqlalchemy"])
def bookings(
    request: pytest.FixtureRequest, session: AsyncSession
) -> BookingRepository:
    if request.param == "memory":
        return InMemoryBookingRepository()
    return SqlAlchemyBookingRepository(session)


async def test_a_saved_booking_comes_back_equal(
    bookings: BookingRepository,
) -> None:
    await bookings.save(booking("b-1", 10, 11))

    assert await bookings.get("b-1") == booking("b-1", 10, 11)


async def test_an_unknown_booking_is_none(
    bookings: BookingRepository,
) -> None:
    assert await bookings.get("nope") is None


async def test_save_replaces_the_stored_booking(
    bookings: BookingRepository,
) -> None:
    held = booking("b-1", 10, 11)
    await bookings.save(held)
    held.cancel(NOW)

    await bookings.save(held)

    stored = await bookings.get("b-1")
    assert stored is not None
    assert stored.status is BookingStatus.CANCELLED
    assert stored.fee == Money(amount=0, currency="EUR")


async def test_overlapping_returns_held_and_confirmed_only(
    bookings: BookingRepository,
) -> None:
    await bookings.save(booking("held", 10, 11))
    await bookings.save(
        booking("confirmed", 11, 12, BookingStatus.CONFIRMED)
    )
    await bookings.save(
        booking("cancelled", 10, 12, BookingStatus.CANCELLED)
    )
    await bookings.save(booking("after", 12, 13))

    found = await bookings.overlapping(
        "atlas", booking("probe", 10, 12).slot
    )

    assert sorted(b.id for b in found) == ["confirmed", "held"]
