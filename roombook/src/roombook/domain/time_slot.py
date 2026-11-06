"""A bookable span of time: aware, aligned, ordered."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from roombook.domain.errors import InvalidTimeSlot

GRANULARITY = timedelta(minutes=15)
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class TimeSlot:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if not (_is_aware(self.start) and _is_aware(self.end)):
            raise InvalidTimeSlot("start and end need a time zone")
        if self.start >= self.end:
            raise InvalidTimeSlot("start must come before end")
        if not (_on_grid(self.start) and _on_grid(self.end)):
            raise InvalidTimeSlot(
                "start and end must fall on 15-minute marks"
            )

    def __str__(self) -> str:
        return f"{self.start.isoformat()}/{self.end.isoformat()}"

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def overlaps(self, other: TimeSlot) -> bool:
        return self.start < other.end and other.start < self.end

    def contains(self, other: TimeSlot) -> bool:
        return self.start <= other.start and other.end <= self.end


def _is_aware(moment: datetime) -> bool:
    return moment.utcoffset() is not None


def _on_grid(moment: datetime) -> bool:
    return (moment - _EPOCH) % GRANULARITY == timedelta(0)
