"""Consume Coinwren payment events; confirm paid bookings."""

from typing import Any, Protocol

import structlog
from faststream import AckPolicy
from faststream.kafka import KafkaRouter
from pydantic import BaseModel, ValidationError

from roombook.application.confirm_booking import (
    ConfirmBooking,
    ConfirmBookingCommand,
)
from roombook.domain.errors import BookingError
from roombook.domain.ids import BookingId

PAYMENTS_TOPIC = "coinwren.payments"
DEAD_LETTER_TOPIC = "coinwren.payments.dead-letter"
CONSUMER_GROUP = "roombook"

log = structlog.get_logger()


class CoinwrenEvent(BaseModel):
    id: str
    type: str
    data: dict[str, Any]


class PaymentSucceeded(BaseModel):
    payment_id: str
    reference: str


class ProcessedMessages(Protocol):
    """The consumer's own port: which messages it has handled."""

    async def seen(self, message_id: str) -> bool: ...

    async def remember(self, message_id: str) -> None: ...


class CoinwrenConsumer:
    """Idempotent: a redelivered event is skipped."""

    def __init__(
        self,
        confirm_booking: ConfirmBooking,
        processed: ProcessedMessages,
    ) -> None:
        self._confirm_booking = confirm_booking
        self._processed = processed

    async def handle(self, body: object) -> None:
        event = CoinwrenEvent.model_validate(body)
        if event.type != "payment.succeeded":
            return
        if await self._processed.seen(event.id):
            await log.ainfo("duplicate skipped", event_id=event.id)
            return
        payment = PaymentSucceeded.model_validate(event.data)
        await self._confirm_booking(
            ConfirmBookingCommand(
                booking_id=BookingId(payment.reference),
                payment_id=payment.payment_id,
            )
        )
        await self._processed.remember(event.id)
        await log.ainfo("payment applied", event_id=event.id)


PERMANENT_FAILURES = (ValidationError, BookingError)


def coinwren_router(consumer: CoinwrenConsumer) -> KafkaRouter:
    """Retry what may heal; dead-letter what never will."""
    router = KafkaRouter()
    dead_letters = router.publisher(DEAD_LETTER_TOPIC)

    @router.subscriber(
        PAYMENTS_TOPIC,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
        ack_policy=AckPolicy.NACK_ON_ERROR,
    )
    async def on_payment_event(body: object) -> None:
        try:
            await consumer.handle(body)
        except PERMANENT_FAILURES as error:
            await log.awarning("dead-lettered", error=str(error))
            await dead_letters.publish(
                body, headers={"x-error": type(error).__name__}
            )

    return router
