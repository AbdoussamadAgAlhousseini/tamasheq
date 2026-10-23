import os
from collections.abc import Iterator

import pytest

from app.config import get_settings
from app.db import get_engine
from app.routers.chat import get_chat_provider, get_limiter


@pytest.fixture(scope="session")
def database_available() -> bool:
    """Les tests marqués `db` nécessitent PostgreSQL ; ils sont ignorés sans TEST_DATABASE=1."""
    return os.environ.get("TEST_DATABASE") == "1"


@pytest.fixture(autouse=True)
def _no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Les tests n'utilisent jamais une vraie clé, même si l'environnement en contient une."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.delenv("ANTHROPIC_API_KEY")


@pytest.fixture(autouse=True)
def _reset_caches() -> Iterator[None]:
    for cached in (get_settings, get_chat_provider, get_limiter):
        cached.cache_clear()
    yield
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_engine.cache_clear()
