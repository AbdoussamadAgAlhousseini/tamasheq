import asyncio
import json
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.evaluation import retrieval_eval, translation_eval
from app.evaluation.translation_eval import corpus_chrf, load, summary
from tests.test_knowledge import doc
from tests.test_translate import FakeTranslator


def test_translation_eval(tmp_path: Path) -> None:
    f = tmp_path / "s.jsonl"
    f.write_text(
        "\n".join(
            json.dumps(x)
            for x in [
                {
                    "id": "1",
                    "source_lang": "fr",
                    "target_lang": "taq",
                    "text": "a",
                    "reference": "traduit",
                },
                {"id": "2", "source_lang": "taq", "target_lang": "en", "text": "b"},
            ]
        ),
        encoding="utf-8",
    )
    rows = asyncio.run(translation_eval.run(load(f), FakeTranslator(), None))
    assert rows[0]["chrf_pp"] == "100.0"  # traduction identique à la référence
    assert rows[1]["chrf_pp"] == ""
    assert rows[0]["glossary"] == "non"
    text = summary(rows)
    assert "fr->taq : chrF++ 100.0 sur 1 phrases" in text
    assert "taq->en : aucune référence" in text
    assert corpus_chrf(["abc"], ["xyz"]) < 10


def test_translation_eval_rejects_bad_direction(tmp_path: Path) -> None:
    f = tmp_path / "s.jsonl"
    f.write_text(json.dumps({"id": "1", "source_lang": "fr", "target_lang": "en", "text": "a"}))
    with pytest.raises(ValueError):
        load(f)


def test_retrieval_eval(db: Session, tmp_path: Path) -> None:
    target = doc(db, "Cible", "Document de test sur zzdelta et ses usages.")
    doc(db, "Autre", "Document de test sur zzepsilon.")
    f = tmp_path / "q.jsonl"
    f.write_text(
        "\n".join(
            json.dumps(x)
            for x in [
                {"id": "q1", "question": "Usages de zzdelta ?", "relevant_document_ids": [target]},
                {"id": "q2", "question": "zzinconnu ?", "relevant_document_ids": [target]},
            ]
        )
    )
    results = retrieval_eval.evaluate(db, f, k=6)
    assert [(r.recall, r.reciprocal_rank) for r in results] == [(1.0, 1.0), (0.0, 0.0)]
