"""The composition root: the one place adapters meet ports."""

import asyncio
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import timedelta

from fastapi import FastAPI
from faststream import FastStream
from faststream.kafka import KafkaBroker
from opentelemetry import trace
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from roombook.adapters.inbound.cli.commands import build_parser, run
from roombook.adapters.inbound.http.app import State, create_app
from roombook.adapters.inbound.messaging.tillpoint import (
    TillpointConsumer,
    tillpoint_router,
)
from roombook.adapters.outbound.memory.fakes import (
    FakePaymentGateway,
)
from roombook.adapters.outbound.notify.console import (
    ConsoleNotifier,
)
from roombook.adapters.outbound.notify.smtp import SmtpNotifier
from roombook.adapters.outbound.observability.logs import (
    configure_logging,
)
from roombook.adapters.outbound.observability.tracing import (
    TracedNotifier,
    TracedPaymentGateway,
    configure_tracing,
    instrument_engine,
)
from roombook.adapters.outbound.outbox.relay import (
    OutboxRelay,
    kafka_publisher,
)
from roombook.adapters.outbound.payments.tillpoint import (
    TillpointPaymentGateway,
    tillpoint_client,
)
from roombook.adapters.outbound.sqlalchemy.processed import (
    SqlAlchemyProcessedMessages,
)
from roombook.adapters.outbound.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from roombook.adapters.outbound.system import SystemClock, Uuid7Ids
from roombook.application.cancel_booking import CancelBooking
from roombook.application.confirm_booking import ConfirmBooking
from roombook.application.expire_stale_holds import ExpireStaleHolds
from roombook.application.hold_room import HoldRoom
from roombook.application.list_availability import ListAvailability
from roombook.application.ports import (
    Clock,
    IdGenerator,
    Notifier,
    PaymentGateway,
    UnitOfWork,
    UnitOfWorkFactory,
)
from roombook.settings import Settings

type Sessions = async_sessionmaker[AsyncSession]


@dataclass(frozen=True, slots=True, kw_only=True)
class Roombook:
    """Every use case, wired. One per process."""

    hold_room: HoldRoom
    confirm_booking: ConfirmBooking
    cancel_booking: CancelBooking
    list_availability: ListAvailability
    expire_stale_holds: ExpireStaleHolds


def build_roombook(
    *,
    unit_of_work: UnitOfWorkFactory,
    payments: PaymentGateway,
    notifier: Notifier,
    clock: Clock,
    ids: IdGenerator,
) -> Roombook:
    return Roombook(
        hold_room=HoldRoom(
            unit_of_work=unit_of_work,
            payments=payments,
            clock=clock,
            ids=ids,
        ),
        confirm_booking=ConfirmBooking(
            unit_of_work=unit_of_work,
            notifier=notifier,
            clock=clock,
        ),
        cancel_booking=CancelBooking(
            unit_of_work=unit_of_work,
            notifier=notifier,
            clock=clock,
        ),
        list_availability=ListAvailability(
            unit_of_work=unit_of_work
        ),
        expire_stale_holds=ExpireStaleHolds(
            unit_of_work=unit_of_work,
            notifier=notifier,
            clock=clock,
        ),
    )


@asynccontextmanager
async def database(settings: Settings) -> AsyncIterator[Sessions]:
    engine = create_async_engine(settings.database_url)
    instrument_engine(engine)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


@asynccontextmanager
async def payment_gateway(
    settings: Settings,
) -> AsyncIterator[PaymentGateway]:
    if settings.payments == "fake":
        yield FakePaymentGateway()
        return
    api_key = settings.tillpoint_api_key.get_secret_value()
    async with tillpoint_client(
        settings.tillpoint_url, api_key
    ) as c:
        yield TillpointPaymentGateway(c)


def notifier(settings: Settings) -> Notifier:
    if settings.notifier == "console":
        return ConsoleNotifier()
    return SmtpNotifier(
        host=settings.smtp_host,
        port=settings.smtp_port,
        sender=settings.mail_from,
        address_template=settings.member_address,
    )


@asynccontextmanager
async def roombook(
    settings: Settings, sessions: Sessions
) -> AsyncIterator[Roombook]:
    tracer = trace.get_tracer("roombook")

    def unit_of_work() -> UnitOfWork:
        return SqlAlchemyUnitOfWork(sessions)

    async with payment_gateway(settings) as payments:
        yield build_roombook(
            unit_of_work=unit_of_work,
            payments=TracedPaymentGateway(payments, tracer),
            notifier=TracedNotifier(notifier(settings), tracer),
            clock=SystemClock(),
            ids=Uuid7Ids(),
        )


def observe(settings: Settings) -> None:
    configure_logging(as_json=settings.log_json)
    configure_tracing(to_console=settings.trace_to_console)


def create_http_app() -> FastAPI:
    """uvicorn --factory roombook.composition:create_http_app"""
    settings = Settings()
    observe(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[State]:
        async with (
            database(settings) as sessions,
            roombook(settings, sessions) as use_cases,
        ):
            yield {"use_cases": use_cases}

    return create_app(lifespan)


def main(argv: Sequence[str] | None = None) -> int:
    """The `roombook` command."""
    args = build_parser().parse_args(argv)
    settings = Settings()
    observe(settings)

    async def run_command() -> int:
        async with (
            database(settings) as sessions,
            roombook(settings, sessions) as use_cases,
        ):
            return await run(args, use_cases)

    return asyncio.run(run_command())


def run_consumer() -> None:
    """The `roombook-consumer` command."""
    settings = Settings()
    observe(settings)

    async def consume() -> None:
        async with (
            database(settings) as sessions,
            roombook(settings, sessions) as use_cases,
        ):
            consumer = TillpointConsumer(
                use_cases.confirm_booking,
                SqlAlchemyProcessedMessages(sessions),
            )
            broker = KafkaBroker(settings.kafka_servers)
            broker.include_router(tillpoint_router(consumer))
            await FastStream(broker).run()

    asyncio.run(consume())


def run_relay() -> None:
    """The `roombook-relay` command."""
    settings = Settings()
    observe(settings)

    async def relay() -> None:
        broker = KafkaBroker(settings.kafka_servers)
        async with database(settings) as sessions, broker:
            outbox = OutboxRelay(sessions, kafka_publisher(broker))
            await outbox.run(idle=timedelta(seconds=1))

    asyncio.run(relay())
