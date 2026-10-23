"""Règles de cycle de vie des contenus et journal des révisions.

Toute modification d'un contenu passe par ce module : il vérifie la transition, l'applique et
l'inscrit dans `revisions` avec l'état avant et après.
"""

import enum
import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CorpusText,
    Dataset,
    DatasetItem,
    KnowledgeDocument,
    LexicalEntry,
    Revision,
    Role,
    Status,
    User,
)

Content = LexicalEntry | CorpusText | KnowledgeDocument

ENTITY: dict[type, str] = {
    LexicalEntry: "lexical_entry",
    CorpusText: "corpus_text",
    KnowledgeDocument: "knowledge_document",
}


class GovernanceError(Exception):
    """Transition refusée ; le message est destiné à l'utilisateur."""


class NotAllowed(GovernanceError):
    """La personne n'a pas le droit d'effectuer cette action."""


def snapshot(obj: Content) -> dict[str, Any]:
    def plain(value: Any) -> Any:
        if isinstance(value, enum.Enum):
            return value.value
        if isinstance(value, uuid.UUID | datetime | date):
            return str(value) if isinstance(value, uuid.UUID) else value.isoformat()
        return value

    columns = type(obj).__mapper__.column_attrs
    return {attr.key: plain(getattr(obj, attr.key)) for attr in columns}


def record(
    session: Session,
    obj: Content,
    action: str,
    actor: User | None,
    before: dict[str, Any] | None,
    reason: str | None = None,
) -> None:
    session.flush()
    session.add(
        Revision(
            entity=ENTITY[type(obj)],
            entity_id=obj.id,
            action=action,
            actor_id=actor.id if actor else None,
            before=before,
            after=snapshot(obj),
            reason=reason,
        )
    )


def _is_staff(user: User) -> bool:
    return user.role in (Role.REVIEWER, Role.ADMIN)


def validate(session: Session, obj: Content, reviewer: User, reason: str | None) -> None:
    """Valider exige un réviseur distinct du contributeur (contrôle à quatre yeux)."""
    if not _is_staff(reviewer):
        raise NotAllowed("Seul un réviseur peut valider.")
    if obj.status not in (Status.RAW, Status.PENDING):
        raise GovernanceError(f"Impossible de valider un contenu au statut « {obj.status} ».")
    if obj.contributor_id is not None and obj.contributor_id == reviewer.id:
        raise NotAllowed("On ne peut pas valider sa propre contribution.")
    before = snapshot(obj)
    obj.status = Status.VALIDATED
    obj.validated_by = reviewer.id
    obj.validated_at = datetime.now(UTC)
    record(session, obj, "validate", reviewer, before, reason)


def restrict(session: Session, obj: Content, reviewer: User, reason: str) -> None:
    if not _is_staff(reviewer):
        raise NotAllowed("Seul un réviseur peut restreindre un contenu.")
    if obj.status == Status.WITHDRAWN:
        raise GovernanceError("Un contenu retiré ne peut pas être restreint.")
    before = snapshot(obj)
    obj.status = Status.RESTRICTED
    record(session, obj, "restrict", reviewer, before, reason)


def withdraw(session: Session, obj: Content, actor: User, reason: str) -> list[Dataset]:
    """Retire un contenu et renvoie les exports qui l'incluaient (à régénérer ou signaler).

    Le contenu reste en base, marqué retiré, pour garder la trace du retrait ; il n'apparaît
    plus nulle part et n'entre plus dans aucun export.
    """
    if actor.role != Role.ADMIN and obj.contributor_id != actor.id:
        raise NotAllowed("Seuls l'administration ou le contributeur peuvent le retirer.")
    if obj.status == Status.WITHDRAWN:
        raise GovernanceError("Contenu déjà retiré.")
    before = snapshot(obj)
    obj.status = Status.WITHDRAWN
    record(session, obj, "withdraw", actor, before, reason)
    return datasets_containing(session, obj)


def datasets_containing(session: Session, obj: Content) -> list[Dataset]:
    return list(
        session.scalars(
            select(Dataset)
            .join(DatasetItem, DatasetItem.dataset_id == Dataset.id)
            .where(DatasetItem.entity == ENTITY[type(obj)], DatasetItem.entity_id == obj.id)
            .order_by(Dataset.created_at)
        )
    )
