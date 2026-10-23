"""Routes de cycle de vie communes aux contenus : validation, restriction, retrait, historique."""

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require
from app.db import get_session
from app.governance import (
    ENTITY,
    Content,
    GovernanceError,
    NotAllowed,
    restrict,
    validate,
    withdraw,
)
from app.models import Revision, Role, Status, User

Contributor = Annotated[User, Depends(require(Role.CONTRIBUTOR, Role.REVIEWER, Role.ADMIN))]
Reviewer = Annotated[User, Depends(require(Role.REVIEWER, Role.ADMIN))]
DB = Annotated[Session, Depends(get_session)]


class Created(BaseModel):
    id: uuid.UUID
    status: Status


class Decision(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


class RequiredReason(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class DatasetRef(BaseModel):
    name: str
    purpose: str
    created_at: datetime


class Withdrawn(BaseModel):
    id: uuid.UUID
    status: Status
    datasets: list[DatasetRef] = Field(
        description="Exports déjà produits qui contenaient ce contenu : à régénérer ou signaler."
    )


class RevisionOut(BaseModel):
    action: str
    actor_id: uuid.UUID | None
    at: datetime
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    reason: str | None


def refused(e: GovernanceError) -> HTTPException:
    code = status.HTTP_403_FORBIDDEN if isinstance(e, NotAllowed) else status.HTTP_409_CONFLICT
    return HTTPException(code, str(e))


def add_lifecycle_routes[C: Content](
    router: APIRouter,
    path: str,
    model: type[C],
    on_withdraw: Callable[[Session, C], None] | None = None,
) -> None:
    """`on_withdraw` s'exécute après le retrait, dans la même transaction (ex. suppression
    d'un fichier audio)."""
    entity = ENTITY[model]

    def load(session: Session, item_id: uuid.UUID) -> C:
        item = session.get(model, item_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Contenu introuvable.")
        return item

    @router.post(f"{path}/{{item_id}}/validate", operation_id=f"validate_{entity}")
    def validate_item(item_id: uuid.UUID, body: Decision, user: Reviewer, session: DB) -> Created:
        item = load(session, item_id)
        try:
            validate(session, item, user, body.reason)
        except GovernanceError as e:
            raise refused(e) from e
        session.commit()
        return Created(id=item.id, status=item.status)

    @router.post(f"{path}/{{item_id}}/restrict", operation_id=f"restrict_{entity}")
    def restrict_item(
        item_id: uuid.UUID, body: RequiredReason, user: Reviewer, session: DB
    ) -> Created:
        item = load(session, item_id)
        try:
            restrict(session, item, user, body.reason)
        except GovernanceError as e:
            raise refused(e) from e
        session.commit()
        return Created(id=item.id, status=item.status)

    @router.post(f"{path}/{{item_id}}/withdraw", operation_id=f"withdraw_{entity}")
    def withdraw_item(
        item_id: uuid.UUID, body: RequiredReason, user: Contributor, session: DB
    ) -> Withdrawn:
        item = load(session, item_id)
        try:
            datasets = withdraw(session, item, user, body.reason)
        except GovernanceError as e:
            raise refused(e) from e
        if on_withdraw is not None:
            on_withdraw(session, item)
        session.commit()
        return Withdrawn(
            id=item.id,
            status=item.status,
            datasets=[
                DatasetRef(name=d.name, purpose=d.purpose.value, created_at=d.created_at)
                for d in datasets
            ],
        )

    @router.get(f"{path}/{{item_id}}/history", operation_id=f"history_{entity}")
    def history(item_id: uuid.UUID, _: Reviewer, session: DB) -> list[RevisionOut]:
        load(session, item_id)
        revisions = session.scalars(
            select(Revision)
            .where(Revision.entity == entity, Revision.entity_id == item_id)
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
