"""The CLI drives the same use cases; errors become exit codes."""

import io

import pytest

from roombook.adapters.inbound.cli.commands import build_parser, run
from tests.memory_wiring import memory_roombook

HOLD = [
    "hold",
    "--room=atlas",
    "--member=member-ada",
    "--start=2026-12-01T10:00+00:00",
    "--end=2026-12-01T11:00+00:00",
]


async def roombook_cli(*runs: list[str]) -> tuple[int, str]:
    """Run commands in turn against one store; last exit code."""
    roombook = memory_roombook()
    out = io.StringIO()
    code = 0
    for argv in runs:
        code = await run(
            build_parser().parse_args(argv), roombook, out
        )
    return code, out.getvalue()


async def test_hold_prints_the_receipt() -> None:
    code, out = await roombook_cli(HOLD)

    assert code == 0
    assert "price    EUR 40.00" in out
    assert "expires  09:15 UTC" in out


async def test_a_taken_slot_exits_with_4(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, _ = await roombook_cli(HOLD, HOLD)

    assert code == 4
    assert "already booked" in capsys.readouterr().err


async def test_availability_lists_free_slots() -> None:
    free = ["availability", "--room=atlas", "--day=2026-12-01"]

    code, out = await roombook_cli(HOLD, free)

    assert code == 0
    assert out.splitlines()[-2:] == [
        "08:00-10:00 WET",
        "11:00-20:00 WET",
    ]


def test_a_bad_date_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(
            ["availability", "--room=atlas", "--day=tomorrow"]
        )
    assert exit_info.value.code == 2
