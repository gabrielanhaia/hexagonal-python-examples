"""Cancel a booking under the cancellation policy."""

from dataclasses import dataclass

from roombook.application.ports import (
    Clock,
    Notifier,
    UnitOfWorkFactory,
)
from roombook.domain.cancellation import CancellationTerms
from roombook.domain.errors import BookingNotFound
from roombook.domain.ids import BookingId, MemberId


@dataclass(frozen=True, slots=True, kw_only=True)
class CancelBookingCommand:
    booking_id: BookingId
    member_id: MemberId


@dataclass(frozen=True, slots=True, kw_only=True)
class CancelBooking:
    unit_of_work: UnitOfWorkFactory
    notifier: Notifier
    clock: Clock

    async def __call__(
        self, command: CancelBookingCommand
    ) -> CancellationTerms:
        async with self.unit_of_work() as uow:
            booking = await uow.bookings.get(command.booking_id)
            if (
                booking is None
                or booking.member_id != command.member_id
            ):
                raise BookingNotFound(
                    f"no booking {command.booking_id}"
                )
            terms = booking.cancel(self.clock.now())
            await uow.bookings.save(booking)
            events = booking.pull_events()
            await uow.outbox.put(events)
            await uow.commit()
        await self.notifier.notify(events)
        return terms
