# ch24 — migrating the framework-shaped app, step by step

Chapter 24 takes `ch01/` to hexagonal without a flag day. Every
step is a complete, runnable project with passing tests, and
`tests/test_characterisation.py` is byte-for-byte the same file
in all five: the HTTP behaviour it pins never changes.

| Step     | What moves                                               |
|----------|----------------------------------------------------------|
| `step1/` | nothing in `app/` (identical to `ch01/app`); add         |
|          | characterisation tests over the whole HTTP API           |
| `step2/` | extract the rules into `app/domain/` (stdlib only); the  |
|          | ORM classes become `RoomRow` and `BookingRow`; routes    |
|          | call the domain                                          |
| `step3/` | add the `Booking` aggregate, the ports                   |
|          | (`app/application/ports.py`) and two adapters per port,  |
|          | proven by one contract suite; no route uses them yet     |
| `step4/` | move one route: hold goes through the `HoldRoom` use     |
|          | case; confirm and cancel are untouched                   |
| `step5/` | strangle the rest: `ConfirmBooking`, `CancelBooking`, a  |
|          | `PaymentGateway` port with a Tillpoint adapter; routes   |
|          | move to `app/adapters/http.py`, persistence to           |
|          | `app/adapters/sqlalchemy/`, and import-linter enforces   |
|          | the dependency rule                                      |

One finding from step 2: `ch01` states the hold-expiry rule twice,
in Python (`Booking.is_expired`) and in SQL (the overlap query),
and the two copies disagree at exactly 15 minutes. A hold created
exactly `HOLD_TTL` ago is "not expired" to the Python and "not
blocking" to the SQL. Step 2 derives both from one function,
`hold_cutoff`, and the disagreement goes away.

## Run any step

```bash
cd ch24/step3
uv sync --locked
uv run pytest -q
```

Step 5 also runs `uv run lint-imports --no-logo`. Recorded
output for every step: `docs/outputs/ch24/`.
