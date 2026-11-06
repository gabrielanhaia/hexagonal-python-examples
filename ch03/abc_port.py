"""The same port as an ABC: every adapter must inherit from it."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta

FREE_CANCELLATION_NOTICE = timedelta(hours=24)


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime: ...


class SystemClock(Clock):  # the adapter imports the core
    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock(Clock):
    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment


class ForgetfulClock(Clock):  # forgot to implement now()
    pass


def cancellation_is_free(start: datetime, clock: Clock) -> bool:
    return start - clock.now() >= FREE_CANCELLATION_NOTICE


if __name__ == "__main__":
    start = datetime(2026, 11, 10, 10, 0, tzinfo=UTC)
    clock = FixedClock(datetime(2026, 11, 9, 9, 0, tzinfo=UTC))
    print("free:", cancellation_is_free(start, clock))
    try:  # mypy rejects the next line too, hence the ignore
        ForgetfulClock()  # type: ignore[abstract]
    except TypeError as error:
        print("TypeError:", error)
