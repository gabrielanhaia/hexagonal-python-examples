"""The Coinwren consumer on FastStream's in-memory Kafka."""

from typing import Any

import pytest
from faststream.kafka import KafkaBroker, TestKafkaBroker

from roombook.adapters.inbound.messaging.coinwren import (
    DEAD_LETTER_TOPIC,
    PAYMENTS_TOPIC,
    CoinwrenConsumer,
    coinwren_router,
)
from roombook.adapters.outbound.memory.fakes import (
    FakePaymentGateway,
    FixedClock,
    InMemoryProcessedMessages,
    RecordingNotifier,
    SequentialIds,
)
from roombook.adapters.outbound.memory.unit_of_work import (
    InMemoryStore,
)
from roombook.application.confirm_booking import ConfirmBooking
from roombook.application.hold_room import HoldRoom, HoldRoomCommand
from roombook.domain.booking import BookingStatus
from roombook.domain.ids import BookingId, RoomId
from tests.support import ADA, NOW, at, atlas


def payment_succeeded(
    booking_id: str, event_id: str = "evt_1"
) -> dict[str, Any]:
    return {
        "id": event_id,
        "type": "payment.succeeded",
        "data": {"payment_id": "pay_1", "reference": booking_id},
    }


class Harness:
    def __init__(self) -> None:
        room = atlas()
        self.store = InMemoryStore(rooms={room.id: room})
        self.notifier = RecordingNotifier()
        self.dead_letters: list[object] = []
        clock = FixedClock(NOW)
        self.hold_room = HoldRoom(
            unit_of_work=self.store.unit_of_work,
            payments=FakePaymentGateway(),
            clock=clock,
            ids=SequentialIds(),
        )
        consumer = CoinwrenConsumer(
            ConfirmBooking(
                unit_of_work=self.store.unit_of_work,
                notifier=self.notifier,
                clock=clock,
            ),
            InMemoryProcessedMessages(),
        )
        self.broker = KafkaBroker()
        self.broker.include_router(coinwren_router(consumer))

        @self.broker.subscriber(DEAD_LETTER_TOPIC)
        async def dead_letter(body: object) -> None:
            self.dead_letters.append(body)

    async def hold(self) -> BookingId:
        receipt = await self.hold_room(
            HoldRoomCommand(
                room_id=RoomId("atlas"),
                member_id=ADA,
                start=at("10:00"),
                end=at("11:00"),
            )
        )
        return receipt.booking_id


@pytest.fixture
def harness() -> Harness:
    return Harness()


async def test_a_payment_confirms_the_held_booking(
    harness: Harness,
) -> None:
    booking_id = await harness.hold()

    async with TestKafkaBroker(harness.broker) as broker:
        await broker.publish(
            payment_succeeded(booking_id), PAYMENTS_TOPIC
        )

    booking = harness.store.bookings[booking_id]
    assert booking.status is BookingStatus.CONFIRMED
    assert booking.payment_id == "pay_1"


async def test_a_redelivered_event_is_applied_once(
    harness: Harness,
) -> None:
    booking_id = await harness.hold()

    async with TestKafkaBroker(harness.broker) as broker:
        for _ in range(2):
            await broker.publish(
                payment_succeeded(booking_id), PAYMENTS_TOPIC
            )

    assert len(harness.notifier.sent) == 1


@pytest.mark.parametrize(
    "event",
    [
        payment_succeeded("no-such-booking"),
        {"id": "evt_2", "type": "payment.succeeded", "data": {}},
        {"unexpected": "shape"},
    ],
)
async def test_events_that_can_never_succeed_are_dead_lettered(
    harness: Harness, event: dict[str, Any]
) -> None:
    async with TestKafkaBroker(harness.broker) as broker:
        await broker.publish(event, PAYMENTS_TOPIC)

    assert harness.dead_letters == [event]
