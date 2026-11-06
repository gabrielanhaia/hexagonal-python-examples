FROM python:3.14.10-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependencies first, so editing code does not reinstall them.
COPY pyproject.toml uv.lock .python-version README.md ./
RUN uv sync --locked --no-install-project

COPY . .
RUN uv sync --locked

RUN useradd --uid 10001 --no-create-home roombook \
    && chown -R roombook /app
USER roombook

ENTRYPOINT ["roombook"]
