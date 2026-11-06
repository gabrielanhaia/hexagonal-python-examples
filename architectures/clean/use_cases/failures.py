from dataclasses import dataclass
from enum import StrEnum

from entities.errors import (
    BookingNotFound,
    DomainError,
    IllegalTransition,
    RoomNotFound,
    SlotUnavailable,
)


class FailureKind(StrEnum):
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True, kw_only=True)
class Failure:
    kind: FailureKind
    message: str


def failure_from(error: DomainError) -> Failure:
    match error:
        case RoomNotFound() | BookingNotFound():
            kind = FailureKind.NOT_FOUND
        case SlotUnavailable() | IllegalTransition():
            kind = FailureKind.CONFLICT
        case _:
            kind = FailureKind.REJECTED
    return Failure(kind=kind, message=str(error))
