from datetime import datetime, timedelta
from fractions import Fraction

from app.domain.values import Money

HOLD_TTL = timedelta(minutes=15)
FREE_CANCELLATION_NOTICE = timedelta(hours=24)
LATE_CANCELLATION_FEE = Fraction(1, 2)


def hold_cutoff(now: datetime) -> datetime:
    """Holds created before this moment have expired."""
    return now - HOLD_TTL


def hold_expired(created_at: datetime, now: datetime) -> bool:
    return created_at < hold_cutoff(now)


def cancellation_fee(
    price: Money, start: datetime, now: datetime
) -> Money:
    if start - now >= FREE_CANCELLATION_NOTICE:
        return price.times(Fraction(0))
    return price.times(LATE_CANCELLATION_FEE)
