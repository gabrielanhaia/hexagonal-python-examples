import pytest

from tests.contract.backends import (
    Backend,
    MemoryBackend,
    PostgresBackend,
)
from tests.support import atlas


@pytest.fixture(
    params=[
        "memory",
        pytest.param("postgres", marks=pytest.mark.postgres),
    ]
)
def backend(request: pytest.FixtureRequest) -> Backend:
    """Every contract test runs once per adapter."""
    if request.param == "memory":
        return MemoryBackend()
    return PostgresBackend(request.getfixturevalue("sessions"))


@pytest.fixture(autouse=True)
async def with_a_room(backend: Backend) -> None:
    await backend.add_room(atlas())
