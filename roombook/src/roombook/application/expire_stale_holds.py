"""Release holds that were never paid for."""

from dataclasses import dataclass

from roombook.application.ports import (
    Clock,
    Notifier,
    UnitOfWorkFactory,
)
from roombook.domain.events import BookingEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class ExpireStaleHolds:
    unit_of_work: UnitOfWorkFactory
    notifier: Notifier
    clock: Clock

    async def __call__(self) -> int:
        """Expire every stale hold; return how many there were."""
        now = self.clock.now()
        events: list[BookingEvent] = []
        async with self.unit_of_work() as uow:
            stale = await uow.bookings.stale_holds(now)
            for booking in stale:
                booking.expire(now)
                await uow.bookings.save(booking)
                events += booking.pull_events()
            await uow.outbox.put(events)
            await uow.commit()
        await self.notifier.notify(events)
        return len(stale)
