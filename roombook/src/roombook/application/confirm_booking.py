"""Confirm a held booking once its payment has gone through."""

from dataclasses import dataclass

from roombook.application.ports import (
    Clock,
    Notifier,
    UnitOfWorkFactory,
)
from roombook.domain.errors import BookingNotFound
from roombook.domain.ids import BookingId


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfirmBookingCommand:
    booking_id: BookingId
    payment_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfirmBooking:
    unit_of_work: UnitOfWorkFactory
    notifier: Notifier
    clock: Clock

    async def __call__(
        self, command: ConfirmBookingCommand
    ) -> None:
        async with self.unit_of_work() as uow:
            booking = await uow.bookings.get(command.booking_id)
            if booking is None:
                raise BookingNotFound(
                    f"no booking {command.booking_id}"
                )
            booking.confirm(command.payment_id, self.clock.now())
            await uow.bookings.save(booking)
            events = booking.pull_events()
            await uow.outbox.put(events)
            await uow.commit()
        await self.notifier.notify(events)
