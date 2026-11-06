from dataclasses import dataclass
from enum import StrEnum

type BookingId = str
type PaymentId = str


class BookingNotFound(Exception):
    pass


class IllegalTransition(Exception):
    pass


class PaymentDeclined(Exception):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class Money:
    amount: int  # minor units
    currency: str


class BookingStatus(StrEnum):
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


@dataclass(slots=True, kw_only=True)
class Booking:
    id: BookingId
    price: Money
    status: BookingStatus = BookingStatus.HELD
    payment_id: PaymentId | None = None

    @property
    def can_confirm(self) -> bool:
        return self.status is BookingStatus.HELD

    def confirm(self, payment_id: PaymentId) -> None:
        if not self.can_confirm:
            raise IllegalTransition(f"booking is {self.status}")
        self.status = BookingStatus.CONFIRMED
        self.payment_id = payment_id
