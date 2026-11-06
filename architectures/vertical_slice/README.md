# architectures/vertical_slice

Jimmy Bogard's vertical slice architecture (chapter 16): one
folder per feature, each owning its endpoint, request, response,
handler and data access.

```text
features/hold_room/       endpoint, request, response,
                          handler, store
features/cancel_booking/  endpoint, request, response,
                          handler, store
kernel/                   the shared kernel: stored rows,
                          HTTP errors, dependencies
app/                      create_app(): mounts the slices
```

The slot rules live in the hold slice's Pydantic request; the
opening-hours, overlap and pricing rules live in its handler.
Nothing is shared between the slices except the kernel.

Contracts (`pyproject.toml`): an `independence` contract between
the two slices, and a `layers` contract, app -> features ->
kernel.

From the repo root, in the `examples` Compose service:

```bash
docker compose run --rm -w /repo/architectures/vertical_slice examples \
    pytest -q
docker compose run --rm -w /repo/architectures/vertical_slice examples \
    lint-imports
```

With uv on the host instead, from this directory:

```bash
uv sync --locked && uv run pytest -q && uv run lint-imports
```
