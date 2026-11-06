from hypothesis import given
from hypothesis import strategies as st

from roombook.domain.availability import free_slots
from roombook.domain.time_slot import GRANULARITY, TimeSlot
from tests.support import slot

WINDOW = slot("08:00", "20:00")
QUARTERS = int(WINDOW.duration / GRANULARITY)


def quarter(index: int) -> TimeSlot:
    start = WINDOW.start + index * GRANULARITY
    return TimeSlot(start, start + GRANULARITY)


@st.composite
def taken_slots(draw: st.DrawFn) -> list[TimeSlot]:
    starts = draw(
        st.sets(st.integers(0, QUARTERS - 1), max_size=12)
    )
    return [quarter(index) for index in sorted(starts)]


def test_an_empty_day_is_one_free_slot() -> None:
    assert free_slots(WINDOW, []) == [WINDOW]


def test_bookings_cut_the_day_into_gaps() -> None:
    taken = [slot("10:00", "11:00"), slot("13:00", "14:30")]
    assert free_slots(WINDOW, taken) == [
        slot("08:00", "10:00"),
        slot("11:00", "13:00"),
        slot("14:30", "20:00"),
    ]


def test_a_fully_booked_day_has_no_free_slots() -> None:
    assert free_slots(WINDOW, [WINDOW]) == []


@given(taken_slots())
def test_every_quarter_is_free_or_taken_never_both(
    taken: list[TimeSlot],
) -> None:
    free = free_slots(WINDOW, taken)
    for index in range(QUARTERS):
        q = quarter(index)
        is_free = any(gap.contains(q) for gap in free)
        is_taken = any(t.overlaps(q) for t in taken)
        assert is_free != is_taken
