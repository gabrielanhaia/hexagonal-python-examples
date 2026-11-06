# ch24/step2 — extract the domain

New: `app/domain/` (`values.py`, `room.py`, `booking.py`,
`errors.py`), standard library only, with unit tests in
`tests/unit/` that need no database. The ORM classes are renamed
`RoomRow` and `BookingRow` and lose their rule methods; the routes
call the domain instead. The hold-expiry rule now has one source,
`hold_cutoff`, used by both the Python check and the SQL query.

```bash
uv sync --locked && uv run pytest -q
```
