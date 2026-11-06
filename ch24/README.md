# ch24 — migrating the framework-shaped app, step by step

Chapter 24 takes `ch01/` to hexagonal without a flag day. Every
step is a complete, runnable project with passing tests, and
`tests/test_characterisation.py` is byte-for-byte the same file
in all five: the HTTP behaviour it pins never changes.

- `step1/`: nothing in `app/` moves (it is identical to
  `ch01/app`); characterisation tests cover the whole HTTP API.
- `step2/`: the rules move into `app/domain/` (standard library
  only); the ORM classes become `RoomRow` and `BookingRow`; the
  routes call the domain.
- `step3/`: the `Booking` aggregate, the ports
  (`app/application/ports.py`) and two adapters per port, proven
  by one contract suite. No route uses them yet.
- `step4/`: one route moves. Hold goes through the `HoldRoom`
  use case; confirm and cancel are untouched.
- `step5/`: the rest is strangled. `ConfirmBooking`,
  `CancelBooking` and a `PaymentGateway` port with a Tillpoint
  adapter; routes move to `app/adapters/http.py`, persistence to
  `app/adapters/sqlalchemy/`, and import-linter enforces the
  dependency rule.

One finding from step 2: `ch01` states the hold-expiry rule twice,
in Python (`Booking.is_expired`) and in SQL (the overlap query),
and the two copies disagree at exactly 15 minutes. A hold created
exactly `HOLD_TTL` ago is "not expired" to the Python and "not
blocking" to the SQL. Step 2 derives both from one function,
`hold_cutoff`, and the disagreement goes away.

## Run any step

From the repo root, in the `examples` Compose service:

```bash
docker compose run --rm -w /repo/ch24/step3 examples pytest -q
```

With uv on the host instead:

```bash
cd ch24/step3
uv sync --locked
uv run pytest -q
```

Step 5 also runs `lint-imports --no-logo`. Recorded
output for every step: `docs/outputs/ch24/`.
