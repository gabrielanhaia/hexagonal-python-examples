"""A span of time: aware and ordered."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TimeSlot:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.utcoffset() is None:
            raise ValueError("a slot needs a time zone")
        if self.start >= self.end:
            raise ValueError("start must come before end")

    def __str__(self) -> str:
        return f"{self.start.isoformat()}/{self.end.isoformat()}"

    def overlaps(self, other: TimeSlot) -> bool:
        return self.start < other.end and other.start < self.end
