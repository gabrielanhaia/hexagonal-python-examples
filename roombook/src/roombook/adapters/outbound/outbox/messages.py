"""Domain events as outbox messages: topic, key, JSON body."""

from dataclasses import asdict, dataclass
from datetime import datetime

from roombook.domain.events import BookingEvent

BOOKINGS_TOPIC = "roombook.bookings"

type Json = (
    str | int | float | bool | list[Json] | dict[str, Json] | None
)


@dataclass(frozen=True, slots=True, kw_only=True)
class OutboxMessage:
    topic: str
    key: str
    type: str
    payload: dict[str, Json]
    occurred_at: datetime


def to_message(event: BookingEvent) -> OutboxMessage:
    return OutboxMessage(
        topic=BOOKINGS_TOPIC,
        key=event.booking_id,
        type=type(event).__name__,
        payload=_json_object(asdict(event)),
        occurred_at=event.occurred_at,
    )


def _json_object(fields: dict[str, object]) -> dict[str, Json]:
    return {name: _json(value) for name, value in fields.items()}


def _json(value: object) -> Json:
    match value:
        case dict():
            return {str(k): _json(v) for k, v in value.items()}
        case datetime():
            return value.isoformat()
        case str() | int() | float() | bool() | None:
            return value
        case _:
            raise TypeError(f"no JSON form for {value!r}")
