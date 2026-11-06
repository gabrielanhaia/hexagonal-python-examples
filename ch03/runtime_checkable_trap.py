"""@runtime_checkable checks that members exist, not their types."""

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...


class TextClock:
    """Has a now() method, so isinstance() accepts it."""

    def now(self) -> str:
        return "09:00"


class NoClock:
    pass


def load_clock(candidate: object) -> Clock:
    if not isinstance(candidate, Clock):
        raise TypeError(f"{type(candidate).__name__} is no Clock")
    return candidate


if __name__ == "__main__":
    print(
        "TextClock passes isinstance:",
        isinstance(TextClock(), Clock),
    )
    print(
        "NoClock passes isinstance:", isinstance(NoClock(), Clock)
    )
    clock = load_clock(TextClock())
    try:
        clock.now().isoformat()
    except AttributeError as error:
        print("AttributeError:", error)
