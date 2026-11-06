"""Ports shaped like the tools behind them. Do not copy these."""

from collections.abc import Mapping
from typing import Any, Protocol


class Database(Protocol):  # the shape of a database driver
    async def fetch_one(
        self, sql: str, params: Mapping[str, object]
    ) -> dict[str, Any] | None: ...

    async def execute(
        self, sql: str, params: Mapping[str, object]
    ) -> int: ...


class HttpResponse(Protocol):
    @property
    def status_code(self) -> int: ...

    def json(self) -> Any: ...


class HttpClient(Protocol):  # the shape of an HTTP client
    async def post(
        self, url: str, *, json: object
    ) -> HttpResponse: ...
