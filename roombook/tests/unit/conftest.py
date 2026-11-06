import pytest

from roombook.adapters.outbound.memory.fakes import (
    FakePaymentGateway,
    FixedClock,
    RecordingNotifier,
    SequentialIds,
)
from roombook.adapters.outbound.memory.unit_of_work import (
    InMemoryStore,
)
from roombook.application.cancel_booking import CancelBooking
from roombook.application.confirm_booking import ConfirmBooking
from roombook.application.expire_stale_holds import ExpireStaleHolds
from roombook.application.hold_room import HoldRoom
from roombook.application.list_availability import ListAvailability
from tests.support import NOW, atlas


@pytest.fixture
def store() -> InMemoryStore:
    room = atlas()
    return InMemoryStore(rooms={room.id: room})


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def payments() -> FakePaymentGateway:
    return FakePaymentGateway()


@pytest.fixture
def notifier() -> RecordingNotifier:
    return RecordingNotifier()


@pytest.fixture
def hold_room(
    store: InMemoryStore,
    payments: FakePaymentGateway,
    clock: FixedClock,
) -> HoldRoom:
    return HoldRoom(
        unit_of_work=store.unit_of_work,
        payments=payments,
        clock=clock,
        ids=SequentialIds(),
    )


@pytest.fixture
def confirm_booking(
    store: InMemoryStore,
    notifier: RecordingNotifier,
    clock: FixedClock,
) -> ConfirmBooking:
    return ConfirmBooking(
        unit_of_work=store.unit_of_work,
        notifier=notifier,
        clock=clock,
    )


@pytest.fixture
def cancel_booking(
    store: InMemoryStore,
    notifier: RecordingNotifier,
    clock: FixedClock,
) -> CancelBooking:
    return CancelBooking(
        unit_of_work=store.unit_of_work,
        notifier=notifier,
        clock=clock,
    )


@pytest.fixture
def list_availability(store: InMemoryStore) -> ListAvailability:
    return ListAvailability(unit_of_work=store.unit_of_work)


@pytest.fixture
def expire_stale_holds(
    store: InMemoryStore,
    notifier: RecordingNotifier,
    clock: FixedClock,
) -> ExpireStaleHolds:
    return ExpireStaleHolds(
        unit_of_work=store.unit_of_work,
        notifier=notifier,
        clock=clock,
    )
