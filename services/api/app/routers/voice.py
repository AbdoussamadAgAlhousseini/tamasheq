"""Collecte vocale consentie : phrases à lire, dépôt d'enregistrements, transcription manuelle,
écoute, relecture et retrait (avec suppression du fichier)."""

import hashlib
import tempfile
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audio import MAX_BYTES, InvalidAudio, probe
from app.auth import optional_user
from app.config import get_settings
from app.governance import record, snapshot
from app.models import AudioRecording, CorpusText, Role, Script, Status, User
from app.routers.dictionary import personal_source
from app.routers.lifecycle import DB, Contributor, Created, Reviewer, add_lifecycle_routes
from app.schemas import Rights, checked
from app.storage import LocalStorage, Storage

router = APIRouter(prefix="/api/v1/voice", tags=["voix"])


@lru_cache
def get_storage() -> Storage:
    return LocalStorage(get_settings().audio_storage_dir)


StorageDep = Annotated[Storage, Depends(get_storage)]


class Prompt(BaseModel):
    id: uuid.UUID
    text: str
    script: Script


@router.get("/prompts")
def prompts(session: DB, limit: Annotated[int, Query(ge=1, le=20)] = 5) -> list[Prompt]:
    """Phrases à lire : textes du corpus validés et publiables, tirés au hasard."""
    texts = session.scalars(
        select(CorpusText)
        .where(CorpusText.status == Status.VALIDATED, CorpusText.allow_publication.is_(True))
        .order_by(func.random())
        .limit(limit)
    )
    return [Prompt(id=t.id, text=t.original_text, script=t.script) for t in texts]


class RecordingRights(Rights):
    allow_voice_synthesis: bool
    prompt_text_id: uuid.UUID | None = None
    transcription: str | None = Field(default=None, max_length=2000)


@router.post("/recordings", status_code=status.HTTP_201_CREATED)
async def upload(
    user: Contributor,
    session: DB,
    storage: StorageDep,
    audio: Annotated[UploadFile, File(description="Fichier audio, 60 s au plus")],
    metadata: Annotated[str, Form(description="Droits et consentements (JSON)")],
) -> Created:
    try:
        rights = RecordingRights.model_validate_json(metadata)
    except ValidationError as e:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            e.errors(include_url=False, include_context=False),
        ) from e
    transcription = None
    if rights.transcription:
        try:
            transcription, _ = checked(rights.transcription, None, "transcription")
        except ValueError as e:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e
    if rights.prompt_text_id is not None:
        prompt = session.get(CorpusText, rights.prompt_text_id)
        if prompt is None or prompt.status != Status.VALIDATED:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Phrase inconnue.")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "upload"
        digest = hashlib.sha256()
        size = 0
        with path.open("wb") as out:
            while chunk := await audio.read(256 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(
                        status.HTTP_413_CONTENT_TOO_LARGE,
                        "Fichier trop volumineux (10 Mo maximum).",
                    )
                digest.update(chunk)
                out.write(chunk)
        try:
            info = probe(path)
        except InvalidAudio as e:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e

        recording_id = uuid.uuid4()
        key = f"recordings/{recording_id}"
        storage.put(key, path)

    recording = AudioRecording(
        id=recording_id,
        storage_key=key,
        mime_type=info.mime_type,
        size_bytes=size,
        duration_seconds=info.duration,
        sha256=digest.hexdigest(),
        prompt_text_id=rights.prompt_text_id,
        transcription=transcription,
        allow_voice_synthesis=rights.allow_voice_synthesis,
        source_id=personal_source(session, user).id,
        contributor_id=user.id,
        status=Status.PENDING,
        **rights.model_dump(include=set(Rights.model_fields)),
    )
    session.add(recording)
    try:
        record(session, recording, "create", user, None)
        session.commit()
    except Exception:
        storage.delete(key)  # pas de fichier orphelin si l'enregistrement en base échoue
        raise
    return Created(id=recording.id, status=recording.status)


def _can_listen(recording: AudioRecording, user: User | None) -> bool:
    if recording.status == Status.VALIDATED and recording.allow_publication:
        return True
    if user is None:
        return False
    return user.role in (Role.REVIEWER, Role.ADMIN) or recording.contributor_id == user.id


@router.get("/recordings/{recording_id}/audio")
def listen(
    recording_id: uuid.UUID,
    session: DB,
    storage: StorageDep,
    user: Annotated[User | None, Depends(optional_user)],
) -> FileResponse:
    recording = session.get(AudioRecording, recording_id)
    if (
        recording is None
        or recording.storage_key is None
        or recording.status == Status.WITHDRAWN
        or not _can_listen(recording, user)
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enregistrement introuvable.")
    return FileResponse(storage.path(recording.storage_key), media_type=recording.mime_type)


class TranscriptionIn(BaseModel):
    transcription: str = Field(min_length=1, max_length=2000)
    reason: str | None = Field(default=None, max_length=2000)


@router.put("/recordings/{recording_id}/transcription")
def correct_transcription(
    recording_id: uuid.UUID, body: TranscriptionIn, user: Contributor, session: DB
) -> Created:
    """Transcription de référence, saisie ou corrigée par la personne ou par un réviseur."""
    recording = session.get(AudioRecording, recording_id)
    if recording is None or recording.status == Status.WITHDRAWN:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enregistrement introuvable.")
    if user.role == Role.CONTRIBUTOR and recording.contributor_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Rôle insuffisant.")
    try:
        text, _ = checked(body.transcription, None, "transcription")
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e
    before = snapshot(recording)
    recording.transcription = text
    if recording.status == Status.VALIDATED:
        # Une transcription modifiée doit être relue à nouveau.
        recording.status = Status.PENDING
    record(session, recording, "transcribe", user, before, body.reason)
    session.commit()
    return Created(id=recording.id, status=recording.status)


class ReviewItem(BaseModel):
    id: uuid.UUID
    status: Status
    duration_seconds: float
    prompt: str | None
    transcription: str | None
    contributor_id: uuid.UUID | None
    created_at: datetime


@router.get("/review")
def review_queue(
    _: Reviewer,
    session: DB,
    status_: Annotated[Status, Query(alias="status")] = Status.PENDING,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ReviewItem]:
    recordings = session.scalars(
        select(AudioRecording)
        .where(AudioRecording.status == status_)
        .order_by(AudioRecording.created_at)
        .limit(limit)
    )
    return [
        ReviewItem(
            id=r.id,
            status=r.status,
            duration_seconds=r.duration_seconds,
            prompt=r.prompt.original_text if r.prompt else None,
            transcription=r.transcription,
            contributor_id=r.contributor_id,
            created_at=r.created_at,
        )
        for r in recordings
    ]


def delete_audio_file(session: Session, recording: AudioRecording) -> None:
    """Au retrait, le fichier audio est effacé ; l'empreinte SHA-256 reste pour la trace."""
    if recording.storage_key is None:
        return
    before = snapshot(recording)
    get_storage().delete(recording.storage_key)
    recording.storage_key = None
    recording.file_deleted_at = datetime.now(UTC)
    record(session, recording, "delete_file", None, before, "suppression du fichier au retrait")


add_lifecycle_routes(router, "/recordings", AudioRecording, on_withdraw=delete_audio_file)
