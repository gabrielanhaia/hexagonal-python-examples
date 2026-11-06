"""Give every request a correlation id, in logs and headers."""

import uuid

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

HEADER = "X-Correlation-ID"

log = structlog.get_logger()


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        incoming = Headers(scope=scope).get(HEADER)
        correlation_id = incoming or str(uuid.uuid4())

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[HEADER] = (
                    correlation_id
                )
                await log.ainfo(
                    "request",
                    method=scope["method"],
                    path=scope["path"],
                    status=message["status"],
                )
            await send(message)

        with structlog.contextvars.bound_contextvars(
            correlation_id=correlation_id
        ):
            await self._app(scope, receive, send_with_id)
