import json
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.main import create_app
from app.models import AudioRecording, CorpusText, Revision, Role, Source, SourceKind, Status
from app.routers.voice import get_storage
from app.schemas import CorpusTextIn
from app.services import corpus
from tests.conftest import make_user

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg requis")

RIGHTS = {
    "license": "CC-BY-4.0",
    "allow_publication": True,
    "allow_training": True,
    "allow_voice_synthesis": False,
}


def ffmpeg(out: Path, *args: str) -> Path:
    subprocess.run(  # noqa: S603
        [shutil.which("ffmpeg") or "ffmpeg", "-loglevel", "error", "-y", *args, str(out)],
        check=True,
    )
    return out


@pytest.fixture(scope="module")
def media(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    d = tmp_path_factory.mktemp("media")
    tone = ["-f", "lavfi", "-i"]
    garbage = d / "garbage.webm"
    garbage.write_bytes(b"\x00not audio" * 100)
    return {
        "webm": ffmpeg(d / "ok.webm", *tone, "sine=frequency=440:duration=2", "-c:a", "libopus"),
        "wav": ffmpeg(d / "ok.wav", *tone, "sine=duration=1", "-ar", "8000"),
        "long": ffmpeg(d / "long.wav", *tone, "sine=duration=61", "-ar", "8000"),
        "short": ffmpeg(d / "short.wav", *tone, "sine=duration=0.2", "-ar", "8000"),
        "video": ffmpeg(d / "video.webm", *tone, "testsrc=duration=1:size=32x32"),
        "garbage": garbage,
    }


@pytest.fixture
def storage_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUDIO_STORAGE_DIR", str(tmp_path / "audio"))
    get_settings.cache_clear()  # la configuration a pu être lue avant ce réglage
    get_storage.cache_clear()
    return tmp_path / "audio"


@pytest.fixture
def client(db: Session, storage_dir: Path) -> Iterator[TestClient]:
    with TestClient(create_app()) as c:
        yield c


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def upload(client: TestClient, token: str, path: Path, **meta: Any) -> Any:
    with path.open("rb") as f:
        return client.post(
            "/api/v1/voice/recordings",
            files={"audio": (path.name, f, "audio/webm")},
            data={"metadata": json.dumps(RIGHTS | meta)},
            headers=auth(token),
        )


def stored(storage_dir: Path) -> list[Path]:
    return [p for p in storage_dir.rglob("*") if p.is_file()] if storage_dir.exists() else []


def test_me(client: TestClient, db: Session) -> None:
    _, token = make_user(db, Role.REVIEWER, "relectrice")
    assert client.get("/api/v1/me", headers=auth(token)).json() == {
        "pseudonym": "relectrice",
        "role": "reviewer",
    }
    assert client.get("/api/v1/me").status_code == 401


def test_upload_valid_recording(
    client: TestClient, db: Session, media: dict[str, Path], storage_dir: Path
) -> None:
    assert upload(client, "aucun", media["webm"]).status_code == 401
    _, token = make_user(db, Role.CONTRIBUTOR, "voix")
    r = upload(client, token, media["webm"])
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "pending"
    rec = db.scalar(select(AudioRecording))
    assert rec is not None
    assert rec.mime_type == "audio/webm"
    assert 1.9 < rec.duration_seconds < 2.2
    assert rec.allow_voice_synthesis is False
    assert len(stored(storage_dir)) == 1
    assert upload(client, token, media["wav"]).status_code == 201


@pytest.mark.parametrize("name", ["garbage", "video", "long", "short"])
def test_invalid_audio_is_rejected_and_not_stored(
    client: TestClient, db: Session, media: dict[str, Path], storage_dir: Path, name: str
) -> None:
    _, token = make_user(db, Role.CONTRIBUTOR, f"v-{name}")
    r = upload(client, token, media[name])
    assert r.status_code == 422, r.text
    assert stored(storage_dir) == []
    assert db.scalar(select(AudioRecording)) is None


def test_too_large(client: TestClient, db: Session, tmp_path: Path, storage_dir: Path) -> None:
    _, token = make_user(db, Role.CONTRIBUTOR, "gros")
    big = tmp_path / "big.wav"
    big.write_bytes(b"0" * (10 * 1024 * 1024 + 1))
    assert upload(client, token, big).status_code == 413
    assert stored(storage_dir) == []


@pytest.mark.parametrize(
    "meta",
    [
        {"allow_voice_synthesis": None},  # consentement explicite exigé
        {"license": ""},
        {"transcription": "zz ⴰ"},  # écritures mélangées
        {"prompt_text_id": "00000000-0000-0000-0000-000000000000"},
    ],
)
def test_invalid_metadata(
    client: TestClient, db: Session, media: dict[str, Path], meta: dict[str, Any]
) -> None:
    _, token = make_user(db, Role.CONTRIBUTOR, "meta")
    data = RIGHTS | meta
    if meta.get("allow_voice_synthesis", False) is None:
        del data["allow_voice_synthesis"]
    with media["wav"].open("rb") as f:
        r = client.post(
            "/api/v1/voice/recordings",
            files={"audio": ("a.wav", f, "audio/wav")},
            data={"metadata": json.dumps(data)},
            headers=auth(token),
        )
    assert r.status_code == 422


def test_listening_rights(client: TestClient, db: Session, media: dict[str, Path]) -> None:
    _, owner = make_user(db, Role.CONTRIBUTOR, "proprio")
    _, other = make_user(db, Role.CONTRIBUTOR, "autre")
    _, reviewer = make_user(db, Role.REVIEWER, "rev")
    rec_id = upload(client, owner, media["wav"]).json()["id"]
    url = f"/api/v1/voice/recordings/{rec_id}/audio"
    assert client.get(url).status_code == 404
    assert client.get(url, headers=auth(other)).status_code == 404
    assert client.get(url, headers=auth(owner)).status_code == 200
    ok = client.get(url, headers=auth(reviewer))
    assert ok.status_code == 200 and ok.headers["content-type"] == "audio/wav"
    assert ok.content == media["wav"].read_bytes()
    client.post(f"/api/v1/voice/recordings/{rec_id}/validate", json={}, headers=auth(reviewer))
    assert client.get(url).status_code == 200  # validé et publiable : public

    private = upload(client, owner, media["wav"], allow_publication=False).json()["id"]
    client.post(f"/api/v1/voice/recordings/{private}/validate", json={}, headers=auth(reviewer))
    assert client.get(f"/api/v1/voice/recordings/{private}/audio").status_code == 404


def test_transcription_and_review(client: TestClient, db: Session, media: dict[str, Path]) -> None:
    _, owner = make_user(db, Role.CONTRIBUTOR, "p2")
    _, other = make_user(db, Role.CONTRIBUTOR, "o2")
    _, reviewer = make_user(db, Role.REVIEWER, "r2")
    rec_id = upload(client, owner, media["wav"]).json()["id"]
    url = f"/api/v1/voice/recordings/{rec_id}/transcription"
    assert client.put(url, json={"transcription": "zz"}, headers=auth(other)).status_code == 403
    assert client.put(url, json={"transcription": "zzmot"}, headers=auth(owner)).status_code == 200
    queue = client.get("/api/v1/voice/review", headers=auth(reviewer)).json()
    assert [q["transcription"] for q in queue] == ["zzmot"]
    client.post(f"/api/v1/voice/recordings/{rec_id}/validate", json={}, headers=auth(reviewer))
    r = client.put(
        url, json={"transcription": "zzcorrige", "reason": "faute"}, headers=auth(reviewer)
    )
    assert r.json()["status"] == "pending"  # une transcription modifiée est relue à nouveau
    history = client.get(f"/api/v1/voice/recordings/{rec_id}/history", headers=auth(reviewer))
    assert [h["action"] for h in history.json()] == [
        "create",
        "transcribe",
        "validate",
        "transcribe",
    ]


def test_withdrawal_deletes_audio_file(
    client: TestClient, db: Session, media: dict[str, Path], storage_dir: Path
) -> None:
    _, owner = make_user(db, Role.CONTRIBUTOR, "retrait")
    rec_id = upload(client, owner, media["wav"]).json()["id"]
    assert len(stored(storage_dir)) == 1
    r = client.post(
        f"/api/v1/voice/recordings/{rec_id}/withdraw",
        json={"reason": "je retire ma voix"},
        headers=auth(owner),
    )
    assert r.status_code == 200 and r.json()["status"] == "withdrawn"
    assert stored(storage_dir) == []
    db.expire_all()
    rec = db.scalar(select(AudioRecording))
    assert rec is not None and rec.storage_key is None and rec.file_deleted_at is not None
    assert len(rec.sha256) == 64  # empreinte conservée pour la trace
    actions = db.scalars(select(Revision.action).order_by(Revision.id)).all()
    assert actions[-2:] == ["withdraw", "delete_file"]
    assert (
        client.get(f"/api/v1/voice/recordings/{rec_id}/audio", headers=auth(owner)).status_code
        == 404
    )


def test_prompts_and_prompted_recording(
    client: TestClient, db: Session, media: dict[str, Path]
) -> None:
    source = Source(title="S", kind=SourceKind.OTHER, license="x")
    db.add(source)
    db.flush()

    def text(value: str, status: Status, publish: bool = True) -> CorpusText:
        data = CorpusTextIn.model_validate(
            {"text": value, "license": "x", "allow_publication": publish, "allow_training": False}
        )
        return corpus.create_text(db, data, source, None, status)

    ok = text("zz phrase validée", Status.VALIDATED)
    text("zz en attente", Status.PENDING)
    text("zz privée", Status.VALIDATED, publish=False)
    db.commit()
    prompts = client.get("/api/v1/voice/prompts", params={"limit": 10}).json()
    assert [p["text"] for p in prompts] == ["zz phrase validée"]

    _, token = make_user(db, Role.CONTRIBUTOR, "lecteur")
    r = upload(client, token, media["wav"], prompt_text_id=str(ok.id))
    assert r.status_code == 201
    queue_user, reviewer = make_user(db, Role.REVIEWER, "r3")
    del queue_user
    [item] = client.get("/api/v1/voice/review", headers=auth(reviewer)).json()
    assert item["prompt"] == "zz phrase validée"
