class DomainError(Exception):
    """A booking rule said no."""


class InvalidTimeSlot(DomainError):
    pass


class OutsideOpeningHours(DomainError):
    pass


class SlotUnavailable(DomainError):
    pass


class IllegalTransition(DomainError):
    pass


class HoldExpired(DomainError):
    pass


class RoomNotFound(DomainError):
    pass


class BookingNotFound(DomainError):
    pass


class PaymentDeclined(DomainError):
    pass
