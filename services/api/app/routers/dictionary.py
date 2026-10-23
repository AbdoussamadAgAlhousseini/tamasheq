import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import require
from app.db import get_session
from app.governance import GovernanceError, NotAllowed, restrict, validate, withdraw
from app.models import (
    LexicalEntry,
    LexicalSense,
    Revision,
    Role,
    Script,
    Source,
    SourceKind,
    Status,
    User,
)
from app.schemas import LexicalEntryIn
from app.services import lexicon

router = APIRouter(prefix="/api/v1", tags=["dictionnaire"])

Contributor = Annotated[User, Depends(require(Role.CONTRIBUTOR, Role.REVIEWER, Role.ADMIN))]
Reviewer = Annotated[User, Depends(require(Role.REVIEWER, Role.ADMIN))]
DB = Annotated[Session, Depends(get_session)]


class SpellingOut(BaseModel):
    form: str
    script: Script


class ExampleOut(BaseModel):
    text: str
    script: Script
    translation_fr: str | None
    translation_en: str | None


class SenseOut(BaseModel):
    definition_fr: str | None
    definition_en: str | None
    translation_fr: str | None
    translation_en: str | None
    examples: list[ExampleOut]


class SourceOut(BaseModel):
    title: str
    citation: str | None
    url: str | None


class EntryOut(BaseModel):
    """Vue publique : aucune donnée sur le contributeur ni sur le consentement."""

    id: uuid.UUID
    headword: str
    script: Script
    language: str
    variant: str | None
    part_of_speech: str | None
    status: Status
    spellings: list[SpellingOut]
    senses: list[SenseOut]
    source: SourceOut
    license: str
    validated_at: datetime | None

    @classmethod
    def of(cls, e: LexicalEntry) -> "EntryOut":
        return cls(
            id=e.id,
            headword=e.headword,
            script=e.headword_script,
            language=e.language,
            variant=e.variant,
            part_of_speech=e.part_of_speech,
            status=e.status,
            spellings=[SpellingOut(form=s.form, script=s.script) for s in e.spellings],
            senses=[
                SenseOut(
                    definition_fr=s.definition_fr,
                    definition_en=s.definition_en,
                    translation_fr=s.translation_fr,
                    translation_en=s.translation_en,
                    examples=[
                        ExampleOut(
                            text=x.text,
                            script=x.script,
                            translation_fr=x.translation_fr,
                            translation_en=x.translation_en,
                        )
                        for x in s.examples
                    ],
                )
                for s in e.senses
            ],
            source=SourceOut(title=e.source.title, citation=e.source.citation, url=e.source.url),
            license=e.license,
            validated_at=e.validated_at,
        )


class SearchOut(BaseModel):
    items: list[EntryOut]


@router.get("/dictionary")
def search(
    session: DB,
    q: Annotated[str, Query(max_length=200)] = "",
    include_pending: bool = False,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> SearchOut:
    entries = lexicon.search(session, q, include_pending, limit)
    return SearchOut(items=[EntryOut.of(e) for e in entries])


@router.get("/dictionary/{entry_id}")
def get_entry(entry_id: uuid.UUID, session: DB, include_pending: bool = False) -> EntryOut:
    entry = session.scalar(lexicon.public_query(include_pending).where(LexicalEntry.id == entry_id))
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrée introuvable.")
    return EntryOut.of(entry)


class ContributionIn(LexicalEntryIn):
    source_id: uuid.UUID | None = Field(
        default=None, description="Source documentaire ; absente : contribution personnelle."
    )


class Created(BaseModel):
    id: uuid.UUID
    status: Status


def personal_source(session: Session, user: User) -> Source:
    """Source des contributions directes d'une personne. L'accord d'entraînement est donné
    contribution par contribution (`allow_training`), d'où `license_allows_training=True`."""
    title = f"Contributions de {user.pseudonym}"
    source = session.scalar(
        select(Source).where(Source.title == title, Source.kind == SourceKind.CONTRIBUTION)
    )
    if source is None:
        source = Source(
            title=title,
            kind=SourceKind.CONTRIBUTION,
            license="Droits précisés pour chaque contribution",
            license_allows_training=True,
        )
        session.add(source)
        session.flush()
    return source


@router.post("/dictionary", status_code=status.HTTP_201_CREATED)
def contribute(body: ContributionIn, user: Contributor, session: DB) -> Created:
    if body.source_id is None:
        source = personal_source(session, user)
    else:
        found = session.get(Source, body.source_id)
        if found is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Source inconnue.")
        source = found
    data = LexicalEntryIn.model_validate(body.model_dump(exclude={"source_id"}))
    entry = lexicon.create_entry(session, data, source, user, Status.PENDING)
    session.commit()
    return Created(id=entry.id, status=entry.status)


def _refused(e: GovernanceError) -> HTTPException:
    code = status.HTTP_403_FORBIDDEN if isinstance(e, NotAllowed) else status.HTTP_409_CONFLICT
    return HTTPException(code, str(e))


def _load(session: Session, entry_id: uuid.UUID) -> LexicalEntry:
    entry = session.get(LexicalEntry, entry_id)
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrée introuvable.")
    return entry


class Decision(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


class RequiredReason(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


@router.post("/dictionary/{entry_id}/validate")
def validate_entry(entry_id: uuid.UUID, body: Decision, user: Reviewer, session: DB) -> Created:
    entry = _load(session, entry_id)
    try:
        validate(session, entry, user, body.reason)
    except GovernanceError as e:
        raise _refused(e) from e
    session.commit()
    return Created(id=entry.id, status=entry.status)


@router.post("/dictionary/{entry_id}/restrict")
def restrict_entry(
    entry_id: uuid.UUID, body: RequiredReason, user: Reviewer, session: DB
) -> Created:
    entry = _load(session, entry_id)
    try:
        restrict(session, entry, user, body.reason)
    except GovernanceError as e:
        raise _refused(e) from e
    session.commit()
    return Created(id=entry.id, status=entry.status)


class DatasetRef(BaseModel):
    name: str
    purpose: str
    created_at: datetime


class Withdrawn(BaseModel):
    id: uuid.UUID
    status: Status
    datasets: list[DatasetRef] = Field(
        description="Exports déjà produits qui contenaient l'entrée : à régénérer ou signaler."
    )


@router.post("/dictionary/{entry_id}/withdraw")
def withdraw_entry(
    entry_id: uuid.UUID, body: RequiredReason, user: Contributor, session: DB
) -> Withdrawn:
    entry = _load(session, entry_id)
    try:
        datasets = withdraw(session, entry, user, body.reason)
    except GovernanceError as e:
        raise _refused(e) from e
    session.commit()
    return Withdrawn(
        id=entry.id,
        status=entry.status,
        datasets=[
            DatasetRef(name=d.name, purpose=d.purpose.value, created_at=d.created_at)
            for d in datasets
        ],
    )


class RevisionOut(BaseModel):
    action: str
    actor_id: uuid.UUID | None
    at: datetime
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    reason: str | None


@router.get("/dictionary/{entry_id}/history")
def history(entry_id: uuid.UUID, _: Reviewer, session: DB) -> list[RevisionOut]:
    _load(session, entry_id)
    revisions = session.scalars(
        select(Revision)
        .where(Revision.entity == "lexical_entry", Revision.entity_id == entry_id)
        .order_by(Revision.id)
    )
    return [
        RevisionOut(
            action=r.action,
            actor_id=r.actor_id,
            at=r.at,
            before=r.before,
            after=r.after,
            reason=r.reason,
        )
        for r in revisions
    ]


class ReviewItem(BaseModel):
    id: uuid.UUID
    headword: str
    status: Status
    contributor_id: uuid.UUID | None
    created_at: datetime


@router.get("/review/dictionary")
def review_queue(
    _: Reviewer,
    session: DB,
    status_: Annotated[Status, Query(alias="status")] = Status.PENDING,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ReviewItem]:
    entries = session.scalars(
        select(LexicalEntry)
        .where(LexicalEntry.status == status_)
        .order_by(LexicalEntry.created_at)
        .limit(limit)
        .options(selectinload(LexicalEntry.senses).selectinload(LexicalSense.examples))
    )
    return [
        ReviewItem(
            id=e.id,
            headword=e.headword,
            status=e.status,
            contributor_id=e.contributor_id,
            created_at=e.created_at,
        )
        for e in entries
    ]
