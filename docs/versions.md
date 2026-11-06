# Versions

Every project pins its direct dependencies exactly (`==`) in its
own `pyproject.toml`, and `uv.lock` pins everything else. CI's
`pinned` job installs with `uv sync --locked`; the `latest` job
lifts every pin to see what the next release breaks.

Each entry: the pin, why it is there, where it is used, and when
it was last checked against its official source (PyPI, Docker Hub
or GHCR, GitHub releases, python.org).

## Runtime and toolchain

- **CPython 3.14.10**, `requires-python = ">=3.14"`; CI also runs
  **3.15.2**. 3.14 for PEP 649 (no quoted forward references, no
  `from __future__ import annotations`). Every project carries a
  `.python-version` of `3.14`, because uv 0.13 defaults to 3.15.
  Verified 2026-11-06.
- **uv 0.13.7**: installs and runs every project
  (`uv sync --locked`, `uv run`). Verified 2026-11-06.
- **uv_build 0.13.7** (`uv_build>=0.13.7,<0.14`): build backend
  for the src-layout projects, `ch07/*` and `ch25`. Verified
  2026-11-06.
- **Docker `python:3.14.10-slim-trixie`**: base image for
  runtimes. Verified 2026-11-06.
- **Docker `ghcr.io/astral-sh/uv:0.13.7-python3.14-trixie-slim`**:
  uv and CPython 3.14.10 in one image; runs any project without a
  local toolchain (see the project READMEs). Verified 2026-11-06.
- **Docker `postgres:18.6-trixie`** / PostgreSQL 18.6: the
  database for `roombook/`, started by docker compose and by
  testcontainers. Verified 2026-11-06.

## Web, data and HTTP

- **fastapi 0.162.0**: every HTTP adapter (`architectures/*`,
  `ch01`, `ch24/*`, `ch25`, `roombook`). Verified 2026-11-06.
- **starlette 1.10.0**: FastAPI's ASGI toolkit; pinned directly
  in `roombook`, locked transitively elsewhere. 1.0 removed
  `on_event`: lifespan only. Verified 2026-11-06.
- **pydantic 2.14.3**: request and response models at the edge,
  never in a domain. Verified 2026-11-06.
- **pydantic-settings 2.16.2**: `ROOMBOOK_*` settings (`ch01`,
  `ch24/*`, `roombook`). Verified 2026-11-06.
- **uvicorn 0.54.0**: the ASGI server (`ch01`, `ch24/*`,
  `roombook`). Verified 2026-11-06.
- **sqlalchemy[asyncio] 2.1.8**: persistence (`architectures/
  layered`, `ch01`, `ch07/*`, `ch24/*`, `roombook`). The
  `asyncio` extra brings greenlet, which 2.1 no longer installs
  by default. Verified 2026-11-06.
- **aiosqlite 0.22.1**: async SQLite driver for the SQLite-backed
  projects (`architectures/layered`, `ch01`, `ch24/*`). Not in the
  book's main lock; added so those projects need no Postgres.
  Released 2025-12-23, still the latest on PyPI. Verified
  2026-11-06.
- **alembic 1.20.1**: migrations (`roombook`). Verified
  2026-11-06.
- **psycopg[binary] 3.3.8**: SQLAlchemy 2.1's default PostgreSQL
  driver (`roombook`). Verified 2026-11-06.
- **httpx2 2.16.0**: the Pydantic-maintained fork of httpx; the
  Tillpoint client (`ch01`, `ch05`, `ch24/*`, `roombook`) and the
  backend of Starlette's `TestClient` in every FastAPI project.
  Verified 2026-11-06.

## Messaging, DI, observability (`roombook`)

- **faststream[kafka] 0.7.8**. Verified 2026-11-06.
- **aiokafka 0.14.0** (via FastStream). 0.15.0 is out, but
  FastStream 0.7.8 requires `aiokafka<0.15`. Verified 2026-11-06.
- **dishka 1.10.1**. Verified 2026-11-06.
- **opentelemetry-api / -sdk 1.45.2** and
  **opentelemetry-instrumentation-sqlalchemy 0.66b2**. The
  SQLAlchemy instrumentation declares support below 2.1 only;
  roombook skips its version check and a Postgres test proves
  spans are produced. No FastAPI instrumentation package:
  FastAPI 0.162 traces natively once a tracer provider exists,
  and adding it would record every request twice. Verified
  2026-11-06.
- **structlog 26.1.0**. Verified 2026-11-06.

## Quality gates

- **ruff 0.17.4**: lint and format, `line-length = 68` so every
  listing fits the printed page. Verified 2026-11-06.
- **mypy 2.4.1**: `strict = true` in every project. Verified
  2026-11-06.
- **import-linter 2.16**: the dependency rule as a contract in
  each `pyproject.toml`. Verified 2026-11-06.
- **pytest 9.2.0**: native `[tool.pytest]` TOML configuration.
  Verified 2026-11-06.
- **pytest-asyncio 1.4.1.post1**: async tests, `asyncio_mode =
  "auto"` with both loop scopes set. Verified 2026-11-06.
- **hypothesis 6.170.15**: property tests (`roombook`). Verified
  2026-11-06.
- **testcontainers 4.15.0**: PostgreSQL for tests marked
  `postgres` (`roombook`); import from
  `testcontainers.community.postgres`, pass `driver="psycopg"`.
  Verified 2026-11-06.

## GitHub Actions (`.github/workflows/ci.yml`)

Pinned to the current major version of each action.

- **actions/checkout@v7** (latest release v7.0.1). Verified
  2026-11-06.
- **astral-sh/setup-uv@v10.3.3** (exact tag: setup-uv publishes no moving `v10` tag); installs
  uv 0.13.7 in the `pinned` job and the newest uv in `latest`.
  Verified 2026-11-06.
- **actions/github-script@v9** (latest release v9.0.0); opens the
  issue when the `latest` job fails. Verified 2026-11-06.
- Runner image **ubuntu-24.04**. Verified 2026-11-06.

## Re-verify

Re-check every entry before a new edition of the book, after a
major release of FastAPI, SQLAlchemy or Pydantic, or six months
after the last date above, whichever comes first.

## Container images

- **python:3.14.10-slim-trixie** (roombook runtime) and
  **ghcr.io/astral-sh/uv:0.13.7** (uv copied into it).
- **ghcr.io/astral-sh/uv:0.13.7-python3.14-trixie-slim**: the
  `examples` Compose service that runs every other project.
- **postgres:18.6-trixie** and **apache/kafka:4.4.0** (KRaft).

All verified to exist on their registries 2026-11-06.
