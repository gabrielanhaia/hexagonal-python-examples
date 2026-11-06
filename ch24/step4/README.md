# ch24/step4 — move one route

The hold route now calls `HoldRoom` (`app/application/hold_room.py`)
through the ports; FastAPI's `Depends` builds the use case per
request. Domain errors become HTTP errors in one function,
`http_error`. Confirm and cancel still run the old code, which is
the point: both styles live side by side, and the characterisation
tests still pass. `tests/unit/test_hold_room.py` tests the use
case with in-memory adapters and a fixed clock.

```bash
uv sync --locked && uv run pytest -q
```
