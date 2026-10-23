import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Role(enum.StrEnum):
    """Rôles applicatifs. Les droits précis seront définis avec la gouvernance des données."""

    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    ADMIN = "admin"


class User(Base):
    """Compte utilisateur. Le pseudonyme est l'identifiant public ; l'e-mail n'est jamais publié.

    La méthode d'authentification (mot de passe, lien magique, OAuth) sera choisie plus tard :
    aucune donnée d'authentification n'est stockée à ce stade.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    pseudonym: Mapped[str] = mapped_column(String(64), unique=True)
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", values_callable=lambda e: [r.value for r in e]),
        default=Role.CONTRIBUTOR,
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
