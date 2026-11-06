from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

type Handler[E] = Callable[[E], Awaitable[None]]


class EventBus:
    """In-process delivery inside one deployable, in order.

    A handler that raises stops the publish; there is no retry
    and no outbox here (chapter 21 adds both).
    """

    def __init__(self) -> None:
        self._handlers: defaultdict[type, list[Handler[Any]]] = (
            defaultdict(list)
        )

    def subscribe[E](
        self, event_type: type[E], handler: Handler[E]
    ) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: object) -> None:
        for handler in self._handlers[type(event)]:
            await handler(event)
