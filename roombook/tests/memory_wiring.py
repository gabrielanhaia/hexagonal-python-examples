"""The whole application, wired to in-memory adapters."""

from roombook.adapters.outbound.memory.fakes import (
    FakePaymentGateway,
    FixedClock,
    RecordingNotifier,
    SequentialIds,
)
from roombook.adapters.outbound.memory.unit_of_work import (
    InMemoryStore,
)
from roombook.composition import Roombook, build_roombook
from tests.support import NOW, atlas


def memory_roombook() -> Roombook:
    room = atlas()
    store = InMemoryStore(rooms={room.id: room})
    return build_roombook(
        unit_of_work=store.unit_of_work,
        payments=FakePaymentGateway(),
        notifier=RecordingNotifier(),
        clock=FixedClock(NOW),
        ids=SequentialIds(),
    )
