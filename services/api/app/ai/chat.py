"""Interface de conversation, indépendante du fournisseur de modèle.

Le reste de l'application ne dépend que de ce module : changer de fournisseur revient à écrire
une autre implémentation de ChatProvider.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

Role = Literal["user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class ChatReply:
    text: str
    provider: str
    model: str
    truncated: bool


ErrorKind = Literal["refused", "unavailable", "misconfigured"]


class ChatProviderError(Exception):
    """Erreur côté fournisseur, classée pour choisir la réponse HTTP et le message affiché."""

    def __init__(self, kind: ErrorKind, detail: str) -> None:
        super().__init__(detail)
        self.kind = kind


class ChatProvider(Protocol):
    name: str

    async def reply(self, messages: list[ChatMessage]) -> ChatReply: ...
