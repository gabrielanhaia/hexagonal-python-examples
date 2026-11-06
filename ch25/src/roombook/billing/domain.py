from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class Invoice:
    id: str
    member_id: str
    booking_id: str
    amount: int  # minor units
    currency: str
    reason: str
