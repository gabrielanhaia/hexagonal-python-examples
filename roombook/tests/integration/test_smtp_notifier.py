"""The SMTP notifier against a minimal SMTP server."""

import asyncio
from collections.abc import AsyncIterator
from email import message_from_bytes
from email.message import Message

import pytest

from roombook.adapters.outbound.notify.smtp import SmtpNotifier
from roombook.domain.events import HoldExpired
from roombook.domain.ids import BookingId
from tests.support import ADA, NOW


class FakeSmtpServer:
    """Speaks just enough SMTP for smtplib.send_message."""

    def __init__(self) -> None:
        self.received: list[Message] = []

    async def handle(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        writer.write(b"220 fake ESMTP\r\n")
        while line := await reader.readline():
            verb = line[:4].upper()
            if verb == b"DATA":
                writer.write(b"354 go ahead\r\n")
                data = await reader.readuntil(b"\r\n.\r\n")
                self.received.append(message_from_bytes(data[:-5]))
                writer.write(b"250 queued\r\n")
            elif verb == b"QUIT":
                writer.write(b"221 bye\r\n")
                break
            else:
                writer.write(b"250 ok\r\n")
            await writer.drain()
        writer.close()


@pytest.fixture
async def smtp() -> AsyncIterator[tuple[FakeSmtpServer, int]]:
    fake = FakeSmtpServer()
    server = await asyncio.start_server(fake.handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    async with server:
        yield fake, port


async def test_sends_one_email_per_event(
    smtp: tuple[FakeSmtpServer, int],
) -> None:
    fake, port = smtp
    notifier = SmtpNotifier(
        host="127.0.0.1",
        port=port,
        sender="bookings@roombook.example",
        address_template="{member_id}@members.test",
    )

    await notifier.notify(
        [
            HoldExpired(
                booking_id=BookingId("b-1"),
                member_id=ADA,
                occurred_at=NOW,
            )
        ]
    )

    [email] = fake.received
    assert email["To"] == "member-ada@members.test"
    assert email["Subject"] == "Hold b-1 has expired"
