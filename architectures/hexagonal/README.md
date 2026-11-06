# architectures/hexagonal

Ports and adapters (chapters 14-17), a slim version of the shape
`roombook/` uses.

```text
domain/        Money, TimeSlot, Room, Booking, errors; stdlib only
application/   HoldRoom, CancelBooking and the port Protocols
adapters/      FastAPI router (driving), in-memory repos and the
               system clock (driven)
composition/   create_app(): the composition root
```

Contracts (`pyproject.toml`): a `layers` contract,
composition -> adapters -> application -> domain, and a
`forbidden` contract that keeps fastapi, pydantic and starlette
out of `application` and `domain`.

```bash
uv sync --locked && uv run pytest -q && uv run lint-imports
```
