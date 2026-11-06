# ch24/step1 — characterisation tests first

`app/` is byte-for-byte `ch01/app`. What is new is
`tests/test_characterisation.py`: seventeen tests that pin the
HTTP API as it behaves today, status codes and bodies, including
the awkward parts (an expired hold is written as `EXPIRED` when
someone tries to confirm it). The same file runs unchanged in
every later step.

From the repo root, in the `examples` Compose service:

```bash
docker compose run --rm -w /repo/ch24/step1 examples pytest -q
```

With uv on the host instead, from this directory:

```bash
uv sync --locked && uv run pytest -q
```
