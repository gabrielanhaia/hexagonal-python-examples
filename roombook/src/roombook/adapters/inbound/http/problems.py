"""Domain errors as RFC 9457 problem details."""

from dataclasses import dataclass

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

from roombook.application.ports import PaymentUnavailable
from roombook.domain.errors import (
    BookingNotFound,
    IllegalTransition,
    InvalidTimeSlot,
    OutsideOpeningHours,
    RoomNotFound,
    SlotUnavailable,
)

PROBLEM_TYPE_BASE = "https://roombook.example/problems/"

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
        409, "slot-unavailable", "Slot already booked"
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
    await log.ainfo("request refused", problem=problem.slug)
    return JSONResponse(
        {
            "type": PROBLEM_TYPE_BASE + problem.slug,
            "title": problem.title,
            "status": problem.status,
            "detail": str(error),
            "instance": request.url.path,
        },
        status_code=problem.status,
        media_type="application/problem+json",
    )
