# ch25 — from one hexagon to many: a modular monolith

Chapter 25. One deployable (`roombook.app.create_app`) holding
two bounded contexts, each a small hexagon:

```text
src/roombook/booking/    domain, application, adapters/
src/roombook/billing/    domain, application, adapters/
src/roombook/contracts/  events.py: the published language
src/roombook/platform/   bus.py: the in-process event bus
src/roombook/app.py      the composition root for both
```

Booking cancels; it publishes `BookingCancelled` on the bus.
Billing subscribes and issues an invoice for a late-cancellation
fee, once per booking even if the event arrives twice. Neither
context imports the other: they share only `contracts/`.

Contracts (`pyproject.toml`):

- `independence` between `roombook.booking` and
  `roombook.billing`;
- `layers` with `containers`: inside each context,
  adapters -> application -> domain;
- `forbidden`: no web framework in either core, nor in
  `contracts/` and `platform/`.

## Watch the independence contract catch a shortcut

`violation.patch` makes billing borrow booking's fee constant
for the invoice text. The tests still pass; the contract does
not.

```bash
git apply ch25/violation.patch
cd ch25
uv run pytest -q                 # passes
uv run lint-imports --no-logo    # independence BROKEN, exit 1
cd ..
git apply -R ch25/violation.patch
```

Recorded output: `docs/outputs/ch25/`.

## Run

```bash
cd ch25
uv sync --locked
uv run pytest -q
uv run lint-imports --no-logo
```
