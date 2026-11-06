# ch03 — Protocol ports, ABC ports, and mypy

Chapter 3. Three small, runnable files and one that exists to be
rejected.

- `protocol_port.py`: a `Clock` port as a `typing.Protocol`;
  the adapters match it without importing it.
- `abc_port.py`: the same port as an `abc.ABC`; every adapter
  must inherit from it, and an incomplete one fails when it is
  instantiated.
- `runtime_checkable_trap.py`: `@runtime_checkable` accepts a
  clock whose `now()` returns a `str`. It checks that the member
  exists, nothing more.
- `wrong_adapter.py`: the same wrong clock passed to a `Clock`
  parameter. mypy rejects it; Python only fails at runtime.

From the repo root, in the `examples` Compose service:

```bash
docker compose run --rm -w /repo/ch03 examples \
    python protocol_port.py
docker compose run --rm -w /repo/ch03 examples \
    python abc_port.py
docker compose run --rm -w /repo/ch03 examples \
    python runtime_checkable_trap.py
docker compose run --rm -w /repo/ch03 examples \
    mypy                    # clean: wrong_adapter.py excluded
docker compose run --rm -w /repo/ch03 examples \
    mypy wrong_adapter.py   # fails, on purpose
docker compose run --rm -w /repo/ch03 examples \
    python wrong_adapter.py # fails later, at runtime
docker compose run --rm -w /repo/ch03 examples \
    pytest -q
```

With uv on the host instead:

```bash
cd ch03
uv sync --locked
uv run python protocol_port.py
uv run python abc_port.py
uv run python runtime_checkable_trap.py
uv run mypy                    # clean: wrong_adapter.py excluded
uv run mypy wrong_adapter.py   # fails, on purpose
uv run python wrong_adapter.py # fails later, at runtime
uv run pytest -q
```

Recorded output for every command: `docs/outputs/ch03/`.
