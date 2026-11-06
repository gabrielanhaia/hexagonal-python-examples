# ch03 — Protocol ports, ABC ports, and mypy

Chapter 3. Three small, runnable files and one that exists to be
rejected.

| File                        | Shows                                  |
|-----------------------------|----------------------------------------|
| `protocol_port.py`          | a `Clock` port as a `typing.Protocol`; |
|                             | adapters match it without importing it |
| `abc_port.py`               | the same port as an `abc.ABC`; adapters |
|                             | must inherit, and an incomplete one    |
|                             | fails at instantiation                 |
| `runtime_checkable_trap.py` | `@runtime_checkable` accepts a clock   |
|                             | whose `now()` returns a `str`: it      |
|                             | checks that the member exists, nothing |
|                             | more                                   |
| `wrong_adapter.py`          | the same wrong clock passed to a       |
|                             | `Clock` parameter; mypy rejects it     |

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
