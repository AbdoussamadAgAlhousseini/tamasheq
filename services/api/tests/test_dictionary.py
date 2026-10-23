from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.main import create_app
from app.models import DatasetPurpose, LexicalEntry, Revision, Role, Source, SourceKind
from app.services import datasets
from tests.conftest import make_user

# Données factices : chaînes de test, pas du tamasheq.


def payload(headword: str = "zzmot", **kw: Any) -> dict[str, Any]:
    return {
        "headword": headword,
        "senses": [{"translation_fr": "maison-test", "translation_en": "house-test"}],
        "spellings": [{"form": "ⴰⴱⴲ"}],
        "license": "CC-BY-4.0",
        "allow_publication": True,
        "allow_training": True,
    } | kw


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    with TestClient(create_app()) as c:
        yield c


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def contribute(client: TestClient, token: str, **kw: Any) -> str:
    response = client.post("/api/v1/dictionary", json=payload(**kw), headers=auth(token))
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "pending"
    return str(response.json()["id"])


def search(client: TestClient, q: str = "", **params: Any) -> list[dict[str, Any]]:
    response = client.get("/api/v1/dictionary", params={"q": q, **params})
    assert response.status_code == 200
    return list(response.json()["items"])


def test_authentication_required(client: TestClient, db: Session) -> None:
    assert client.post("/api/v1/dictionary", json=payload()).status_code == 401
    assert (
        client.post("/api/v1/dictionary", json=payload(), headers=auth("faux")).status_code == 401
    )


def test_contribution_lifecycle(client: TestClient, db: Session) -> None:
    contributor, c_token = make_user(db, Role.CONTRIBUTOR, "contrib")
    _, r_token = make_user(db, Role.REVIEWER, "relecteur")

    entry_id = contribute(client, c_token)
    assert search(client) == []  # en attente : invisible par défaut
    pending = search(client, include_pending=True)
    assert [e["status"] for e in pending] == ["pending"]

    # un contributeur ne valide pas
    assert (
        client.post(
            f"/api/v1/dictionary/{entry_id}/validate", json={}, headers=auth(c_token)
        ).status_code
        == 403
    )

    r = client.post(
        f"/api/v1/dictionary/{entry_id}/validate", json={"reason": "vérifié"}, headers=auth(r_token)
    )
    assert r.status_code == 200 and r.json()["status"] == "validated"
    [shown] = search(client)
    assert shown["headword"] == "zzmot"
    assert shown["spellings"] == [{"form": "ⴰⴱⴲ", "script": "Tfng"}]
    assert "contributor_id" not in shown and "consent_reference" not in shown

    # double validation refusée
    again = client.post(f"/api/v1/dictionary/{entry_id}/validate", json={}, headers=auth(r_token))
    assert again.status_code == 409

    history = client.get(f"/api/v1/dictionary/{entry_id}/history", headers=auth(r_token)).json()
    assert [h["action"] for h in history] == ["create", "validate"]
    assert history[1]["before"]["status"] == "pending"
    assert history[1]["after"]["status"] == "validated"
    assert history[1]["reason"] == "vérifié"


def test_reviewer_cannot_validate_own_contribution(client: TestClient, db: Session) -> None:
    _, token = make_user(db, Role.REVIEWER, "rev1")
    _, other = make_user(db, Role.REVIEWER, "rev2")
    entry_id = contribute(client, token)
    own = client.post(f"/api/v1/dictionary/{entry_id}/validate", json={}, headers=auth(token))
    assert own.status_code == 403
    ok = client.post(f"/api/v1/dictionary/{entry_id}/validate", json={}, headers=auth(other))
    assert ok.status_code == 200


def validated(client: TestClient, db: Session, **kw: Any) -> str:
    _, c = make_user(db, Role.CONTRIBUTOR, f"c{len(kw)}{kw.get('headword', '')}")
    _, r = make_user(db, Role.REVIEWER, f"r{len(kw)}{kw.get('headword', '')}")
    entry_id = contribute(client, c, **kw)
    assert (
        client.post(f"/api/v1/dictionary/{entry_id}/validate", json={}, headers=auth(r)).status_code
        == 200
    )
    return entry_id


def test_publication_requires_consent(client: TestClient, db: Session) -> None:
    validated(client, db, headword="zzprive", allow_publication=False)
    assert search(client) == []


def test_search(client: TestClient, db: Session) -> None:
    validated(client, db, headword="zzalpha")
    validated(client, db, headword="zzbeta")
    assert [e["headword"] for e in search(client, "ZZALPHA")] == ["zzalpha"]
    assert len(search(client, "maison-test")) == 2  # traduction française
    assert len(search(client, "ⴰⴱ")) == 2  # graphie tifinagh
    assert search(client, "%") == []  # caractères spéciaux de LIKE neutralisés
    assert search(client, "_") == []


def test_restrict_hides_entry(client: TestClient, db: Session) -> None:
    entry_id = validated(client, db)
    _, r = make_user(db, Role.REVIEWER, "rev-restrict")
    missing = client.post(f"/api/v1/dictionary/{entry_id}/restrict", json={}, headers=auth(r))
    assert missing.status_code == 422  # motif obligatoire
    ok = client.post(
        f"/api/v1/dictionary/{entry_id}/restrict",
        json={"reason": "savoir réservé"},
        headers=auth(r),
    )
    assert ok.json()["status"] == "restricted"
    assert search(client) == []
    assert client.get(f"/api/v1/dictionary/{entry_id}").status_code == 404


def test_withdrawal_is_traced_to_exports(client: TestClient, db: Session) -> None:
    contributor, token = make_user(db, Role.CONTRIBUTOR, "auteur")
    _, other = make_user(db, Role.CONTRIBUTOR, "autre")
    _, reviewer = make_user(db, Role.REVIEWER, "rev-w")
    entry_id = contribute(client, token)
    client.post(f"/api/v1/dictionary/{entry_id}/validate", json={}, headers=auth(reviewer))

    datasets.export(db, "lexicon", DatasetPurpose.TRAINING, "entrainement-v1", None)
    db.commit()

    refused = client.post(
        f"/api/v1/dictionary/{entry_id}/withdraw", json={"reason": "x"}, headers=auth(other)
    )
    assert refused.status_code == 403

    r = client.post(
        f"/api/v1/dictionary/{entry_id}/withdraw",
        json={"reason": "je retire ma contribution"},
        headers=auth(token),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "withdrawn"
    assert [d["name"] for d in r.json()["datasets"]] == ["entrainement-v1"]
    assert search(client) == []
    # un nouvel export ne le contient plus
    _, content = datasets.export(db, "lexicon", DatasetPurpose.TRAINING, "entrainement-v2", None)
    assert content == ""


def test_database_protects_originals_and_history(client: TestClient, db: Session) -> None:
    _, token = make_user(db, Role.CONTRIBUTOR, "c-orig")
    contribute(client, token)
    with pytest.raises(DBAPIError, match="forme d'origine"):
        db.execute(text("UPDATE lexical_entries SET headword = 'modifie'"))
    db.rollback()
    with pytest.raises(DBAPIError, match="journal des révisions"):
        db.execute(text("DELETE FROM revisions"))
    db.rollback()
    with pytest.raises(DBAPIError, match="journal des révisions"):
        db.execute(text("UPDATE revisions SET reason = 'x'"))
    db.rollback()
    assert db.scalar(select(LexicalEntry.headword)) == "zzmot"
    assert db.scalars(select(Revision.action)).all() == ["create"]


def test_revoked_token(client: TestClient, db: Session) -> None:
    from app.cli import main

    _, token = make_user(db, Role.CONTRIBUTOR, "revoque")
    main(["revoke-tokens", "--email", "revoque@test.invalid"])
    assert client.post("/api/v1/dictionary", json=payload(), headers=auth(token)).status_code == 401


def test_capability_is_experimental(client: TestClient) -> None:
    caps = {c["name"]: c["status"] for c in client.get("/api/v1/capabilities").json()}
    assert caps["dictionary"] == "experimental"


def test_unknown_source_rejected(client: TestClient, db: Session) -> None:
    _, token = make_user(db, Role.CONTRIBUTOR, "c-src")
    r = client.post(
        "/api/v1/dictionary",
        json=payload(source_id="00000000-0000-0000-0000-000000000000"),
        headers=auth(token),
    )
    assert r.status_code == 422


def test_documented_source_is_kept(client: TestClient, db: Session) -> None:
    source = Source(title="Ouvrage test", kind=SourceKind.PUBLICATION, license="CC-BY-4.0")
    db.add(source)
    db.commit()
    _, token = make_user(db, Role.CONTRIBUTOR, "c-doc")
    _, r = make_user(db, Role.REVIEWER, "r-doc")
    entry_id = contribute(client, token, source_id=str(source.id))
    client.post(f"/api/v1/dictionary/{entry_id}/validate", json={}, headers=auth(r))
    assert client.get(f"/api/v1/dictionary/{entry_id}").json()["source"]["title"] == "Ouvrage test"
