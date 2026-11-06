"""A Notifier that sends one email per event over SMTP."""

import asyncio
import smtplib
from collections.abc import Sequence
from email.message import EmailMessage

from roombook.adapters.outbound.notify.wording import headline
from roombook.domain.events import BookingEvent


class SmtpNotifier:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        sender: str,
        address_template: str,
    ) -> None:
        self._host = host
        self._port = port
        self._sender = sender
        self._address_template = address_template

    async def notify(self, events: Sequence[BookingEvent]) -> None:
        for event in events:
            await asyncio.to_thread(
                self._send, self._compose(event)
            )

    def _compose(self, event: BookingEvent) -> EmailMessage:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = self._address_template.format(
            member_id=event.member_id
        )
        message["Subject"] = headline(event)
        message.set_content(headline(event))
        return message

    def _send(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self._host, self._port) as smtp:
            smtp.send_message(message)
