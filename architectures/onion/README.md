# architectures/onion

Jeffrey Palermo's Onion Architecture (chapter 15). The ring names
come from his 2008 diagram.

```text
domain_model/          Money, TimeSlot, Room, Booking, errors
domain_services/       repository interfaces, AvailabilityService
application_services/  BookingApplicationService, Clock interface
infrastructure/        in-memory repositories, system clock
ui/                    FastAPI routes and startup (wiring)
```

The domain model is the same code as `hexagonal/domain/`. The
difference is the extra named ring: the overlap rule spans many
bookings, so it lives in a domain service instead of the use
case.

Contracts (`pyproject.toml`): a `layers` contract from `ui` down
to `domain_model` (an outer ring may use any inner ring), and a
`forbidden` contract that keeps web frameworks out of the three
core rings.

```bash
uv sync --locked && uv run pytest -q && uv run lint-imports
```
