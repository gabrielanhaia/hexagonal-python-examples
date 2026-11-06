# Troubleshooting

The causes below are ranked by how likely they are to be the
reason a command in this repository failed for you. Error text is
quoted from real runs.

## 1. Docker is not running

Anything that starts a container fails: `docker compose`, the
`docker run` commands in the READMEs, and every `roombook` test
marked `postgres` (testcontainers starts `postgres:18.6-trixie`
for them). Testcontainers reports:

```text
docker.errors.DockerException: Error while fetching server API
version: ('Connection aborted.', FileNotFoundError(2, 'No such
file or directory'))
```

Start Docker Desktop (or the Docker daemon) and check with
`docker info`. To run the rest of the `roombook` suite without
Docker: `uv run pytest -m "not postgres"`.

## 2. Python older than 3.14

Every project declares `requires-python = ">=3.14"`:

```text
error: The requested interpreter resolved to Python 3.13.18,
which is incompatible with the project's Python requirement:
`>=3.14` (from `project.requires-python`)
```

Let uv fetch one: `uv python install 3.14`. Each project has a
`.python-version` of `3.14`, so `uv sync` then picks it up.

## 3. A different uv version

The repository is tested with uv 0.13.7. Older releases may
still read the lock files (0.8.8 did, in a spot check), but they
resolve and build differently, and `uv sync --locked` refuses to
proceed if your uv would write a different `uv.lock`. Install the
pinned version, or run inside the uv image:

```bash
uv self update 0.13.7   # standalone installs only
```

With Homebrew or pip, upgrade uv through them instead.

uv 0.13 defaults to Python 3.15 for new work. That is why every
project pins 3.14 in `.python-version`; do not delete the file.

## 4. `lint-imports` cannot find the package

```text
Could not find package 'roombook' in your Python path.
```

The project is not installed in the environment you ran from. Run
`uv sync --locked` in that project's directory first, and run
`uv run lint-imports` from the same directory.

## 5. A `.venv` shared between macOS and a Linux container

If you run `uv sync` on the host and then mount the same project
into a container, uv in the container finds a virtualenv that
points at the host's interpreter, deletes it and builds a Linux
one in its place, which breaks the host's copy:

```text
warning: Ignoring existing virtual environment linked to
non-existent Python interpreter: `.venv/bin/python` ->
`/opt/homebrew/opt/python@3.14/bin/python3.14`
Removed virtual environment at: .venv
```

Keep the container's environment out of the mounted tree, as the
READMEs do:

```bash
-e UV_PROJECT_ENVIRONMENT=/tmp/venv
```

## 6. Apple Silicon and image platforms

Every image used here publishes `linux/arm64` as well as
`linux/amd64` (`python:3.14.10-slim-trixie`,
`postgres:18.6-trixie`, the uv image, `apache/kafka:4.4.0`), so
nothing should run under emulation. If containers are slow or
fail with `exec format error`, check for a forced platform:

```bash
echo "$DOCKER_DEFAULT_PLATFORM"   # should be empty
```

## 7. A port is already taken

`docker compose` publishes the API on port 8000; PostgreSQL is
not published, so a local PostgreSQL on 5432 does not conflict,
and testcontainers picks a free random host port. If 8000 is
busy, stop the other process (`lsof -i :8000` shows it) or run
`uvicorn` with `--port 8001` in the single-project examples.

## 8. `ch01` or `ch24` remembers old data

These run on SQLite and create `roombook.db` in the directory you
start them from (ignored by git). Delete it to start clean. The
tests never touch it: they use a temporary database.

## 9. A `lint-imports` failure that is supposed to happen

`ch07/violation` exists to break a contract, and
`ch25/violation.patch` breaks one when applied. CI expects the
first to fail (`[tool.companion] lint-imports = "must-fail"` in
its `pyproject.toml`). Remove the patch with
`git apply -R ch25/violation.patch`.
