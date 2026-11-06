"""mypy rejects this file; that is the point.

    uv run mypy wrong_adapter.py

It is left out of the default mypy run in pyproject.toml.
The recorded output is in docs/outputs/ch03/mypy-caught.txt.
"""

from datetime import UTC, datetime

from protocol_port import cancellation_is_free


class TextClock:
    def now(self) -> str:
        return "09:00"


start = datetime(2026, 11, 10, 10, 0, tzinfo=UTC)
cancellation_is_free(start, TextClock())
