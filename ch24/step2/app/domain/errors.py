class DomainError(Exception):
    """A booking rule said no."""


class InvalidTimeSlot(DomainError):
    pass
