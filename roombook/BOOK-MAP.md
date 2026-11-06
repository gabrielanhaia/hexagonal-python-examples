# Book map: which roombook code each chapter quotes

Paths are from the repository root, exactly as a listing's first
line prints them (`# roombook/src/roombook/domain/booking.py`).
`S/` below abbreviates `roombook/src/roombook/`. Every recorded
output a chapter may print is in `docs/outputs/roombook/`; each
file starts with the command that produced it.

Recorded lines are not wrapped. Many exceed 68 characters (pytest
`-v` headers, curl bodies, Kafka dumps): excerpt with `# ...`,
never re-wrap or retype them.

## Part II: Thinking in Hexagons

### 4. The Domain Owns Nothing

- `S/domain/money.py`: `Money` (frozen, slotted, int minor units,
  `scaled(Fraction)` rounds half to even, `__str__`).
- `S/domain/time_slot.py`: `TimeSlot`, `GRANULARITY`, the three
  invariants in `__post_init__`, `overlaps`, `contains`.
- `S/domain/room.py`: `OpeningHours.on(day)` (time zones via
  stdlib `zoneinfo`), `Room.check_open`, `Room.price_for`.
- `S/domain/ids.py`: `NewType` ids.
- Time as an input: `Booking.hold(..., now=...)` in
  `S/domain/booking.py`; no `datetime.now()` anywhere in
  `domain/` or `application/` (the clock is the `Clock` port).
- Enforced by the "The core imports no framework" contract in
  `roombook/pyproject.toml` (`[tool.importlinter]`).
- Tests: `roombook/tests/unit/test_money.py`, `test_time_slot.py`,
  `test_room.py`.

### 5. Ports Are Protocols the Core Writes

- `S/application/ports.py`: every driven port. `BookingRepository`
  (5 methods), `RoomRepository` (1), `UnitOfWork` (async context
  manager, read-only `@property` repositories, `Self`),
  `UnitOfWorkFactory` (callback Protocol), `Clock`, `IdGenerator`,
  `PaymentGateway` + `Checkout` + `PaymentUnavailable` (the port's
  own error), `Notifier`, `Outbox`.
- Driving ports are the use-case classes themselves: their
  `__call__(command) -> result` signature is the port.
- Port size in practice: the fakes in
  `S/adapters/outbound/memory/fakes.py` (each under ten lines).
- Adapter-owned ports: `UseCases` in
  `S/adapters/inbound/http/dependencies.py` and
  `S/adapters/inbound/cli/commands.py`; `ProcessedMessages` in
  `S/adapters/inbound/messaging/coinwren.py`. Each driving adapter
  declares only what it needs; `Roombook` satisfies all of them
  structurally.

### 6. Adapters on Both Sides

- Driving: `S/adapters/inbound/http/routes.py` (`hold_room`
  route), translation in `S/adapters/inbound/http/schemas.py`
  (`HoldRequest.to_command`, `HoldResponse.of`).
- Driven: `S/adapters/outbound/memory/repositories.py`
  (`InMemoryBookingRepository` stores copies via
  `dataclasses.replace`) and `.../memory/unit_of_work.py`
  (`InMemoryStore`, `InMemoryUnitOfWork`).
- Two adapters per port: memory and SQLAlchemy, proven by
  `roombook/tests/contract/test_unit_of_work.py`.

### 7. The Dependency Rule, Enforced

- `roombook/pyproject.toml`: `[tool.importlinter]` with three
  contracts (layers, forbidden, independence),
  `include_external_packages = true`; `[tool.mypy] strict = true`.
- Output: `docs/outputs/roombook/lint-imports.txt`, `mypy.txt`.
- (The deliberate violation lives in `ch07/`, not here.)

## Part III: Building the Booking Service

### 8. A Layout That Tells the Truth

- `roombook/pyproject.toml` (exact pins, `[project.scripts]`,
  `[dependency-groups] dev`, ruff 68, mypy strict, native
  `[tool.pytest]`, import-linter), `roombook/.python-version`,
  `roombook/Dockerfile`, `roombook/README.md` (tree).
- `uv_build==0.13.7` as the build backend.
- Outputs: `ruff.txt`, `ruff-format.txt`.

### 9. Modeling Bookings

- `S/domain/booking.py`: `BookingStatus`, `ACTIVE_STATUSES`, the
  `_NEXT` transition table, `Booking.hold/confirm/cancel/expire`,
  `_become` raising `IllegalTransition`, `_record` and
  `pull_events`, equality by id, idempotent `confirm` for the same
  payment id.
- Aggregate choice: one `Booking` per claim; overlap checked through
  `BookingRepository.overlapping` and enforced by the exclusion
  constraint (`roombook/migrations/versions/0001_bookings.py`).
- `Booking` is a plain (unslotted) mutable dataclass on purpose:
  value objects and events are frozen and slotted; the aggregate
  mutates through methods. (Ch. 12 shows the measured cost slots
  would have under imperative mapping.)
- `S/domain/cancellation.py`: `cancellation_terms` (pure function),
  `CancellationTerms`, `FREE_CANCELLATION_NOTICE`,
  `LATE_CANCELLATION_FEE`.
- `S/domain/events.py`: the four events and
  `type BookingEvent = ...` (PEP 695).
- `S/domain/errors.py`: `BookingError` and its subclasses.
  `RoomNotFound` is the one error added beyond the bible's list
  (holding an unknown room needs it).
- `S/domain/availability.py`: `free_slots`.
- Hypothesis: `roombook/tests/unit/test_time_slot.py`
  (`slots()` strategy, symmetry), `test_availability.py` (every
  quarter free xor taken). Transition tests:
  `roombook/tests/unit/test_booking.py`.

### 10. Use Cases and Application Services

- `S/application/hold_room.py`: `HoldRoomCommand`, `HoldReceipt`,
  `HoldRoom` (a frozen dataclass of ports with `async __call__`).
  Read it top to bottom: build slot, open unit of work, load room,
  domain check, `Booking.hold`, add, outbox, commit, then the
  checkout after commit.
- Use case as a class, decided: a frozen dataclass whose fields
  are its ports; one instance per process, a new unit of work per
  call (`unit_of_work: UnitOfWorkFactory`), so it is safe under
  concurrent requests.
- Authorisation in the use case: `S/application/cancel_booking.py`
  answers "not yours" as `BookingNotFound`.
- Other use cases: `confirm_booking.py`, `list_availability.py`,
  `expire_stale_holds.py`.
- Tests with fakes: `roombook/tests/unit/conftest.py` (wiring a use
  case is one constructor), `test_hold_room.py` and siblings.
  Output: `docs/outputs/roombook/pytest-unit.txt` (53 tests).

### 11. Driving Adapters: HTTP, CLI and a Consumer

- HTTP: `S/adapters/inbound/http/app.py` (`create_app(lifespan)`,
  `exception_handlers=`, `middleware=`), `dependencies.py`
  (`Annotated[..., Depends()]` aliases, lifespan state via
  `request.state.use_cases`, `X-Member-Id` header),
  `routes.py`, `schemas.py` (Pydantic v2, `AwareDatetime`,
  `ConfigDict(extra="forbid", frozen=True)`).
- Problem details: `S/adapters/inbound/http/problems.py` (`PROBLEMS`
  table, `problem_response`, `application/problem+json`).
- CLI: `S/adapters/inbound/cli/commands.py` (`build_parser`, `run`,
  `_dispatch` with `match`, `EXIT_CODES`).
- Consumer: `S/adapters/inbound/messaging/coinwren.py`
  (`CoinwrenConsumer.handle`, `coinwren_router` with
  `AckPolicy.NACK_ON_ERROR`, dead-letter publisher).
- Job: `S/adapters/inbound/jobs/expire_holds.py`.
- The core never changed: same `HoldRoom` behind all three.
- Outputs: `curl-hold.txt`, `cli-hold.txt`, `cli-hold-conflict.txt`,
  `cli-hold-closed.txt`, `cli-availability.txt`, `cli-cancel.txt`,
  `cli-expire-holds.txt`, `cli-help.txt`, `consumer.txt`.
- Tests: `roombook/tests/e2e/test_http.py`,
  `roombook/tests/integration/test_cli.py`,
  `roombook/tests/integration/test_coinwren_consumer.py`
  (FastStream `TestKafkaBroker`).

### 12. Driven Adapters: SQLAlchemy 2 Without Letting It In

- Chosen approach, separate records + explicit mappers:
  `S/adapters/outbound/sqlalchemy/records.py` (`Base`,
  `type_annotation_map`, `BookingRecord` with `TSTZRANGE` and
  `ExcludeConstraint`), `mappers.py` (`booking_to_record`,
  `booking_from_record`, `update_record`, `slot_to_range`).
- Repositories: `S/adapters/outbound/sqlalchemy/repositories.py`
  (`select()` + `scalars`, `Range.overlaps`, `get(...,
  with_for_update=True)`, `stale_holds` with
  `with_for_update(skip_locked=True)`, and `add` translating
  `ExclusionViolation` into `SlotUnavailable`).
- The alternative, imperative mapping on the real `Booking`:
  `S/adapters/outbound/sqlalchemy/imperative.py`
  (`registry.map_imperatively`, `composite(Money, ...)`, a
  `TimeSlotType` `TypeDecorator`, the `load` event to restore
  `_events`, and the column `key=` needed so the `price` composite
  does not collide with the `price` column).
  Costs, measured in `roombook/tests/integration/
  test_imperative_mapping.py`: a `slots=True` dataclass fails with
  `TypeError: cannot create weak reference`; loading skips
  `__init__`; mapping instruments the class for the whole process
  (the fixture must `dispose()`, and a failed mapping leaked into
  unrelated tests while this was being built).
- Engine and sessions: `database()` in `S/composition.py`
  (`create_async_engine`, `async_sessionmaker(...,
  expire_on_commit=False)`, `postgresql+psycopg://`).
- Alembic: `roombook/alembic.ini`, `roombook/migrations/env.py`
  (async engine via `run_sync`),
  `roombook/migrations/versions/0001_bookings.py` (`CREATE
  EXTENSION btree_gist`, the `EXCLUDE USING gist` constraint),
  `0002_seed_rooms.py`.
- Coinwren client: `S/adapters/outbound/payments/coinwren.py`
  (`import httpx2`, `Idempotency-Key`, every provider failure
  becomes `PaymentUnavailable`). Tests with `httpx2.MockTransport`:
  `roombook/tests/integration/test_coinwren_gateway.py`.

### 13. Wiring: the Composition Root

- `S/composition.py`: `Roombook` (every use case, wired),
  `build_roombook` (pure wiring, also used by the tests),
  `database`, `payment_gateway`, `notifier`, `roombook` (async
  context managers own the resources), `create_http_app` (lifespan
  yields `{"use_cases": ...}`), `main`, `run_consumer`,
  `run_relay`.
- `S/settings.py`: pydantic-settings, `ROOMBOOK_` prefix,
  `SecretStr`, `Literal` adapter switches (`payments="fake" |
  "coinwren"`, `notifier="console" | "smtp"`).
- dishka: `S/composition_dishka.py` (`Provider`, `Scope.APP`,
  `from_context`, generator providers for finalisation,
  `@decorate` for the tracing decorators, `provide_all`,
  `make_async_container`). The graph is APP-scoped because the unit
  of work is created per call by a factory, so dishka's
  `setup_dishka`/`FromDishka` request scope is not needed here;
  routes do not change between the two roots.
- Test: `roombook/tests/integration/test_composition.py` (both roots
  build the same graph; every refusal has an HTTP status and an exit
  code).

## Part V: Production Patterns

### 18. Testing the Hexagon

- Fakes, not mocks: `S/adapters/outbound/memory/`.
- One contract, two adapters:
  `roombook/tests/contract/conftest.py` (`backend` fixture
  parametrised over memory and postgres), `backends.py`,
  `test_unit_of_work.py`. Output: `pytest-contract.txt`.
- PostgreSQL via testcontainers: `roombook/tests/conftest.py`
  (`testcontainers.community.postgres`, `driver="psycopg"`,
  migrations applied with Alembic's API, `TRUNCATE` per test).
- Markers: `@pytest.mark.postgres`; `pytest -m "not postgres"`.
- Outputs for a same-run comparison: `pytest-unit.txt`,
  `pytest-not-postgres.txt`, `pytest-all.txt` (durations are one
  machine's single run; quote them as a ratio within one file, not
  as absolutes).

### 19. Transactions and the Unit of Work

- Port: `UnitOfWork` in `S/application/ports.py`.
- SQLAlchemy: `S/adapters/outbound/sqlalchemy/unit_of_work.py`
  (`close()` rolls back anything uncommitted).
- In memory: `S/adapters/outbound/memory/unit_of_work.py`.
- The race: `roombook/tests/integration/test_double_booking.py`
  (`CheckThenWait` and `RacingUnitOfWork` use `@override` and an
  `asyncio.Barrier` so both holds pass the domain check; Postgres
  refuses one; the loser's `__cause__` is `IntegrityError`).
  Output: `docs/outputs/roombook/concurrency.txt`.
- Translation: `SqlAlchemyBookingRepository.add`.
- Idempotency keys: `Idempotency-Key` header in the Coinwren
  client; idempotent `Booking.confirm`; `processed_messages`.

### 20. Errors That Cross Boundaries

- Hierarchy: `S/domain/errors.py`; port error
  `PaymentUnavailable` in `S/application/ports.py`.
- HTTP: `PROBLEMS` in `S/adapters/inbound/http/problems.py`.
- CLI: `EXIT_CODES` in `S/adapters/inbound/cli/commands.py`
  (2 bad input, 3 not found, 4 conflict, 5 payments down).
- Consumer: `PERMANENT_FAILURES` in
  `S/adapters/inbound/messaging/coinwren.py` (dead-letter);
  anything else raises, `NACK_ON_ERROR` redelivers.
- Provider errors never leak: `CoinwrenPaymentGateway`; SQL errors
  never leak: `SqlAlchemyBookingRepository.add`.
- Outputs: `curl-hold.txt` (409, 404), `cli-hold-conflict.txt`
  (exit 4), `cli-hold-closed.txt` (exit 2).

### 21. Events, the Outbox, and Messaging

- Events recorded on the aggregate (`S/domain/booking.py`), handed
  to the `Outbox` port in each use case before `commit()`.
- Serialisation: `S/adapters/outbound/outbox/messages.py`
  (`to_message`, recursive `type Json`).
- Same transaction: `SqlAlchemyOutbox` in
  `S/adapters/outbound/sqlalchemy/repositories.py`.
- Relay: `S/adapters/outbound/outbox/relay.py` (`OutboxRelay`,
  `FOR UPDATE SKIP LOCKED`, `kafka_publisher` with key and
  `message-id` header). At-least-once.
- Idempotent consumer: `CoinwrenConsumer` +
  `S/adapters/outbound/sqlalchemy/processed.py`
  (`INSERT ... ON CONFLICT DO NOTHING`). Duplicates between a
  successful confirm and `remember()` are absorbed by
  `Booking.confirm` being idempotent for the same payment id.
- Tests: `roombook/tests/integration/test_outbox_relay.py`,
  `test_coinwren_consumer.py`.
- Outputs: `outbox-relay.txt` (relay log + the topic, keyed, with
  headers), `consumer.txt` (one payment delivered twice: applied
  once, duplicate skipped).

### 22. Observability Without Touching the Domain

- `S/adapters/outbound/observability/tracing.py`:
  `configure_tracing` (sets the global provider; FastAPI 0.162's
  native telemetry picks it up, so the contrib FastAPI instrumentor
  is not used and not installed: using both doubles every server
  span), `instrument_engine`, `TracedPaymentGateway`,
  `TracedNotifier` (decorators that satisfy the same Protocol).
- `instrument_engine` passes `skip_dep_check=True`:
  `opentelemetry-instrumentation-sqlalchemy 0.66b2` declares
  `sqlalchemy < 2.1.0` and silently instruments nothing on 2.1.8.
  `roombook/tests/integration/test_tracing.py::
  test_sqlalchemy_2_1_statements_are_traced` proves the spans
  (`connect`, `SELECT`) are produced.
- `S/adapters/outbound/observability/logs.py`: structlog with
  `merge_contextvars`; library loggers on plain stdlib.
- Correlation id: `S/adapters/inbound/http/correlation.py` (pure
  ASGI middleware, `bound_contextvars`, `X-Correlation-ID`).
- Output: `docs/outputs/roombook/api-log.txt` (correlation ids match
  the responses in `curl-hold.txt`).
