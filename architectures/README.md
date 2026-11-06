# architectures/ — one feature, five architectures

Part IV of the book (chapters 14-17). The same feature is built
five times so the structures can be compared on equal terms:

- **hold a room**: validate the slot (timezone-aware, start before
  end, 15-minute steps), check opening hours, reject overlaps with
  held or confirmed bookings, price = hourly rate x duration,
  create a `HELD` booking;
- **cancel a booking**: free if cancelled at least 24 hours before
  the start, otherwise a 50% fee.

| Directory         | Architecture                     | Chapter |
|-------------------|----------------------------------|---------|
| `layered/`        | presentation -> service -> data  | 16      |
| `hexagonal/`      | ports and adapters               | 14-17   |
| `onion/`          | Palermo's rings                  | 15      |
| `clean/`          | Martin's Clean Architecture      | 14      |
| `vertical_slice/` | one folder per feature (Bogard)  | 16      |

Every variant exposes the same HTTP API through FastAPI and keeps
its data in memory, except `layered/`, whose point is that the
business code depends on the persistence layer: it uses
SQLAlchemy 2.1 on in-memory SQLite (aiosqlite).

## The shared scenarios

`tests/test_scenarios.py` is byte-for-byte identical in all five
variants (`measure.py` checks the hash). Only `tests/conftest.py`
differs, because each variant builds its app and fixes its clock
in its own way. The clock is fixed at 2026-11-09 09:00 UTC; room
`atlas` is open 08:00-20:00 UTC at 2400 EUR minor units an hour.

1. a hold creates a `HELD` booking priced by the hour
2. a slot off the 15-minute grid is rejected (422)
3. a slot that ends before it starts is rejected (422)
4. a slot outside opening hours is rejected (422)
5. an unknown room is not found (404)
6. a hold that overlaps another is a conflict (409)
7. a slot that starts when another ends is accepted (201)
8. cancelling 24 hours ahead is free
9. cancelling later costs half the price
10. cancelling an unknown booking is not found (404)
11. cancelling twice is a conflict (409)
12. a cancelled slot can be held again
13. a booking longer than four hours is rejected (422)
14. a booking of exactly four hours is accepted

Scenarios 13 and 14 arrive with the "max booking length" rule,
added to each variant in its own commit (see
`add-max-length-rule.md`).

## The rule each variant enforces

Each `pyproject.toml` carries an import-linter contract that
encodes that architecture's own rule:

- `layered/`: layers, presentation over services over data access;
- `hexagonal/`: composition over adapters over application over
  domain, and the core imports no web framework;
- `onion/`: ui over infrastructure over the three core rings,
  and the core rings import no web framework;
- `clean/`: frameworks over interface adapters over use cases
  over entities, and only the outer circle knows FastAPI;
- `vertical_slice/`: the two slices are independent of each
  other, and the shared kernel imports no slice.

## Run

From a variant's directory:

```bash
uv sync --locked
uv run pytest -q
uv run lint-imports
uv run mypy
```

Without a local uv, with Docker only (from the repo root):

```bash
docker run --rm -v "$PWD":/w -w /w/architectures/clean \
  -e UV_PROJECT_ENVIRONMENT=/tmp/venv \
  ghcr.io/astral-sh/uv:0.13.7-python3.14-trixie-slim \
  sh -c "uv sync --locked && uv run pytest -q"
```

## Measure

```bash
python3 architectures/measure.py
```

Standard library only. It counts files, lines, classes and
Protocols, tests, and the files each variant touched when the
max-length rule landed. The recorded run is in
`docs/outputs/architectures/measure.txt`.
