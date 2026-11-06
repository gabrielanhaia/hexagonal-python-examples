"""The same object graph, declared for dishka instead.

uvicorn --factory roombook.composition_dishka:create_http_app
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka import (
    AsyncContainer,
    Provider,
    Scope,
    decorate,
    from_context,
    make_async_container,
    provide,
    provide_all,
)
from fastapi import FastAPI
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from roombook.adapters.inbound.http.app import State, create_app
from roombook.adapters.outbound.observability.tracing import (
    TracedNotifier,
    TracedPaymentGateway,
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
from roombook.composition import (
    Roombook,
    database,
    notifier,
    observe,
    payment_gateway,
)
from roombook.settings import Settings


class Infrastructure(Provider):
    scope = Scope.APP

    settings = from_context(provides=Settings)
    clock = provide(SystemClock, provides=Clock)
    ids = provide(Uuid7Ids, provides=IdGenerator)

    @provide
    async def sessions(
        self, settings: Settings
    ) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
        async with database(settings) as sessions:
            yield sessions

    @provide
    def unit_of_work(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> UnitOfWorkFactory:
        def new_unit_of_work() -> UnitOfWork:
            return SqlAlchemyUnitOfWork(sessions)

        return new_unit_of_work

    @provide
    async def payments(
        self, settings: Settings
    ) -> AsyncIterator[PaymentGateway]:
        async with payment_gateway(settings) as gateway:
            yield gateway

    @provide
    def notifier(self, settings: Settings) -> Notifier:
        return notifier(settings)


class Tracing(Provider):
    scope = Scope.APP

    @decorate
    def trace_payments(
        self, payments: PaymentGateway
    ) -> PaymentGateway:
        return TracedPaymentGateway(
            payments, trace.get_tracer("roombook")
        )

    @decorate
    def trace_notifier(self, notifier: Notifier) -> Notifier:
        return TracedNotifier(
            notifier, trace.get_tracer("roombook")
        )


class Application(Provider):
    scope = Scope.APP

    use_cases = provide_all(
        HoldRoom,
        ConfirmBooking,
        CancelBooking,
        ListAvailability,
        ExpireStaleHolds,
        Roombook,
    )


def make_roombook_container(settings: Settings) -> AsyncContainer:
    return make_async_container(
        Infrastructure(),
        Tracing(),
        Application(),
        context={Settings: settings},
    )


def create_http_app() -> FastAPI:
    settings = Settings()
    observe(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[State]:
        container = make_roombook_container(settings)
        try:
            yield {"use_cases": await container.get(Roombook)}
        finally:
            await container.close()

    return create_app(lifespan)
