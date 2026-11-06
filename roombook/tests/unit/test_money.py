from fractions import Fraction

import pytest

from roombook.domain.money import Money


def test_adds_amounts_in_the_same_currency() -> None:
    total = Money(1050, "EUR") + Money(250, "EUR")
    assert total == Money(1300, "EUR")


def test_refuses_to_mix_currencies() -> None:
    with pytest.raises(ValueError, match="cannot mix EUR and GBP"):
        Money(100, "EUR") + Money(100, "GBP")


@pytest.mark.parametrize("code", ["eur", "EURO", "E1R", ""])
def test_rejects_codes_that_are_not_iso_4217(code: str) -> None:
    with pytest.raises(ValueError, match="not an ISO 4217 code"):
        Money(100, code)


@pytest.mark.parametrize(
    ("amount", "expected"), [(25, 12), (35, 18), (4000, 2000)]
)
def test_halving_rounds_half_to_even(
    amount: int, expected: int
) -> None:
    half = Money(amount, "EUR").scaled(Fraction(1, 2))
    assert half == Money(expected, "EUR")


def test_prints_with_two_decimal_places() -> None:
    assert str(Money(4005, "EUR")) == "EUR 40.05"
