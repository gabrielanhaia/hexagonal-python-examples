"""The front-desk CLI: the same use cases, from a terminal."""

import argparse
import sys
from datetime import date, datetime
from typing import Protocol, TextIO

from roombook.adapters.inbound.jobs.expire_holds import expire_holds
from roombook.application.cancel_booking import (
    CancelBooking,
    CancelBookingCommand,
)
from roombook.application.expire_stale_holds import ExpireStaleHolds
from roombook.application.hold_room import HoldRoom, HoldRoomCommand
from roombook.application.list_availability import (
    AvailabilityQuery,
    ListAvailability,
)
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
from roombook.domain.ids import BookingId, MemberId, RoomId

EXIT_CODES: dict[type[Exception], int] = {
    InvalidTimeSlot: 2,
    OutsideOpeningHours: 2,
    RoomNotFound: 3,
    BookingNotFound: 3,
    SlotUnavailable: 4,
    IllegalTransition: 4,
    PaymentUnavailable: 5,
}


class UseCases(Protocol):
    """What this adapter needs from the composition root."""

    @property
    def hold_room(self) -> HoldRoom: ...

    @property
    def cancel_booking(self) -> CancelBooking: ...

    @property
    def list_availability(self) -> ListAvailability: ...

    @property
    def expire_stale_holds(self) -> ExpireStaleHolds: ...


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roombook", description="Book meeting rooms."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    hold = commands.add_parser("hold", help="hold a room")
    hold.add_argument("--room", required=True)
    hold.add_argument("--member", required=True)
    hold.add_argument(
        "--start", required=True, type=datetime.fromisoformat
    )
    hold.add_argument(
        "--end", required=True, type=datetime.fromisoformat
    )

    cancel = commands.add_parser("cancel", help="cancel a booking")
    cancel.add_argument("booking_id")
    cancel.add_argument("--member", required=True)

    free = commands.add_parser("availability", help="free slots")
    free.add_argument("--room", required=True)
    free.add_argument(
        "--day", required=True, type=date.fromisoformat
    )

    commands.add_parser("expire-holds", help="release stale holds")
    return parser


async def run(
    args: argparse.Namespace,
    use_cases: UseCases,
    out: TextIO = sys.stdout,
) -> int:
    """Run one command; return the process exit code."""
    try:
        await _dispatch(args, use_cases, out)
    except (BookingError, PaymentUnavailable) as error:
        print(f"roombook: {error}", file=sys.stderr)
        return EXIT_CODES[type(error)]
    return 0


async def _dispatch(
    args: argparse.Namespace, use_cases: UseCases, out: TextIO
) -> None:
    match args.command:
        case "hold":
            receipt = await use_cases.hold_room(
                HoldRoomCommand(
                    room_id=RoomId(args.room),
                    member_id=MemberId(args.member),
                    start=args.start,
                    end=args.end,
                )
            )
            print(f"held     {receipt.booking_id}", file=out)
            print(f"price    {receipt.price}", file=out)
            print(
                f"expires  {receipt.expires_at:%H:%M %Z}", file=out
            )
            print(f"pay at   {receipt.checkout_url}", file=out)
        case "cancel":
            terms = await use_cases.cancel_booking(
                CancelBookingCommand(
                    booking_id=BookingId(args.booking_id),
                    member_id=MemberId(args.member),
                )
            )
            print(f"cancelled {args.booking_id}", file=out)
            print(f"fee       {terms.fee}", file=out)
            print(f"refund    {terms.refund}", file=out)
        case "availability":
            found = await use_cases.list_availability(
                AvailabilityQuery(
                    room_id=RoomId(args.room), day=args.day
                )
            )
            for slot in found.free:
                start, end = slot.start, slot.end
                print(
                    f"{start:%H:%M}-{end:%H:%M} {end:%Z}", file=out
                )
        case "expire-holds":
            expired = await expire_holds(
                use_cases.expire_stale_holds
            )
            print(f"expired {expired} hold(s)", file=out)
