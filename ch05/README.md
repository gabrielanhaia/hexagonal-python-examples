# ch05 — a provider-shaped port and its consumer-defined rewrite

Chapter 5. One use case, confirming a held booking, written twice.

- `provider_shaped/`: the core talks to ports shaped like the
  tools behind them, a database driver (`fetch_one`, `execute`
  with SQL strings) and an HTTP client (`post`, `status_code`,
  `json()`). The SQL and the HTTP status codes live in the core.
- `consumer_defined/`: the core writes the ports it needs, in its
  own words: `BookingRepository.get/save` and
  `PaymentGateway.charge`. The HTTP shape moves into a driven
  adapter, `consumer_defined/coinwren.py`.

Compare the fakes in `tests/`: the provider-shaped test needs a
scripted database and a canned HTTP response, and it asserts on
SQL text. The consumer-defined fakes are a dict and a list.

From the repo root, in the `examples` Compose service:

```bash
docker compose run --rm -w /repo/ch05 examples pytest -q
docker compose run --rm -w /repo/ch05 examples mypy
```

With uv on the host instead:

```bash
cd ch05
uv sync --locked
uv run pytest -q
uv run mypy
```
