from dataclasses import dataclass
from typing import Protocol, override

from entities.errors import BookingNotFound, DomainError
from use_cases.failures import Failure, failure_from
from use_cases.gateways import BookingGateway, Clock


@dataclass(frozen=True, slots=True, kw_only=True)
class CancelBookingRequest:
    booking_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CancelBookingResponse:
    booking_id: str
    status: str
    fee_amount: int
    currency: str


class CancelBookingInputBoundary(Protocol):
    async def cancel(
        self, request: CancelBookingRequest
    ) -> None: ...


class CancelBookingOutputBoundary(Protocol):
    def present(self, response: CancelBookingResponse) -> None: ...

    def present_failure(self, failure: Failure) -> None: ...


class CancelBookingInteractor(CancelBookingInputBoundary):
    def __init__(
        self,
        *,
        bookings: BookingGateway,
        clock: Clock,
        output: CancelBookingOutputBoundary,
    ) -> None:
        self._bookings = bookings
        self._clock = clock
        self._output = output

    @override
    async def cancel(self, request: CancelBookingRequest) -> None:
        booking = await self._bookings.get(request.booking_id)
        try:
            if booking is None:
                raise BookingNotFound(request.booking_id)
            fee = booking.cancel(now=self._clock.now())
        except DomainError as error:
            self._output.present_failure(failure_from(error))
            return
        await self._bookings.save(booking)
        self._output.present(
            CancelBookingResponse(
                booking_id=booking.id,
                status=booking.status,
                fee_amount=fee.amount,
                currency=fee.currency,
            )
        )
