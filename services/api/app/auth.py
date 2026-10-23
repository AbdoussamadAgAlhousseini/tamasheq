"""Authentification par jeton porteur (en-tête `Authorization: Bearer <jeton>`).

Les jetons sont créés en ligne de commande (`python -m app.cli create-user`), montrés une seule
fois, et seule leur empreinte SHA-256 est stockée. Une connexion depuis l'interface web viendra
plus tard ; ce mécanisme suffit aux réviseurs et à l'administration.
"""

import hashlib
import secrets
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import ApiToken, Role, User

_bearer = HTTPBearer(auto_error=False)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_token(session: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    session.add(ApiToken(user_id=user.id, token_hash=hash_token(token)))
    return token


def optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[Session, Depends(get_session)],
) -> User | None:
    """Personne connectée, ou None sans jeton. Un jeton invalide est refusé, pas ignoré."""
    if credentials is None:
        return None
    token = session.scalar(
        select(ApiToken).where(
            ApiToken.token_hash == hash_token(credentials.credentials),
            ApiToken.revoked_at.is_(None),
        )
    )
    if token is None or not token.user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Jeton invalide ou révoqué.")
    return token.user


def current_user(user: Annotated[User | None, Depends(optional_user)]) -> User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise.")
    return user


def require(*roles: Role) -> Callable[[User], User]:
    def check(user: Annotated[User, Depends(current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Rôle insuffisant.")
        return user

    return check
