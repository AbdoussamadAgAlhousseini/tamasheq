import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.cli import main
from app.governance import validate
from app.models import (
    CorpusText,
    Dataset,
    DatasetItem,
    LexicalEntry,
    Role,
    Source,
    SourceKind,
    Status,
)
from tests.conftest import make_user

# Données factices : chaînes de test, pas du tamasheq.


def line(headword: str, **kw: Any) -> str:
    return json.dumps(
        {
            "headword": headword,
            "senses": [{"translation_fr": "test"}],
            "license": "CC-BY-4.0",
            "allow_publication": True,
            "allow_training": True,
        }
        | kw
    )


def source(db: Session, training: bool | None) -> Source:
    s = Source(
        title=f"source-{training}",
        kind=SourceKind.DICTIONARY,
        license="test",
        license_allows_training=training,
    )
    db.add(s)
    db.commit()
    return s


def test_import_is_all_or_nothing(db: Session, tmp_path: Path) -> None:
    s = source(db, True)
    bad = tmp_path / "bad.jsonl"
    bad.write_text(line("zzun") + "\n" + line("zzⴰ") + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="ligne 2"):
        main(["import", "lexicon", str(bad), "--source", str(s.id)])
    assert db.scalar(select(func.count()).select_from(LexicalEntry)) == 0

    good = tmp_path / "good.jsonl"
    good.write_text(line("zzun") + "\n\n" + line("zzdeux") + "\n", encoding="utf-8")
    main(["import", "lexicon", str(good), "--source", str(s.id)])
    statuses = db.scalars(select(LexicalEntry.status)).all()
    assert statuses == [Status.RAW, Status.RAW]  # jamais validé à l'import


def _import_and_validate(db: Session, tmp_path: Path, src: Source, *lines: str) -> None:
    f = tmp_path / f"{src.id}.jsonl"
    f.write_text("\n".join(lines), encoding="utf-8")
    main(["import", "lexicon", str(f), "--source", str(src.id)])
    reviewer, _ = make_user(db, Role.REVIEWER, f"rev-{src.id}")
    db.expire_all()
    for entry in db.scalars(select(LexicalEntry).where(LexicalEntry.source_id == src.id)):
        validate(db, entry, reviewer, None)
    db.commit()


def test_export_rules(db: Session, tmp_path: Path) -> None:
    licensed = source(db, True)
    unknown = source(db, None)
    _import_and_validate(
        db,
        tmp_path,
        licensed,
        line("zzok"),
        line("zznotrain", allow_training=False),
        line("zzrestreint", distribution_restrictions="usage communautaire seulement"),
    )
    _import_and_validate(db, tmp_path, unknown, line("zzlicenceinconnue"))

    out = tmp_path / "exports"
    main(["export", "lexicon", "--purpose", "training", "--name", "t1", "--out", str(out)])
    main(["export", "lexicon", "--purpose", "publication", "--name", "p1", "--out", str(out)])

    def headwords(name: str) -> list[str]:
        content = (out / f"{name}.jsonl").read_text(encoding="utf-8")
        manifest = json.loads((out / f"{name}.manifest.json").read_text(encoding="utf-8"))
        assert manifest["sha256"] == hashlib.sha256(content.encode()).hexdigest()
        rows = [json.loads(x) for x in content.splitlines()]
        assert manifest["item_count"] == len(rows)
        assert all(r["source"]["license"] and r["license"] for r in rows)
        return sorted(r["headword"] for r in rows)

    assert headwords("t1") == ["zzok"]
    assert headwords("p1") == ["zzlicenceinconnue", "zznotrain", "zzok"]
    assert db.scalar(select(func.count()).select_from(DatasetItem)) == 4
    assert {d.name for d in db.scalars(select(Dataset))} == {"t1", "p1"}


def test_withdraw_contributor(
    db: Session, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from app.schemas import CorpusTextIn, LexicalEntryIn
    from app.services import corpus, lexicon

    person, _ = make_user(db, Role.CONTRIBUTOR, "personne")
    make_user(db, Role.ADMIN, "admin")
    src = source(db, True)
    lexicon.create_entry(
        db, LexicalEntryIn.model_validate_json(line("zza")), src, person, Status.PENDING
    )
    corpus.create_text(
        db,
        CorpusTextIn.model_validate(
            {"text": "zz texte", "license": "x", "allow_publication": True, "allow_training": True}
        ),
        src,
        person,
        Status.PENDING,
    )
    db.commit()
    main(
        [
            "withdraw-contributor",
            "--email",
            "personne@test.invalid",
            "--reason",
            "demande de retrait",
            "--actor",
            "admin@test.invalid",
        ]
    )
    assert "2 contenu(s) retiré(s)" in capsys.readouterr().out
    db.expire_all()
    assert db.scalar(select(LexicalEntry.status)) == Status.WITHDRAWN
    assert db.scalar(select(CorpusText.status)) == Status.WITHDRAWN
