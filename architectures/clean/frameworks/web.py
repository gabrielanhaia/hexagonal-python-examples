from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from interface_adapters.controllers import (
    CancelBookingController,
    HoldRoomController,
)
from interface_adapters.presenters import (
    CancelBookingPresenter,
    HoldRoomPresenter,
    ViewModel,
)
from use_cases.cancel_booking import CancelBookingInteractor
from use_cases.gateways import BookingGateway, Clock, RoomGateway
from use_cases.hold_room import HoldRoomInteractor

router = APIRouter()


@dataclass(frozen=True, slots=True, kw_only=True)
class Gateways:
    rooms: RoomGateway
    bookings: BookingGateway
    clock: Clock


def get_gateways(request: Request) -> Gateways:
    return cast(Gateways, request.app.state.gateways)


GatewaysDep = Annotated[Gateways, Depends(get_gateways)]


class HoldBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    member_id: str
    start: datetime
    end: datetime


def render(view_model: ViewModel) -> JSONResponse:
    return JSONResponse(
        view_model.body, status_code=view_model.status_code
    )


@router.post("/rooms/{room_id}/holds")
async def hold_room(
    room_id: str, body: HoldBody, gateways: GatewaysDep
) -> JSONResponse:
    presenter = HoldRoomPresenter()
    interactor = HoldRoomInteractor(
        rooms=gateways.rooms,
        bookings=gateways.bookings,
        output=presenter,
    )
    await HoldRoomController(interactor).hold(
        room_id=room_id,
        member_id=body.member_id,
        start=body.start,
        end=body.end,
    )
    return render(presenter.view_model)


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str, gateways: GatewaysDep
) -> JSONResponse:
    presenter = CancelBookingPresenter()
    interactor = CancelBookingInteractor(
        bookings=gateways.bookings,
        clock=gateways.clock,
        output=presenter,
    )
    await CancelBookingController(interactor).cancel(
        booking_id=booking_id
    )
    return render(presenter.view_model)
