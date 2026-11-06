"""The published language between contexts: plain, frozen facts.

Both contexts may import this module; neither may import the
other.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class BookingCancelled:
    booking_id: str
    member_id: str
    fee_amount: int  # minor units
    currency: str
    occurred_at: datetime
