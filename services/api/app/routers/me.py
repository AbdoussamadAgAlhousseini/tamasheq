from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import current_user
from app.models import Role, User

router = APIRouter(prefix="/api/v1", tags=["compte"])


class Me(BaseModel):
    pseudonym: str
    role: Role


@router.get("/me")
def me(user: Annotated[User, Depends(current_user)]) -> Me:
    """Vérifie un jeton et renvoie le compte associé (sans l'adresse e-mail)."""
    return Me(pseudonym=user.pseudonym, role=user.role)
