"""Structured logs on stderr, carrying the correlation id."""

import logging
import sys

import structlog

LIBRARY_LOGGER = "roombook.libraries"


def configure_logging(*, as_json: bool) -> None:
    """structlog for our code; plain stdlib for the libraries."""
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    logging.getLogger(LIBRARY_LOGGER).setLevel(logging.INFO)
    renderer = (
        structlog.processors.JSONRenderer()
        if as_json
        else structlog.dev.ConsoleRenderer(colors=False)
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            renderer,
        ],
        logger_factory=structlog.PrintLoggerFactory(sys.stderr),
    )
