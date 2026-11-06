from datetime import datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from roombook.domain.errors import InvalidTimeSlot
from roombook.domain.time_slot import GRANULARITY, TimeSlot
from tests.support import at, slot

DAY_START = at("00:00")
QUARTERS_PER_WEEK = 4 * 24 * 7


@st.composite
def slots(draw: st.DrawFn) -> TimeSlot:
    first = draw(st.integers(0, QUARTERS_PER_WEEK))
    length = draw(st.integers(1, 4 * 12))
    return TimeSlot(
        DAY_START + first * GRANULARITY,
        DAY_START + (first + length) * GRANULARITY,
    )


def test_needs_a_time_zone() -> None:
    naive = datetime(2026, 12, 1, 10, 0)  # noqa: DTZ001
    with pytest.raises(InvalidTimeSlot, match="time zone"):
        TimeSlot(naive, at("11:00"))


def test_start_must_come_before_end() -> None:
    with pytest.raises(InvalidTimeSlot, match="before end"):
        slot("11:00", "10:00")


def test_times_must_fall_on_quarter_hours() -> None:
    with pytest.raises(InvalidTimeSlot, match="15-minute"):
        slot("10:00", "10:20")


def test_back_to_back_slots_do_not_overlap() -> None:
    first = slot("09:00", "10:00")
    second = slot("10:00", "11:00")
    assert not first.overlaps(second)


@given(slots(), slots())
def test_overlap_is_symmetric(a: TimeSlot, b: TimeSlot) -> None:
    assert a.overlaps(b) == b.overlaps(a)


@given(slots())
def test_a_slot_overlaps_itself(a: TimeSlot) -> None:
    assert a.overlaps(a)


@given(slots(), slots())
def test_containing_implies_overlapping(
    a: TimeSlot, b: TimeSlot
) -> None:
    if a.contains(b):
        assert a.overlaps(b)
