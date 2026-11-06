class BookingError(Exception):
    """A booking rule said no."""


class InvalidBooking(BookingError):
    pass


class InvalidTimeSlot(InvalidBooking):
    pass


class OutsideOpeningHours(InvalidBooking):
    pass


class SlotUnavailable(BookingError):
    pass


class IllegalTransition(BookingError):
    pass


class RoomNotFound(BookingError):
    pass


class BookingNotFound(BookingError):
    pass


class BookingTooLong(InvalidBooking):
    pass
