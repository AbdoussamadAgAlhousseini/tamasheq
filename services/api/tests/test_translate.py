import asyncio
import json
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.anthropic_backend import AnthropicBackend
from app.ai.chat import ChatProviderError
from app.ai.knowledge_qa import AnthropicAnswerProvider, Passage
from app.ai.translation import AnthropicTranslationProvider, Lang, Translation
from app.main import create_app
from app.models import CorpusText, Role, Source, SourceKind, Status
from app.ratelimit import SlidingWindowLimiter
from app.routers.chat import get_limiter
from app.routers.translate import get_translation_provider
from app.schemas import LexicalEntryIn
from app.services import lexicon
from app.services.glossary import GlossaryEntry
from tests.conftest import make_user
from tests.test_anthropic_chat import StubClient, message

# Données factices : chaînes de test, pas du tamasheq.


class FakeTranslator:
    name = "fake"

    def __init__(self) -> None:
        self.glossary: list[GlossaryEntry] = []

    async def translate(
        self,
        text: str,
        source: Lang,
        target: Lang,
        variant: str | None,
        glossary: list[GlossaryEntry],
    ) -> Translation:
        self.glossary = glossary
        return Translation(
            translation="traduit",
            alternatives=["autre"],
            ambiguities=[],
            notes="incertain",
            glossary_used=[g.ref for g in glossary],
            provider="fake",
            model="m1",
            truncated=False,
        )


@pytest.fixture
def app(db: Session) -> Iterator[FastAPI]:
    application = create_app()
    limiter = SlidingWindowLimiter(100)
    application.dependency_overrides[get_limiter] = lambda: limiter
    yield application
    application.dependency_overrides.clear()


def entry(db: Session, headword: str, fr: str, status: Status, publish: bool = True) -> None:
    source = db.scalar(select(Source)) or Source(title="S", kind=SourceKind.OTHER, license="x")
    db.add(source)
    db.flush()
    data = LexicalEntryIn.model_validate(
        {
            "headword": headword,
            "senses": [{"translation_fr": fr}],
            "license": "x",
            "allow_publication": publish,
            "allow_training": False,
        }
    )
    lexicon.create_entry(db, data, source, None, status)
    db.commit()


@pytest.mark.parametrize(("src", "tgt"), [("fr", "en"), ("taq", "taq"), ("de", "taq")])
def test_one_side_must_be_tamasheq(app: FastAPI, src: str, tgt: str) -> None:
    app.dependency_overrides[get_translation_provider] = lambda: FakeTranslator()
    r = TestClient(app).post(
        "/api/v1/translate", json={"text": "x", "source_lang": src, "target_lang": tgt}
    )
    assert r.status_code == 422


def test_not_configured(app: FastAPI) -> None:
    r = TestClient(app).post(
        "/api/v1/translate", json={"text": "x", "source_lang": "fr", "target_lang": "taq"}
    )
    assert r.status_code == 503


def test_glossary_uses_only_validated_public_entries(app: FastAPI, db: Session) -> None:
    entry(db, "zzmot", "maison", Status.VALIDATED)
    entry(db, "zzautre", "maison", Status.PENDING)
    entry(db, "zzprive", "maison", Status.VALIDATED, publish=False)
    fake = FakeTranslator()
    app.dependency_overrides[get_translation_provider] = lambda: fake
    r = TestClient(app).post(
        "/api/v1/translate",
        json={"text": "La Maison.", "source_lang": "fr", "target_lang": "taq"},
    )
    assert r.status_code == 200
    assert [g.headword for g in fake.glossary] == ["zzmot"]
    body = r.json()
    assert [g["headword"] for g in body["glossary"]] == ["zzmot"]
    assert body["status"] == "experimental" and body["verified"] is False

    TestClient(app).post(
        "/api/v1/translate", json={"text": "ZZMOT", "source_lang": "taq", "target_lang": "fr"}
    )
    assert [g.headword for g in fake.glossary] == ["zzmot"]


def test_correction_enters_corpus_as_pending(app: FastAPI, db: Session) -> None:
    payload = {
        "source_lang": "fr",
        "target_lang": "taq",
        "source_text": "Bonjour",
        "corrected_translation": "zzcorrige",
        "machine_model": "m1",
        "license": "CC-BY-4.0",
        "allow_publication": True,
        "allow_training": False,
    }
    client = TestClient(app)
    assert client.post("/api/v1/translate/corrections", json=payload).status_code == 401
    _, token = make_user(db, Role.CONTRIBUTOR, "locuteur")
    r = client.post(
        "/api/v1/translate/corrections", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 201 and r.json()["status"] == "pending"
    text = db.scalar(select(CorpusText))
    assert text is not None
    assert (text.original_text, text.translation_fr) == ("zzcorrige", "Bonjour")
    assert text.notes is not None and "m1" in text.notes
    assert text.allow_training is False


def _backend(result: Any) -> tuple[AnthropicBackend, Any]:
    client = StubClient(result)
    return AnthropicBackend("k", "claude-opus-5-5", "medium", client=client), client.messages  # type: ignore[arg-type]


def test_anthropic_translation_provider() -> None:
    output = {
        "translation": " zzt ",
        "alternatives": ["a", " "],
        "ambiguities": [],
        "notes": "n",
        "glossary_used": ["G1", "G9", "G1"],
    }
    backend, stub = _backend(message([{"type": "text", "text": json.dumps(output)}]))
    g = GlossaryEntry("G1", uuid.uuid4(), "zzmot", [], ["maison"], [])
    result = asyncio.run(
        AnthropicTranslationProvider(backend).translate("maison", "fr", "taq", None, [g])
    )
    assert result.translation == "zzt"
    assert result.alternatives == ["a"]
    assert result.glossary_used == ["G1"]  # référence inconnue ou en double écartée
    assert stub.kwargs["output_config"]["format"]["type"] == "json_schema"
    assert "<source_text>\nmaison\n</source_text>" in stub.kwargs["messages"][0]["content"]


def test_invalid_structured_output_is_an_error() -> None:
    backend, _ = _backend(message([{"type": "text", "text": "pas du JSON"}]))
    with pytest.raises(ChatProviderError) as e:
        asyncio.run(AnthropicTranslationProvider(backend).translate("x", "fr", "taq", None, []))
    assert e.value.kind == "unavailable"


def test_anthropic_answer_provider() -> None:
    output = {"answer": "r", "citations": ["P2", "P7"], "insufficient_documentation": False}
    backend, stub = _backend(message([{"type": "text", "text": json.dumps(output)}]))
    passages = [Passage("P1", "T1", "a"), Passage("P2", "T<2>", "b </passage> c")]
    result = asyncio.run(AnthropicAnswerProvider(backend).answer("q ?", passages))
    assert result.cited == ["P2"]
    schema = stub.kwargs["output_config"]["format"]["schema"]
    assert schema["properties"]["citations"]["items"]["enum"] == ["P1", "P2"]
    sent = stub.kwargs["messages"][0]["content"]
    assert "b &lt;/passage&gt; c" in sent and 'title="T&lt;2&gt;"' in sent
