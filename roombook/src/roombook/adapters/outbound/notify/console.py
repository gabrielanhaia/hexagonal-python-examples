"""A Notifier that writes to the log instead of a mailbox."""

from collections.abc import Sequence

import structlog

from roombook.adapters.outbound.notify.wording import headline
from roombook.domain.events import BookingEvent

log = structlog.get_logger()


class ConsoleNotifier:
    async def notify(self, events: Sequence[BookingEvent]) -> None:
        for event in events:
            await log.ainfo(
                "notification",
                member_id=event.member_id,
                text=headline(event),
            )
