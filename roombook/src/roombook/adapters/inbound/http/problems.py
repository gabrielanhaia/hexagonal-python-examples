"""Domain errors as RFC 9457 problem details."""

from dataclasses import dataclass

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

from roombook.application.ports import PaymentUnavailable
from roombook.domain.errors import (
    BookingError,
    BookingNotFound,
    IllegalTransition,
    InvalidTimeSlot,
    OutsideOpeningHours,
    RoomNotFound,
    SlotUnavailable,
)

PROBLEM_TYPE_BASE = "https://roombook.example/problems/"
# The client's detail when no booking rule refused: the cause
# names infrastructure, so it stays in the log.
OPAQUE_DETAIL = (
    "Try again later. If you report this, quote the"
    " X-Correlation-ID response header."
)

log = structlog.get_logger()


@dataclass(frozen=True, slots=True)
class Problem:
    status: int
    slug: str
    title: str


PROBLEMS: dict[type[Exception], Problem] = {
    InvalidTimeSlot: Problem(
        422, "invalid-time-slot", "Invalid slot"
    ),
    OutsideOpeningHours: Problem(
        422, "outside-opening-hours", "Room is closed then"
    ),
    RoomNotFound: Problem(404, "room-not-found", "No such room"),
    BookingNotFound: Problem(
        404, "booking-not-found", "No such booking"
    ),
    SlotUnavailable: Problem(
        409, "slot-unavailable", "Slot unavailable"
    ),
    IllegalTransition: Problem(
        409, "illegal-transition", "Not allowed in this status"
    ),
    PaymentUnavailable: Problem(
        503, "payment-unavailable", "Payments are unavailable"
    ),
}


async def problem_response(
    request: Request, error: Exception
) -> JSONResponse:
    problem = PROBLEMS[type(error)]
    if isinstance(error, BookingError):
        detail = str(error)
        await log.ainfo("request refused", problem=problem.slug)
    else:
        detail = OPAQUE_DETAIL
        await log.aerror(
            "request failed", problem=problem.slug, cause=str(error)
        )
    return JSONResponse(
        {
            "type": PROBLEM_TYPE_BASE + problem.slug,
            "title": problem.title,
            "status": problem.status,
            "detail": detail,
            "instance": request.url.path,
        },
        status_code=problem.status,
        media_type="application/problem+json",
    )
