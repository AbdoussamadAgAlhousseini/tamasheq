from sqlalchemy import Select, String, case, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.governance import record
from app.models import (
    LexicalEntry,
    LexicalExample,
    LexicalSense,
    LexicalSpelling,
    Source,
    Status,
    User,
)
from app.schemas import LexicalEntryIn, resolved
from app.text import search_key


def create_entry(
    session: Session, data: LexicalEntryIn, source: Source, actor: User | None, status: Status
) -> LexicalEntry:
    entry = LexicalEntry(
        headword=data.headword,
        headword_script=resolved(data.script),
        headword_key=search_key(data.headword),
        part_of_speech=data.part_of_speech,
        notes=data.notes,
        source_id=source.id,
        contributor_id=actor.id if actor and status != Status.RAW else None,
        status=status,
        **data.model_dump(include=set(_RIGHTS)),
    )
    for spelling in data.spellings:
        entry.spellings.append(
            LexicalSpelling(
                form=spelling.form,
                form_key=search_key(spelling.form),
                script=resolved(spelling.script),
            )
        )
    for position, sense in enumerate(data.senses):
        s = LexicalSense(position=position, **sense.model_dump(exclude={"examples"}))
        for example in sense.examples:
            s.examples.append(LexicalExample(**example.model_dump()))
        entry.senses.append(s)
    session.add(entry)
    record(session, entry, "create", actor, None)
    return entry


_RIGHTS = (
    "license",
    "allow_publication",
    "allow_training",
    "consent_reference",
    "distribution_restrictions",
    "collected_on",
    "variant",
    "language",
)


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def public_query(include_pending: bool) -> Select[LexicalEntry]:
    """Seules les entrées dont la publication est autorisée et qui ne sont ni restreintes ni
    retirées sont visibles ; les entrées en attente ne le sont que sur demande, et marquées."""
    statuses = [Status.VALIDATED, Status.PENDING] if include_pending else [Status.VALIDATED]
    return (
        select(LexicalEntry)
        .where(LexicalEntry.status.in_(statuses), LexicalEntry.allow_publication.is_(True))
        .options(
            selectinload(LexicalEntry.spellings),
            selectinload(LexicalEntry.senses).selectinload(LexicalSense.examples),
            selectinload(LexicalEntry.source),
        )
    )


def search(session: Session, q: str, include_pending: bool, limit: int) -> list[LexicalEntry]:
    query = public_query(include_pending)
    key = search_key(q)
    if key:
        pattern = f"%{_escape_like(key)}%"
        spelled = select(LexicalSpelling.entry_id).where(
            LexicalSpelling.form_key.like(pattern, escape="\\")
        )
        translated = select(LexicalSense.entry_id).where(
            or_(
                func.lower(cast(LexicalSense.translation_fr, String)).like(pattern, escape="\\"),
                func.lower(cast(LexicalSense.translation_en, String)).like(pattern, escape="\\"),
            )
        )
        query = query.where(
            or_(
                LexicalEntry.headword_key.like(pattern, escape="\\"),
                LexicalEntry.id.in_(spelled),
                LexicalEntry.id.in_(translated),
            )
        ).order_by(case((LexicalEntry.headword_key == key, 0), else_=1))
    query = query.order_by(LexicalEntry.headword_key).limit(limit)
    return list(session.scalars(query))
