from datetime import UTC, datetime

import pytest

import abc_port
import protocol_port
import runtime_checkable_trap as trap

START = datetime(2026, 11, 10, 10, 0, tzinfo=UTC)
NOW = datetime(2026, 11, 9, 9, 0, tzinfo=UTC)


def test_a_protocol_adapter_needs_no_base_class() -> None:
    clock = protocol_port.FixedClock(NOW)

    assert protocol_port.Clock not in type(clock).__mro__
    assert protocol_port.cancellation_is_free(START, clock)


def test_an_abc_adapter_must_inherit() -> None:
    clock = abc_port.FixedClock(NOW)

    assert isinstance(clock, abc_port.Clock)
    assert abc_port.cancellation_is_free(START, clock)


def test_an_abc_refuses_an_incomplete_adapter() -> None:
    with pytest.raises(TypeError, match="abstract method"):
        abc_port.ForgetfulClock()  # type: ignore[abstract]


def test_runtime_checkable_checks_presence_only() -> None:
    assert isinstance(trap.TextClock(), trap.Clock)
    assert not isinstance(trap.NoClock(), trap.Clock)


def test_the_wrong_clock_fails_later_at_runtime() -> None:
    clock = trap.load_clock(trap.TextClock())

    with pytest.raises(AttributeError):
        clock.now().isoformat()
