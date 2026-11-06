from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import Depends, Request

from kernel.database import Database

type Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_database(request: Request) -> Database:
    return cast(Database, request.app.state.database)


def get_clock(request: Request) -> Clock:
    return cast(Clock, request.app.state.clock)


DatabaseDep = Annotated[Database, Depends(get_database)]
ClockDep = Annotated[Clock, Depends(get_clock)]
