# ch07 — the dependency rule, enforced

Chapter 7. Two copies of the same small slice of roombook, with
the same import-linter contracts in `pyproject.toml`:

- a `layers` contract: adapters -> application -> domain;
- a `forbidden` contract: `roombook.domain` may not import
  sqlalchemy, pydantic or fastapi.

`violation/` makes the domain `Booking` a SQLAlchemy model, the
most common way the rule gets broken. The tests still pass and
mypy is clean; only `lint-imports` notices.

`fixed/` keeps `Booking` a plain dataclass and moves the ORM into
`adapters/sqlalchemy/records.py`, with `to_domain` and
`to_record` mapping between the two.

From the repo root, in the `examples` Compose service:

```bash
docker compose run --rm -w /repo/ch07/violation examples \
    lint-imports --no-logo   # exits 1: one contract broken
docker compose run --rm -w /repo/ch07/fixed examples \
    lint-imports --no-logo   # exits 0
```

With uv on the host instead:

```bash
cd ch07/violation
uv sync --locked
uv run lint-imports --no-logo   # exits 1: one contract broken

cd ../fixed
uv sync --locked
uv run lint-imports --no-logo   # exits 0
```

Recorded output: `docs/outputs/ch07/`.

`violation/pyproject.toml` carries `[tool.companion]
lint-imports = "must-fail"`. CI reads it and fails the build if
that contract ever stops being broken, so the demonstration
cannot rot silently.
