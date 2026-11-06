from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from roombook.app import create_app

NOW = datetime(2026, 11, 9, 9, 0, tzinfo=UTC)


class FixedClock:
    def now(self) -> datetime:
        return NOW


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(clock=FixedClock())) as client:
        yield client
