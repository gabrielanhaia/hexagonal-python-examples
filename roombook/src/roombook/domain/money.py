"""Money in integer minor units. Never a float."""

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class Money:
    amount: int
    currency: str

    def __post_init__(self) -> None:
        code = self.currency
        if len(code) != 3 or not (
            code.isalpha() and code.isupper()
        ):
            raise ValueError(f"not an ISO 4217 code: {code!r}")

    def __str__(self) -> str:
        """Two decimal places: every roombook currency has cents."""
        units, cents = divmod(self.amount, 100)
        return f"{self.currency} {units}.{cents:02d}"

    @classmethod
    def zero(cls, currency: str) -> Money:
        return cls(0, currency)

    def __add__(self, other: Money) -> Money:
        self._require_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._require_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def scaled(self, factor: Fraction) -> Money:
        """Multiply, rounding half to even to the minor unit."""
        return Money(round(self.amount * factor), self.currency)

    def _require_same_currency(self, other: Money) -> None:
        if other.currency != self.currency:
            raise ValueError(
                f"cannot mix {self.currency} and {other.currency}"
            )
