from datetime import date

import pytest

from roombook.domain.errors import OutsideOpeningHours
from roombook.domain.money import Money
from tests.support import at, atlas, slot


def test_charges_the_hourly_rate_per_quarter_hour() -> None:
    price = atlas().price_for(slot("10:00", "11:30"))
    assert price == Money(6000, "EUR")


def test_accepts_a_slot_from_opening_to_closing() -> None:
    atlas().check_open(slot("08:00", "20:00"))


@pytest.mark.parametrize(
    ("start", "end"), [("07:45", "09:00"), ("19:00", "20:15")]
)
def test_refuses_a_slot_outside_opening_hours(
    start: str, end: str
) -> None:
    with pytest.raises(OutsideOpeningHours, match="08:00-20:00"):
        atlas().check_open(slot(start, end))


def test_opening_hours_follow_the_rooms_local_clock() -> None:
    summer = atlas().opening_hours.on(date(2026, 7, 1))
    assert summer.start == at("07:00", day="2026-07-01")
