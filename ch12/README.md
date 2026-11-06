# ch12 — an aggregate that owns child records

Chapter 12. `roombook/` maps single-row aggregates; this project
shows the records-and-mappers approach on the hard case: an
aggregate that owns a collection.

```text
src/roombook/domain/room.py       Room owns BlackoutPeriod children
src/roombook/domain/time_slot.py  TimeSlot.overlaps
src/roombook/domain/errors.py     what the aggregate refuses
src/roombook/adapters/sqlalchemy/
    records.py                    RoomRecord, BlackoutRecord,
                                  relationship()
    mappers.py                    to_domain, to_record, reconcile
    repository.py                 SqlAlchemyRoomRepository
tests/test_room.py                the rules, no database
tests/test_lazy_loading.py        the async lazy-load trap
tests/test_repository.py          save adds, updates, deletes
```

A `Room` is closed during its blackout periods (maintenance
windows), and `Room.add_blackout()` refuses one that overlaps
another. The domain is plain classes; nothing in it imports
SQLAlchemy.

The repository loads the whole aggregate in one go with
`selectinload(RoomRecord.blackouts)`. Without it, touching
`record.blackouts` under an `AsyncSession` needs IO that asyncio
cannot do implicitly: SQLAlchemy raises `MissingGreenlet` (with
aiosqlite, wrapped in a `StatementError`).
`tests/test_lazy_loading.py` shows both sides.

Nothing tracks the domain object, so `save` reconciles the child
rows by id: a blackout the room no longer has is removed from
`RoomRecord.blackouts` and `delete-orphan` deletes its row; one
it still has is updated in place; a new one is inserted.

The tests use SQLite through aiosqlite in a temporary file, so
nothing else is needed.

```bash
docker compose run --rm -w /repo/ch12 examples pytest -q
docker compose run --rm -w /repo/ch12 examples mypy
docker compose run --rm -w /repo/ch12 examples \
    lint-imports --no-logo
```

Contracts (`pyproject.toml`): adapters may import the domain,
never the reverse, and the domain imports no SQLAlchemy.
