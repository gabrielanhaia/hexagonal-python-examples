# roombook

A booking service for a network of coworking spaces, built as a
hexagon. Members hold a meeting room for fifteen minutes, pay
through a payment provider called Tillpoint (fictional), and the
hold becomes a confirmed booking. This is the service Parts II,
III and V of the book build.

```
src/roombook/
├── domain/        # Booking, Room, TimeSlot, Money, events, errors
├── application/   # use cases + the ports they need (Protocols)
├── adapters/
│   ├── inbound/   # http (FastAPI), cli, messaging (FastStream), jobs
│   └── outbound/  # sqlalchemy, memory, payments, notify, outbox,
│                  # observability
├── composition.py          # the composition root
├── composition_dishka.py   # the same graph, wired by dishka
└── settings.py             # ROOMBOOK_* environment variables
migrations/        # Alembic, including the no-double-booking constraint
tests/             # unit, contract, integration, e2e
```

## Run it

Everything runs in Docker with the pinned toolchain. From the
repository root:

```bash
docker compose run --rm roombook availability --room atlas --day 2026-12-01
docker compose up roombook-api          # http://localhost:8000/docs
docker compose run --rm roombook-dev pytest
```

`BOOK-MAP.md` lists which files each chapter quotes.
