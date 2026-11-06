"""A driven port as a Protocol: adapters never import it."""

from datetime import UTC, datetime, timedelta
from typing import Protocol

FREE_CANCELLATION_NOTICE = timedelta(hours=24)


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:  # no base class: it matches by shape
    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment


def cancellation_is_free(start: datetime, clock: Clock) -> bool:
    return start - clock.now() >= FREE_CANCELLATION_NOTICE


if __name__ == "__main__":
    start = datetime(2026, 11, 10, 10, 0, tzinfo=UTC)
    clock = FixedClock(datetime(2026, 11, 9, 9, 0, tzinfo=UTC))
    print("free:", cancellation_is_free(start, clock))
    print(
        "Clock in FixedClock's bases:", Clock in FixedClock.__mro__
    )
