"""Tracing set up at the edge, and decorators around ports."""

from collections.abc import Sequence

from opentelemetry import trace
from opentelemetry.instrumentation.sqlalchemy import (
    SQLAlchemyInstrumentor,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.trace import Tracer
from sqlalchemy.ext.asyncio import AsyncEngine

from roombook.application.ports import (
    Checkout,
    Notifier,
    PaymentGateway,
)
from roombook.domain.events import BookingEvent
from roombook.domain.ids import BookingId
from roombook.domain.money import Money


def configure_tracing(*, to_console: bool) -> TracerProvider:
    """Install the global provider FastAPI's tracing reads."""
    provider = TracerProvider(
        resource=Resource.create({"service.name": "roombook"})
    )
    if to_console:
        provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )
    trace.set_tracer_provider(provider)
    return provider


def instrument_engine(engine: AsyncEngine) -> None:
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


class TracedPaymentGateway:
    """A PaymentGateway that records a span around each call."""

    def __init__(
        self, inner: PaymentGateway, tracer: Tracer
    ) -> None:
        self._inner = inner
        self._tracer = tracer

    async def start_checkout(
        self, booking_id: BookingId, amount: Money
    ) -> Checkout:
        with self._tracer.start_as_current_span(
            "PaymentGateway.start_checkout"
        ) as span:
            span.set_attribute("roombook.booking_id", booking_id)
            return await self._inner.start_checkout(
                booking_id, amount
            )


class TracedNotifier:
    """A Notifier that records a span around each call."""

    def __init__(self, inner: Notifier, tracer: Tracer) -> None:
        self._inner = inner
        self._tracer = tracer

    async def notify(self, events: Sequence[BookingEvent]) -> None:
        with self._tracer.start_as_current_span(
            "Notifier.notify"
        ) as span:
            span.set_attribute("roombook.event_count", len(events))
            await self._inner.notify(events)
