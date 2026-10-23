import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    LexicalEntry,
    LexicalSense,
    Script,
    Source,
    SourceKind,
    Status,
    User,
)
from app.routers.lifecycle import DB, Contributor, Created, Reviewer, add_lifecycle_routes
from app.schemas import LexicalEntryIn
from app.services import lexicon

router = APIRouter(prefix="/api/v1", tags=["dictionnaire"])


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


add_lifecycle_routes(router, "/dictionary", LexicalEntry)
