"""The tracing decorators record spans; the ports never know."""

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from roombook.adapters.outbound.memory.fakes import (
    FakePaymentGateway,
    RecordingNotifier,
)
from roombook.adapters.outbound.observability.tracing import (
    TracedNotifier,
    TracedPaymentGateway,
)
from roombook.domain.ids import BookingId
from roombook.domain.money import Money


def tracer_and_spans() -> tuple[
    TracerProvider, InMemorySpanExporter
]:
    spans = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(spans))
    return provider, spans


async def test_a_checkout_is_wrapped_in_a_span() -> None:
    provider, spans = tracer_and_spans()
    payments = TracedPaymentGateway(
        FakePaymentGateway(), provider.get_tracer("test")
    )

    await payments.start_checkout(BookingId("b-1"), Money(1, "EUR"))

    [span] = spans.get_finished_spans()
    assert span.name == "PaymentGateway.start_checkout"
    assert span.attributes == {"roombook.booking_id": "b-1"}


async def test_the_wrapped_notifier_still_delivers() -> None:
    provider, spans = tracer_and_spans()
    inner = RecordingNotifier()
    notifier = TracedNotifier(inner, provider.get_tracer("test"))

    await notifier.notify([])

    [span] = spans.get_finished_spans()
    assert span.name == "Notifier.notify"
    assert inner.sent == []
