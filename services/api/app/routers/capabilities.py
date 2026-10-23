from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.ai.chat import ChatProvider
from app.routers.chat import get_chat_provider

router = APIRouter(prefix="/api/v1", tags=["capacités"])

CapabilityStatus = Literal["not_available", "experimental", "evaluated"]


class Capability(BaseModel):
    name: str
    status: CapabilityStatus
    note: str


# Source de vérité de ce que l'application affirme savoir faire. Un statut ne passe à
# « evaluated » qu'avec des résultats publiés dans evaluation/ (voir docs/evaluation.md).
NOT_YET = ("asr", "tts")


@router.get("/capabilities")
def capabilities(
    chat_provider: Annotated[ChatProvider | None, Depends(get_chat_provider)],
) -> list[Capability]:
    chat = (
        Capability(name="chat", status="experimental", note="Capacités en tamasheq non évaluées.")
        if chat_provider is not None
        else Capability(name="chat", status="not_available", note="Assistant non configuré.")
    )
    # Le dictionnaire fonctionne ; son contenu n'est affiché qu'après validation par un réviseur.
    dictionary = Capability(
        name="dictionary",
        status="experimental",
        note="Fonction active ; seules les entrées validées par un réviseur sont publiées.",
    )
    ai = chat_provider is not None
    translation = Capability(
        name="translation",
        status="experimental" if ai else "not_available",
        note="Qualité non évaluée." if ai else "Traduction non configurée.",
    )
    knowledge = Capability(
        name="knowledge",
        status="experimental",
        note="Recherche active ; seuls les documents validés et autorisés sont visibles.",
    )
    knowledge_qa = Capability(
        name="knowledge_qa",
        status="experimental" if ai else "not_available",
        note="Réponses fondées sur les documents publics, non évaluées."
        if ai
        else "Réponses non configurées.",
    )
    # Collecte d'enregistrements active, mais aucun modèle de reconnaissance ou de synthèse
    # vocale n'est ni intégré ni évalué pour le tamasheq.
    return [chat, dictionary, translation, knowledge, knowledge_qa] + [
        Capability(name=name, status="not_available", note="Aucun modèle évalué pour le tamasheq.")
        for name in NOT_YET
    ]
