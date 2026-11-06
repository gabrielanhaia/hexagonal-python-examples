"""The cancellation policy: free with notice, half without."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from fractions import Fraction

from roombook.domain.money import Money

FREE_CANCELLATION_NOTICE = timedelta(hours=24)
LATE_CANCELLATION_FEE = Fraction(1, 2)


@dataclass(frozen=True, slots=True)
class CancellationTerms:
    fee: Money
    refund: Money


def cancellation_terms(
    paid: Money, starts_at: datetime, cancelled_at: datetime
) -> CancellationTerms:
    """What a member pays to cancel, and what comes back."""
    if starts_at - cancelled_at >= FREE_CANCELLATION_NOTICE:
        fee = Money.zero(paid.currency)
    else:
        fee = paid.scaled(LATE_CANCELLATION_FEE)
    return CancellationTerms(fee=fee, refund=paid - fee)
