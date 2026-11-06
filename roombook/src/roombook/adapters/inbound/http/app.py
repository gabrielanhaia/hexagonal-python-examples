"""The FastAPI application, minus its wiring."""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI
from starlette.middleware import Middleware

from roombook.adapters.inbound.http.correlation import (
    CorrelationIdMiddleware,
)
from roombook.adapters.inbound.http.dependencies import UseCases
from roombook.adapters.inbound.http.problems import (
    PROBLEMS,
    problem_response,
)
from roombook.adapters.inbound.http.routes import router

type State = dict[str, UseCases]
type Lifespan = Callable[
    [FastAPI], AbstractAsyncContextManager[State]
]


def create_app(lifespan: Lifespan) -> FastAPI:
    """`lifespan` must yield {"use_cases": <UseCases>}."""
    app = FastAPI(
        title="roombook",
        lifespan=lifespan,
        exception_handlers={
            error: problem_response for error in PROBLEMS
        },
        middleware=[Middleware(CorrelationIdMiddleware)],
    )
    app.include_router(router)
    return app
