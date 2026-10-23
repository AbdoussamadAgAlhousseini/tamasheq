import os
from collections.abc import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import issue_token
from app.config import get_settings
from app.db import get_engine
from app.models import Role, User
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


@pytest.fixture(scope="session")
def migrated(database_available: bool) -> None:
    if not database_available:
        pytest.skip("TEST_DATABASE=1 requis")
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config("alembic.ini"), "head")


CONTENT_TABLES = (
    "dataset_items, datasets, revisions, lexical_examples, lexical_senses, lexical_spellings, "
    "lexical_entries, corpus_texts, orthography_conventions, sources, api_tokens, users"
)


@pytest.fixture
def db(migrated: None) -> Iterator[Session]:
    """Base vide pour chaque test (TRUNCATE ne déclenche pas les triggers de ligne)."""
    with get_engine().begin() as connection:
        connection.execute(text(f"TRUNCATE {CONTENT_TABLES} RESTART IDENTITY CASCADE"))
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session


def make_user(session: Session, role: Role, name: str) -> tuple[User, str]:
    user = User(email=f"{name}@test.invalid", pseudonym=name, role=role)
    session.add(user)
    session.flush()
    token = issue_token(session, user)
    session.commit()
    return user, token
