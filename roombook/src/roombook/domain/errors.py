"""The rules the domain refuses to break, as exceptions."""


class BookingError(Exception):
    """Base class: a request the booking rules refuse."""


class InvalidTimeSlot(BookingError):
    """The start and end do not make a bookable slot."""


class OutsideOpeningHours(BookingError):
    """The slot falls outside the room's opening hours."""


class SlotUnavailable(BookingError):
    """Another active booking already holds the slot."""


class RoomNotFound(BookingError):
    """No room has this id."""


class BookingNotFound(BookingError):
    """No booking with this id belongs to the requester."""


class IllegalTransition(BookingError):
    """The booking's status does not allow the action."""
