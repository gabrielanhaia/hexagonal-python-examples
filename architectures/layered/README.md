# architectures/layered

The classic baseline (chapter 16): presentation calls services,
services call data access. The models are SQLAlchemy ORM models,
so the business rules in `services/` depend on the persistence
layer. That dependency is the whole difference from the other
four variants.

```text
presentation/  FastAPI app, routes, Pydantic schemas
services/      business rules (BookingService) and errors
data_access/   ORM models, engine and sessions, BookingDAO
```

Contract (`pyproject.toml`): a `layers` contract,
presentation -> services -> data_access. Skipping a layer
downward is allowed; importing upward is not.

Database: in-memory SQLite through aiosqlite. `UTCDateTime`
in `data_access/models.py` exists because SQLite stores no
timezones.

```bash
uv sync --locked && uv run pytest -q && uv run lint-imports
```
