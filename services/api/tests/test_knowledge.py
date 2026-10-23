from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.ai.knowledge_qa import Answer, Passage
from app.main import create_app
from app.models import Role, Source, SourceKind, Status
from app.ratelimit import SlidingWindowLimiter
from app.routers.chat import get_limiter
from app.routers.knowledge import get_answer_provider
from app.schemas import KnowledgeDocumentIn
from app.services.knowledge import chunk_text, create_document, query_terms
from tests.conftest import make_user

# Documents factices : aucun savoir touareg n'est inventé, même pour les tests.


def test_chunking_keeps_text_and_bounds() -> None:
    body = "Premier paragraphe court.\n\nSecond paragraphe court.\n\n" + " ".join(
        f"Phrase numéro {i} du long paragraphe." for i in range(100)
    )
    chunks = chunk_text(body, max_chars=300)
    assert all(len(c) <= 300 for c in chunks)
    assert chunks[0] == "Premier paragraphe court.\n\nSecond paragraphe court."
    assert " ".join(" ".join(chunks).split()) == " ".join(body.split())
    assert chunk_text("x" * 650, max_chars=300) == ["x" * 300, "x" * 300, "x" * 50]


def test_query_terms_are_safe() -> None:
    assert query_terms("Quels sont les usages de ZZALPHA ?") == ["usages", "zzalpha"]
    assert query_terms("a & b | !c :* 'd'") == []  # ni opérateurs tsquery ni mots d'une lettre
    assert query_terms("zz:* | zz") == ["zz"]


class FakeAnswers:
    name = "fake"

    def __init__(self, cite: list[str] | None = None) -> None:
        self.cite = cite
        self.passages: list[Passage] | None = None

    async def answer(self, question: str, passages: list[Passage]) -> Answer:
        self.passages = passages
        cited = self.cite if self.cite is not None else [p.ref for p in passages]
        return Answer("réponse", cited, False, "fake", "m1", False)


def doc(
    db: Session,
    title: str,
    body: str,
    *,
    level: str = "public",
    status: Status = Status.VALIDATED,
    **kw: Any,
) -> str:
    source = db.query(Source).first() or Source(
        title="Source test", kind=SourceKind.OTHER, license="test"
    )
    db.add(source)
    db.flush()
    data = KnowledgeDocumentIn.model_validate(
        {
            "title": title,
            "body": body,
            "theme": "plants",
            "access_level": level,
            "license": "CC-BY-4.0",
            "allow_publication": True,
            "allow_training": False,
        }
        | kw
    )
    document = create_document(db, data, source, None, status)
    db.commit()
    return str(document.id)


@pytest.fixture
def app(db: Session) -> Iterator[FastAPI]:
    application = create_app()
    limiter = SlidingWindowLimiter(100)
    application.dependency_overrides[get_limiter] = lambda: limiter
    yield application
    application.dependency_overrides.clear()


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def titles(client: TestClient, q: str = "", headers: dict[str, str] | None = None) -> set[str]:
    r = client.get("/api/v1/knowledge", params={"q": q}, headers=headers or {})
    assert r.status_code == 200
    return {d["title"] for d in r.json()}


def test_visibility_by_access_level(app: FastAPI, db: Session) -> None:
    doc(db, "Public", "Document de test sur zzalpha.")
    community = doc(db, "Communauté", "Document de test sur zzalpha.", level="community")
    doc(db, "Restreint", "Document de test sur zzalpha.", level="restricted")
    doc(db, "Non publiable", "Document de test sur zzalpha.", allow_publication=False)
    _, token = make_user(db, Role.CONTRIBUTOR, "membre")
    client = TestClient(app)

    assert titles(client, "zzalpha") == {"Public"}
    assert titles(client) == {"Public"}
    assert titles(client, "zzalpha", auth(token)) == {"Public", "Communauté"}
    assert client.get(f"/api/v1/knowledge/{community}").status_code == 404
    assert client.get(f"/api/v1/knowledge/{community}", headers=auth(token)).status_code == 200
    assert client.get("/api/v1/knowledge", headers=auth("faux")).status_code == 401


def test_only_validated_documents_are_visible(app: FastAPI, db: Session) -> None:
    source = Source(title="S", kind=SourceKind.OTHER, license="x")
    db.add(source)
    db.commit()
    for status in (Status.RAW, Status.PENDING, Status.RESTRICTED, Status.WITHDRAWN):
        data = KnowledgeDocumentIn.model_validate(
            {
                "title": status.value,
                "body": "Document de test sur zzbeta.",
                "theme": "plants",
                "access_level": "public",
                "license": "x",
                "allow_publication": True,
                "allow_training": False,
            }
        )
        create_document(db, data, source, None, status)
    db.commit()
    assert titles(TestClient(app), "zzbeta") == set()


def test_ask_sends_only_public_passages(app: FastAPI, db: Session) -> None:
    doc(db, "Public", "Document de test sur zzalpha et ses usages.")
    doc(db, "Communauté", "Document de test sur zzalpha, réservé.", level="community")
    _, token = make_user(db, Role.CONTRIBUTOR, "membre2")
    fake = FakeAnswers()
    app.dependency_overrides[get_answer_provider] = lambda: fake
    r = TestClient(app).post(
        "/api/v1/knowledge/ask", json={"question": "Usages de zzalpha ?"}, headers=auth(token)
    )
    assert r.status_code == 200
    assert fake.passages is not None
    assert [p.title for p in fake.passages] == ["Public"]  # même pour un membre connecté
    body = r.json()
    assert body["answer"] == "réponse" and not body["insufficient_documentation"]
    assert [ref["title"] for ref in body["references"]] == ["Public"]
    assert body["verified"] is False


def test_ask_without_documentation_does_not_call_model(app: FastAPI, db: Session) -> None:
    fake = FakeAnswers()
    app.dependency_overrides[get_answer_provider] = lambda: fake
    r = TestClient(app).post("/api/v1/knowledge/ask", json={"question": "zzinconnu ?"})
    assert r.json() == {
        "answer": None,
        "insufficient_documentation": True,
        "references": [],
        "provider": None,
        "model": None,
        "status": "experimental",
        "verified": False,
    }
    assert fake.passages is None


def test_uncited_answer_is_flagged(app: FastAPI, db: Session) -> None:
    doc(db, "Public", "Document de test sur zzalpha.")
    app.dependency_overrides[get_answer_provider] = lambda: FakeAnswers(cite=[])
    r = TestClient(app).post("/api/v1/knowledge/ask", json={"question": "zzalpha ?"})
    assert r.json()["insufficient_documentation"] is True


def test_ask_not_configured(app: FastAPI, db: Session) -> None:
    r = TestClient(app).post("/api/v1/knowledge/ask", json={"question": "zzalpha ?"})
    assert r.status_code == 503


def test_review_through_api_and_original_protected(app: FastAPI, db: Session) -> None:
    pending = doc(db, "En attente", "Document de test sur zzgamma.", status=Status.PENDING)
    _, token = make_user(db, Role.REVIEWER, "relecteur")
    client = TestClient(app)
    assert titles(client, "zzgamma") == set()
    r = client.post(f"/api/v1/knowledge/{pending}/validate", json={}, headers=auth(token))
    assert r.status_code == 200
    assert titles(client, "zzgamma") == {"En attente"}
    history = client.get(f"/api/v1/knowledge/{pending}/history", headers=auth(token)).json()
    assert [h["action"] for h in history] == ["create", "validate"]
    with pytest.raises(DBAPIError, match="forme d'origine"):
        db.execute(text("UPDATE knowledge_documents SET body = 'x'"))
    db.rollback()
