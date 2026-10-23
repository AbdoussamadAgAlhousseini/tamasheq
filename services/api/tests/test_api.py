from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db import get_session
from app.main import create_app


class _BrokenSession:
    def execute(self, *_: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("connexion refusée"))


def test_health_reports_unavailable_database() -> None:
    app = create_app()

    def broken() -> Iterator[Session]:
        yield _BrokenSession()  # type: ignore[misc]

    app.dependency_overrides[get_session] = broken
    response = TestClient(app).get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}


def test_no_capability_claimed_before_evaluation() -> None:
    response = TestClient(create_app()).get("/api/v1/capabilities")
    assert response.status_code == 200
    statuses = {c["name"]: c["status"] for c in response.json()}
    # Sans clé de modèle : seules les fonctions sans IA sont actives, et aucune ne se dit évaluée.
    assert statuses == {
        "chat": "not_available",
        "dictionary": "experimental",
        "translation": "not_available",
        "knowledge": "experimental",
        "knowledge_qa": "not_available",
        "asr": "not_available",
        "tts": "not_available",
    }
