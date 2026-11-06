from typing import Any

import pytest
from faststream.kafka import (
    ConsumerRecord,
    KafkaBroker,
    KafkaMessage,
    TestKafkaBroker,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from roombook.adapters.outbound.memory.fakes import (
    FakePaymentGateway,
    FixedClock,
)
from roombook.adapters.outbound.outbox.messages import (
    BOOKINGS_TOPIC,
)
from roombook.adapters.outbound.outbox.relay import (
    OutboxRelay,
    kafka_publisher,
)
from roombook.adapters.outbound.sqlalchemy.mappers import (
    room_to_record,
)
from roombook.adapters.outbound.sqlalchemy.records import (
    OutboxRecord,
)
from roombook.adapters.outbound.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from roombook.adapters.outbound.system import Uuid7Ids
from roombook.application.hold_room import HoldRoom, HoldRoomCommand
from roombook.domain.ids import BookingId, RoomId
from tests.support import ADA, NOW, at, atlas

type Sessions = async_sessionmaker[AsyncSession]


class RecordingPublisher:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def __call__(self, record: OutboxRecord) -> None:
        self.sent.append((record.topic, record.key, record.type))


async def hold_atlas(sessions: Sessions) -> BookingId:
    async with sessions.begin() as session:
        session.add(room_to_record(atlas()))
    hold_room = HoldRoom(
        unit_of_work=lambda: SqlAlchemyUnitOfWork(sessions),
        payments=FakePaymentGateway(),
        clock=FixedClock(NOW),
        ids=Uuid7Ids(),
    )
    receipt = await hold_room(
        HoldRoomCommand(
            room_id=RoomId("atlas"),
            member_id=ADA,
            start=at("10:00"),
            end=at("11:00"),
        )
    )
    return receipt.booking_id


@pytest.mark.postgres
async def test_each_committed_event_is_relayed_once(
    sessions: Sessions,
) -> None:
    booking_id = await hold_atlas(sessions)
    publish = RecordingPublisher()
    relay = OutboxRelay(sessions, publish)

    assert await relay.relay_batch() == 1
    assert await relay.relay_batch() == 0
    assert publish.sent == [
        (BOOKINGS_TOPIC, booking_id, "BookingHeld")
    ]


@pytest.mark.postgres
async def test_a_failed_publish_leaves_the_row_for_next_time(
    sessions: Sessions,
) -> None:
    await hold_atlas(sessions)

    async def broker_down(record: OutboxRecord) -> None:
        raise ConnectionError("broker unreachable")

    with pytest.raises(ConnectionError):
        await OutboxRelay(sessions, broker_down).relay_batch()
    relay = OutboxRelay(sessions, RecordingPublisher())
    assert await relay.relay_batch() == 1


async def test_the_kafka_publisher_sends_key_and_headers() -> None:
    broker = KafkaBroker()
    received: list[tuple[Any, bytes | None, dict[str, Any]]] = []

    @broker.subscriber(BOOKINGS_TOPIC)
    async def listen(body: object, message: KafkaMessage) -> None:
        record = message.raw_message
        assert isinstance(record, ConsumerRecord)
        received.append((body, record.key, dict(message.headers)))

    record = OutboxRecord(
        id=7,
        topic=BOOKINGS_TOPIC,
        key="b-1",
        type="BookingHeld",
        payload={"booking_id": "b-1"},
    )
    async with TestKafkaBroker(broker):
        await kafka_publisher(broker)(record)

    [(body, key, headers)] = received
    assert body == {"booking_id": "b-1"}
    assert key == b"b-1"
    assert headers["message-id"] == "7"
    assert headers["event-type"] == "BookingHeld"
