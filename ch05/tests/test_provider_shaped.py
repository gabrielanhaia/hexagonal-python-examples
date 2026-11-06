"""The fake has to speak SQL and HTTP to test one rule."""

from collections.abc import Mapping
from typing import Any

from provider_shaped.confirm import ConfirmBooking


class ScriptedDatabase:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row
        self.executed: list[tuple[str, Mapping[str, object]]] = []

    async def fetch_one(
        self, sql: str, params: Mapping[str, object]
    ) -> dict[str, Any] | None:
        assert sql.startswith("SELECT status, price_cents")
        return self.row

    async def execute(
        self, sql: str, params: Mapping[str, object]
    ) -> int:
        self.executed.append((sql, params))
        return 1


class CannedResponse:
    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> Any:
        return self._body


class ScriptedHttp:
    def __init__(self, response: CannedResponse) -> None:
        self.response = response
        self.posted: list[tuple[str, object]] = []

    async def post(
        self, url: str, *, json: object
    ) -> CannedResponse:
        self.posted.append((url, json))
        return self.response


async def test_confirm_charges_and_updates_the_row() -> None:
    db = ScriptedDatabase(
        {"status": "HELD", "price_cents": 2400, "currency": "EUR"}
    )
    http = ScriptedHttp(CannedResponse(201, {"id": "ch_1"}))

    await ConfirmBooking(db=db, http=http)("b-1")

    sql, params = db.executed[0]
    assert sql.startswith(
        "UPDATE bookings SET status = 'CONFIRMED'"
    )
    assert params == {"payment_id": "ch_1", "id": "b-1"}
    assert http.posted[0][0] == "/v1/charges"
