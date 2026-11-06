from datetime import timedelta

import pytest

from roombook.domain.cancellation import cancellation_terms
from roombook.domain.money import Money
from tests.support import at

PAID = Money(4000, "EUR")
STARTS = at("10:00")


@pytest.mark.parametrize(
    "notice", [timedelta(hours=24), timedelta(days=3)]
)
def test_cancelling_with_a_days_notice_is_free(
    notice: timedelta,
) -> None:
    terms = cancellation_terms(PAID, STARTS, STARTS - notice)
    assert terms.fee == Money(0, "EUR")
    assert terms.refund == PAID


def test_cancelling_late_costs_half() -> None:
    late = STARTS - timedelta(hours=23, minutes=59)
    terms = cancellation_terms(PAID, STARTS, late)
    assert terms.fee == Money(2000, "EUR")
    assert terms.refund == Money(2000, "EUR")
