# ch01 — the framework-shaped roombook

Chapter 1's "before" app: a working FastAPI service of the kind a
competent team ships under a deadline. The booking rules live in
the route handlers (`app/main.py`) and in the SQLAlchemy models
(`app/models.py`); the request schema (`app/schemas.py`) holds the
slot rules. Chapter 24 migrates this app to hexagonal, step by
step, in `ch24/`.

```text
app/main.py      routes: hold, confirm (calls Tillpoint), cancel
app/models.py    ORM models; hold expiry and the cancellation fee
app/schemas.py   Pydantic request and response models
app/db.py        engine and session, built at import time
app/settings.py  ROOMBOOK_* environment settings
```

Where each rule lives today:

| Rule                              | Where                       |
|-----------------------------------|-----------------------------|
| 15-minute steps, start < end      | `schemas.HoldIn`            |
| opening hours, overlap, price     | `main.hold_room`            |
| a hold expires after 15 minutes   | `models.Booking.is_expired` |
|                                   | and the `hold_room` query   |
| cancellation fee                  | `models.Booking`            |
| charge the member                 | `main.confirm_booking`      |

The hold-expiry rule is written twice, once in Python and once in
SQL. Every test needs the database, and "now" is read from the
system clock inside the model.

Tillpoint is a fictional payment provider; the default URL uses
the reserved `.example` domain, and the tests replace the client
with an `httpx2.MockTransport`.

## Run

From the repo root, in the `examples` Compose service:

```bash
docker compose run --rm -w /repo/ch01 examples pytest -q
docker compose run --rm -w /repo/ch01 -p 8000:8000 examples \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
```

With uv on the host instead:

```bash
cd ch01
uv sync --locked
uv run pytest -q
uv run uvicorn app.main:app --port 8000
```

The service creates `roombook.db` (SQLite) in the working
directory and seeds one room, `atlas`. Settings come from
`ROOMBOOK_DATABASE_URL`, `ROOMBOOK_TILLPOINT_URL` and
`ROOMBOOK_TILLPOINT_API_KEY`.

```bash
curl -s -X POST localhost:8000/rooms/atlas/holds \
  -H 'content-type: application/json' \
  -d '{"member_id": "m-1", "start": "2026-12-01T10:00:00Z",
       "end": "2026-12-01T11:00:00Z"}'
```
