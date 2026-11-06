class DomainError(Exception):
    """A booking rule said no."""


class InvalidBooking(DomainError):
    """The request breaks a rule about the booking itself."""


class InvalidTimeSlot(InvalidBooking):
    pass


class OutsideOpeningHours(InvalidBooking):
    pass


class SlotUnavailable(DomainError):
    pass


class IllegalTransition(DomainError):
    pass


class RoomNotFound(DomainError):
    pass


class BookingNotFound(DomainError):
    pass
