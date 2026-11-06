# The change-cost experiment: "a booking may not exceed 4 hours"

Chapter 17 compares the five variants by adding one new business
rule to each and counting what moved. The rule:

> A booking may not last longer than four hours. A request for
> more is rejected with 422; exactly four hours is accepted.

Each variant got the rule in its own commit on `main`, with the
subject `architectures/<variant>: a booking may not exceed 4
hours`. Two scenarios were added to the shared
`tests/test_scenarios.py` in the same commits (13 and 14 in
`architectures/README.md`), so the file stays identical in all
five.

## See the commits

```bash
git log --oneline --grep "may not exceed 4 hours"
git show --stat <commit>
```

`measure.py` reads the same commits and lists the touched files
per variant.

## Where the rule landed

| Variant           | Rule lives in                          |
|-------------------|----------------------------------------|
| `layered/`        | `BookingService.hold_room`             |
| `hexagonal/`      | `Booking.hold` in the domain           |
| `onion/`          | `Booking.hold` in the domain model     |
| `clean/`          | `Booking.hold` in the entities         |
| `vertical_slice/` | the hold slice's Pydantic request      |

In `layered/`, `hexagonal/`, `onion/` and `clean/` the rule also
added a `BookingTooLong` error class. It subclasses the existing
"invalid booking" error, so the code that maps errors to HTTP
status codes (the route in `layered/` and `hexagonal/`, the
interactor's `failure_from` in `clean/`) did not change. In
`vertical_slice/` the rule is a Pydantic validator, and FastAPI
turns its `ValueError` into a 422 without new code.

## Reproduce from scratch

To redo the experiment on your own branch, check out the commit
before each rule commit, add the rule your way, and run:

```bash
uv run pytest -q
git diff --stat
```
