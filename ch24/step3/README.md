# ch24/step3 — introduce the ports

New: the `Booking` aggregate in `app/domain/booking.py`; the ports
in `app/application/ports.py` (`RoomRepository`,
`BookingRepository`, `Clock`); two adapters for the booking port,
`app/adapters/sqlalchemy_repository.py` and
`app/adapters/memory.py`. `tests/contract/` runs one suite against
both. The routes do not use any of it yet: the seam exists before
anything crosses it.

From the repo root, in the `examples` Compose service:

```bash
docker compose run --rm -w /repo/ch24/step3 examples pytest -q
```

With uv on the host instead, from this directory:

```bash
uv sync --locked && uv run pytest -q
```
