import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.db import get_engine
from app.main import create_app


@pytest.fixture
def alembic_config() -> Config:
    return Config("alembic.ini")


def test_migrations_upgrade_and_downgrade(database_available: bool, alembic_config: Config) -> None:
    if not database_available:
        pytest.skip("TEST_DATABASE=1 requis")
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    assert "users" in inspect(get_engine()).get_table_names()
    command.downgrade(alembic_config, "base")
    assert "users" not in inspect(get_engine()).get_table_names()
    command.upgrade(alembic_config, "head")


def test_health_with_database(database_available: bool) -> None:
    if not database_available:
        pytest.skip("TEST_DATABASE=1 requis")
    response = TestClient(create_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
