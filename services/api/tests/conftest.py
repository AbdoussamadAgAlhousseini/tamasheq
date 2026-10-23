import os
from collections.abc import Iterator

import pytest

from app.config import get_settings
from app.db import get_engine


@pytest.fixture(scope="session")
def database_available() -> bool:
    """Les tests marqués `db` nécessitent PostgreSQL ; ils sont ignorés sans TEST_DATABASE=1."""
    return os.environ.get("TEST_DATABASE") == "1"


@pytest.fixture(autouse=True)
def _reset_caches() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_engine.cache_clear()
