# ch24/step5 — strangle the rest

The end state:

```text
app/domain/        values, room, booking, errors; stdlib only
app/application/   HoldRoom, ConfirmBooking, CancelBooking, ports
app/adapters/      http (routes and wiring), schemas, tillpoint,
                   sqlalchemy/ (records, database, repositories),
                   memory, clock
app/main.py        the composition root
```

`pyproject.toml` now carries two import-linter contracts: layers
`app.main -> app.adapters -> app.application -> app.domain`, and
a ban on fastapi, httpx2, pydantic, sqlalchemy and `app.settings`
inside the core. The slot rules moved out of the Pydantic schema
into `TimeSlot`. The repository commits on `save`; the Unit of Work
is chapter 19's subject.

```bash
uv sync --locked
uv run pytest -q
uv run lint-imports --no-logo
uv run uvicorn app.main:app --port 8000
```
