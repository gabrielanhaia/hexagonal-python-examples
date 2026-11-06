from dataclasses import dataclass, field
from typing import override

from use_cases.cancel_booking import (
    CancelBookingOutputBoundary,
    CancelBookingResponse,
)
from use_cases.failures import Failure, FailureKind
from use_cases.hold_room import (
    HoldRoomOutputBoundary,
    HoldRoomResponse,
)

STATUS_FOR = {
    FailureKind.NOT_FOUND: 404,
    FailureKind.CONFLICT: 409,
    FailureKind.REJECTED: 422,
}


@dataclass(slots=True, kw_only=True)
class ViewModel:
    status_code: int = 500
    body: dict[str, object] = field(default_factory=dict)


def failure_view(failure: Failure) -> ViewModel:
    return ViewModel(
        status_code=STATUS_FOR[failure.kind],
        body={"detail": failure.message},
    )


def money_view(amount: int, currency: str) -> dict[str, object]:
    return {"amount": amount, "currency": currency}


class HoldRoomPresenter(HoldRoomOutputBoundary):
    def __init__(self) -> None:
        self.view_model = ViewModel()

    @override
    def present(self, response: HoldRoomResponse) -> None:
        self.view_model = ViewModel(
            status_code=201,
            body={
                "booking_id": response.booking_id,
                "status": response.status,
                "price": money_view(
                    response.price_amount, response.currency
                ),
            },
        )

    @override
    def present_failure(self, failure: Failure) -> None:
        self.view_model = failure_view(failure)


class CancelBookingPresenter(CancelBookingOutputBoundary):
    def __init__(self) -> None:
        self.view_model = ViewModel()

    @override
    def present(self, response: CancelBookingResponse) -> None:
        self.view_model = ViewModel(
            status_code=200,
            body={
                "booking_id": response.booking_id,
                "status": response.status,
                "fee": money_view(
                    response.fee_amount, response.currency
                ),
            },
        )

    @override
    def present_failure(self, failure: Failure) -> None:
        self.view_model = failure_view(failure)
