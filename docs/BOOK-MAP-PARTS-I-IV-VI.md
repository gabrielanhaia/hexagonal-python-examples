# Book map: chapters 1, 3, 5, 7, 14-17, 24, 25

What to quote, and which recorded output backs each printed
command. Paths are from the repository root. Every file under
`docs/outputs/` starts with the command that produced it
(`$ cd <dir> && <command>`), followed by its real output.

Conventions that apply to every recorded output:

- `lint-imports` is recorded as `uv run lint-imports --no-logo`
  (without the flag it prints an ASCII banner first).
- pytest summary lines (`14 passed in 0.06s`) carry wall-clock
  seconds from one run on one laptop. Elide the timing or treat
  it as decoration; no duration in this repo is a measurement.
- `docs/outputs/ch03/wrong_adapter-runtime.txt` is the only file
  whose paths were rewritten: the container path became
  `/path/to/hexagonal-python-examples/`.

## Chapter 1 — `ch01/`

Quote:

- `ch01/app/main.py`: `hold_room` (opening hours, the overlap
  query and pricing, all inline), `confirm_booking` (the
  Coinwren call inline, `402` on decline), `cancel_booking`,
  `get_coinwren`, `lifespan` (creates tables, seeds `atlas`).
- `ch01/app/models.py`: `Booking.is_expired` and
  `Booking.cancellation_fee` (both read `datetime.now(UTC)`
  inside the model), `HOLD_TTL`, `UTCDateTime`.
- `ch01/app/schemas.py`: `HoldIn` and its two validators.
- `ch01/app/db.py`: the engine built at import time from
  settings.
- `ch01/tests/conftest.py`: the env var set before importing the
  app, and `app.dependency_overrides` for Coinwren. Every test
  needs the database.

Output: `docs/outputs/ch01/pytest.txt`.

Usable fact for the "three change requests" trace: the
hold-expiry rule is written twice, `models.Booking.is_expired`
(Python) and the `or_(...)` in `main.hold_room` (SQL). At exactly
15 minutes they disagree: the hold is not expired, and it does
not block the slot. Chapter 24's step 2 is where it surfaces.

## Chapter 3 — `ch03/`

Quote:

- `ch03/protocol_port.py`: `Clock(Protocol)`, `SystemClock` and
  `FixedClock` with no base class, `cancellation_is_free`.
- `ch03/abc_port.py`: `Clock(ABC)`, `SystemClock(Clock)`,
  `ForgetfulClock` (no `now()`), and the `TypeError`.
- `ch03/runtime_checkable_trap.py`: `@runtime_checkable Clock`,
  `TextClock.now() -> str` passing `isinstance`, `load_clock`.
- `ch03/wrong_adapter.py`: the same `TextClock` passed to
  `cancellation_is_free`; excluded from the default mypy run in
  `ch03/pyproject.toml` (`[tool.mypy] files`).

Outputs, in `docs/outputs/ch03/`: `protocol_port.txt`,
`abc_port.txt`, `runtime_checkable_trap.txt` (shows `True`,
`False`, then `AttributeError: 'str' object has no attribute
'isoformat'`), `mypy.txt` (clean), `mypy-caught.txt` (the
structural error with the Expected/Got note, exit 1),
`wrong_adapter-runtime.txt` (the `TypeError` Python raises
instead, at runtime), `pytest.txt`.

## Chapter 5 — `ch05/`

Quote:

- `ch05/provider_shaped/ports.py`: `Database` (`fetch_one`,
  `execute` with SQL strings), `HttpClient`, `HttpResponse`.
- `ch05/provider_shaped/confirm.py`: `ConfirmBooking` with SQL
  text and status codes in the core.
- `ch05/consumer_defined/ports.py`: `BookingRepository`
  (`get`, `save`), `PaymentGateway.charge`.
- `ch05/consumer_defined/confirm.py`: the same use case in the
  domain's words.
- `ch05/consumer_defined/coinwren.py`: `CoinwrenPayments`,
  where the HTTP shape went.
- `ch05/model.py`: `Booking.can_confirm`, `Booking.confirm`.
- The fakes, side by side: `ScriptedDatabase`, `CannedResponse`,
  `ScriptedHttp` in `tests/test_provider_shaped.py` (asserts on
  SQL text) against `InMemoryBookings` and `FakePayments` in
  `tests/test_consumer_defined.py`.

Output: `docs/outputs/ch05/pytest.txt`.

## Chapter 7 — `ch07/`

Quote:

- `ch07/violation/src/roombook/domain/booking.py`: `Booking` as
  a SQLAlchemy model (the violation).
- `ch07/violation/pyproject.toml` (identical contracts in
  `ch07/fixed/pyproject.toml`): the `layers` contract and the
  `forbidden` contract with `include_external_packages = true`;
  plus `[tool.companion] lint-imports = "must-fail"`.
- `ch07/fixed/src/roombook/domain/booking.py`: the plain
  dataclass.
- `ch07/fixed/src/roombook/adapters/sqlalchemy/records.py`:
  `BookingRecord`, `to_domain`, `to_record`.
- `.github/workflows/ci.yml`, job `pinned`, step
  `import-linter`: how CI requires the violation to stay broken.

Outputs, in `docs/outputs/ch07/`: `violation-lint-imports.txt`
(`The domain imports no framework BROKEN`,
`roombook.domain.booking -> sqlalchemy (l.3, l.4)`, exit 1),
`fixed-lint-imports.txt` (2 kept), `violation-pytest.txt` and
`fixed-pytest.txt` (both pass: only the contract notices).

## Chapters 14-17 — `architectures/`

Shared facts:

- Same HTTP API, same rules, same 14 scenarios in every variant:
  `architectures/<variant>/tests/test_scenarios.py` is
  byte-identical (sha256 prefix `e8b537dacbf5`, checked by
  `measure.py`). Only `tests/conftest.py` differs.
- The entity code of `hexagonal/domain/`, `onion/domain_model/`
  and `clean/entities/` is the same file set; `diff -r` shows
  only import lines. The architectures differ around it.
- Storage is in memory everywhere except `layered/` (SQLAlchemy
  2.1 on in-memory SQLite via aiosqlite 0.22.1).

### Chapter 14 — Clean (`architectures/clean/`)

- `use_cases/hold_room.py`: `HoldRoomRequest`,
  `HoldRoomResponse`, `HoldRoomInputBoundary`,
  `HoldRoomOutputBoundary`, `HoldRoomInteractor` (explicitly
  subclasses its input boundary, `@override`).
- `use_cases/failures.py`: `FailureKind`, `Failure`,
  `failure_from`.
- `use_cases/gateways.py`: `RoomGateway`, `BookingGateway`,
  `Clock`.
- `interface_adapters/controllers.py`: `HoldRoomController`.
- `interface_adapters/presenters.py`: `ViewModel`, `STATUS_FOR`,
  `HoldRoomPresenter`, `CancelBookingPresenter`.
- `frameworks/web.py`: per-request wiring of presenter,
  interactor and controller; `render`. The routes return
  `JSONResponse`, so FastAPI's OpenAPI schema loses the response
  models: a measurable cost of presenters under FastAPI.
- `frameworks/main.py`: `create_app`.
- Compare with `architectures/hexagonal/application/hold_room.py`
  (`HoldRoom`, returns the `Booking`) and
  `architectures/hexagonal/adapters/http.py` (`http_error`).
- Outputs: `docs/outputs/architectures/clean-pytest.txt`,
  `clean-lint-imports.txt`, and the `hexagonal-*` pair.

### Chapter 15 — Onion (`architectures/onion/`)

- `domain_services/availability.py`: `AvailabilityService`
  (`ensure_free`), the overlap rule as a domain service.
- `domain_services/repositories.py`: repository interfaces in
  the core.
- `application_services/booking_service.py`:
  `BookingApplicationService` (`hold_room`, `cancel_booking`),
  `Cancellation`.
- `ui/startup.py`: `create_app`, wiring in the outer ring.
- `pyproject.toml`: `layers` from `ui` down to `domain_model`.
- Outputs: `docs/outputs/architectures/onion-*.txt`.

### Chapter 16 — Layered and vertical slices

`architectures/layered/`:

- `data_access/models.py`: `Room`, `Booking` ORM models,
  `BookingStatus`, `ACTIVE`, `UTCDateTime`.
- `data_access/bookings.py`: `BookingDAO.has_overlap`.
- `services/booking_service.py`: `BookingService.hold_room`,
  `cancel_booking`, `check_slot`, `is_open`.
- `presentation/api.py`: `booking_service` (a session per
  request), `http_error`. `presentation/app.py`: `create_app`.

`architectures/vertical_slice/`:

- `features/hold_room/request.py`: `HoldRoomRequest` with the
  slot rules as Pydantic validators.
- `features/hold_room/handler.py`: `hold_room`, a transaction
  script.
- `features/hold_room/store.py`: `HoldRoomStore`.
- `features/cancel_booking/`: the same five files for cancel.
- `kernel/database.py`, `kernel/errors.py`,
  `kernel/dependencies.py`: the whole shared kernel.
- `pyproject.toml`: the `independence` contract.

Outputs: `docs/outputs/architectures/layered-*.txt`,
`vertical_slice-*.txt`.

### Chapter 17 — `architectures/measure.py`

Recorded in `docs/outputs/architectures/measure.txt`:

```text
variant          files  lines  classes  protos  tests  touched
layered             11    339       21       0     14        3
hexagonal           15    364       29       3     14        3
onion               17    381       28       3     14        3
clean               18    536       40       7     14        3
vertical_slice      19    261       14       0     14        2
```

How to read it, as `measure.py` defines it: production code
only (`tests/` excluded); `files` counts every `.py` file,
including empty `__init__.py`; `lines` are non-blank,
non-comment lines (docstrings count); `classes` includes
Pydantic models and error classes; `protos` counts classes with
`Protocol` as a base. `touched` is the file count of the
max-length rule commit, and in every variant one of those files
is the shared `tests/test_scenarios.py`.

The rule commits: `git log --oneline --grep "may not exceed 4
hours"`. Where the rule landed is tabled in
`architectures/add-max-length-rule.md`. No durations were
measured.

## Chapter 24 — `ch24/step1` to `ch24/step5`

- Invariant: `tests/test_characterisation.py` is byte-identical
  in all five steps (17 tests).
- step1: `app/` is byte-identical to `ch01/app`.
  `tests/conftest.py`: `FakeCoinwren`, `age_hold`.
- step2: `app/domain/booking.py` (`hold_cutoff`, `hold_expired`,
  `cancellation_fee`), `app/domain/room.py`
  (`OpeningHours.contain`, `Room.price_for`),
  `app/domain/values.py` (`Money`, `TimeSlot`); `app/main.py`
  (`to_room`, routes calling the domain). The ORM classes become
  `RoomRow` and `BookingRow`. This is where the two copies of the
  expiry rule are made to agree (see chapter 1).
- step3: `app/domain/booking.py` (`Booking.hold`, `is_expired`,
  `blocks_slot`, `expire`, `confirm`, `cancel`),
  `app/application/ports.py`,
  `app/adapters/sqlalchemy_repository.py` (`to_booking`,
  `to_row`), `app/adapters/memory.py`,
  `tests/contract/test_booking_repository.py` (one suite, two
  adapters). No route uses them yet.
- step4: `app/application/hold_room.py` (`HoldRoom`);
  `app/main.py` (`get_hold_room`, `http_error`, `booking_out`)
  next to the untouched confirm and cancel routes.
- step5: `app/application/confirm_booking.py`,
  `app/application/cancel_booking.py`,
  `app/adapters/http.py`, `app/adapters/coinwren.py`,
  `app/adapters/schemas.py` (`BookingOut.of`), `app/main.py`
  (composition root), and the contracts in `pyproject.toml`.

Outputs, in `docs/outputs/ch24/`: `step1-pytest.txt` (21) to
`step5-pytest.txt` (48), `step5-lint-imports.txt` (2 kept), and
`app-diff-step1-step2.txt` to `app-diff-step4-step5.txt`
(`git diff --no-index --stat` between consecutive `app/` trees).

## Chapter 25 — `ch25/`

Quote:

- `ch25/src/roombook/contracts/events.py`: `BookingCancelled`.
- `ch25/src/roombook/platform/bus.py`: `EventBus`
  (`subscribe`, `publish`).
- `ch25/src/roombook/booking/application.py`: `CancelBooking`
  publishing through the `Events` port.
- `ch25/src/roombook/billing/application.py`:
  `IssueCancellationInvoice` (idempotent per booking).
- `ch25/src/roombook/app.py`: `create_app`, the one place both
  contexts meet (`bus.subscribe(...)`).
- `ch25/pyproject.toml`: `independence`, `layers` with
  `containers`, `forbidden`.
- `ch25/violation.patch`: billing borrows booking's
  `LATE_CANCELLATION_FEE`.

Outputs, in `docs/outputs/ch25/`: `pytest.txt`,
`lint-imports.txt` (3 kept), `violation-lint-imports.txt`
(`Booking and billing are independent BROKEN`,
`roombook.billing.application -> roombook.booking.domain
(l.5)`), `violation-pytest.txt` (still passes: tests do not
notice the shortcut).
