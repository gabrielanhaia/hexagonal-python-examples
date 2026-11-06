"""What the Room aggregate refuses to do."""


class BlackoutOverlaps(Exception):
    """Two maintenance windows on one room may not overlap."""


class UnknownBlackout(Exception):
    """The room has no blackout period with that id."""


class RoomBlackedOut(Exception):
    """The room is closed for maintenance during that slot."""
