# architectures/clean

Robert C. Martin's Clean Architecture (chapter 14), built with
every type the 2012 diagram names.

```text
entities/            Money, TimeSlot, Room, Booking, errors
use_cases/           interactors, input and output boundaries,
                     request and response models, gateways
interface_adapters/  controllers, presenters, in-memory gateways
frameworks/          FastAPI routes, create_app(), system clock
```

Control flows controller -> interactor -> presenter, while every
source dependency points inward: the interactor calls the output
boundary, and the presenter implements it. Only plain request and
response models cross the use-case boundary, never an entity.
The presenter builds a `ViewModel`; the route renders it.

Contracts (`pyproject.toml`): a `layers` contract,
frameworks -> interface_adapters -> use_cases -> entities, and a
`forbidden` contract that keeps fastapi, pydantic and starlette
out of everything but `frameworks/`.

From the repo root, in the `examples` Compose service:

```bash
docker compose run --rm -w /repo/architectures/clean examples \
    pytest -q
docker compose run --rm -w /repo/architectures/clean examples \
    lint-imports
```

With uv on the host instead, from this directory:

```bash
uv sync --locked && uv run pytest -q && uv run lint-imports
```
