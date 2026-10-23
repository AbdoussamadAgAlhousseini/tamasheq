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
NOT_YET = ("translation", "dictionary", "knowledge", "asr", "tts")


@router.get("/capabilities")
def capabilities(
    chat_provider: Annotated[ChatProvider | None, Depends(get_chat_provider)],
) -> list[Capability]:
    chat = (
        Capability(name="chat", status="experimental", note="Capacités en tamasheq non évaluées.")
        if chat_provider is not None
        else Capability(name="chat", status="not_available", note="Assistant non configuré.")
    )
    return [chat] + [
        Capability(name=name, status="not_available", note="Pas encore développé.")
        for name in NOT_YET
    ]
