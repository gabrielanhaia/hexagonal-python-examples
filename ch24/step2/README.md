# ch24/step2 — extract the domain

New: `app/domain/` (`values.py`, `room.py`, `booking.py`,
`errors.py`), standard library only, with unit tests in
`tests/unit/` that need no database. The ORM classes are renamed
`RoomRow` and `BookingRow` and lose their rule methods; the routes
call the domain instead. The hold-expiry rule now has one source,
`hold_cutoff`, used by both the Python check and the SQL query.

From the repo root, in the `examples` Compose service:

```bash
docker compose run --rm -w /repo/ch24/step2 examples pytest -q
```

With uv on the host instead, from this directory:

```bash
uv sync --locked && uv run pytest -q
```
