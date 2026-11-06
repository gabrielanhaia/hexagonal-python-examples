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

From the repo root, in the `examples` Compose service:

```bash
docker compose run --rm -w /repo/ch24/step5 examples pytest -q
docker compose run --rm -w /repo/ch24/step5 examples \
    lint-imports --no-logo
docker compose run --rm -w /repo/ch24/step5 -p 8000:8000 examples \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
```

With uv on the host instead, from this directory:

```bash
uv sync --locked
uv run pytest -q
uv run lint-imports --no-logo
uv run uvicorn app.main:app --port 8000
```
