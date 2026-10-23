from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["capacités"])

CapabilityStatus = Literal["not_available", "experimental", "evaluated"]


class Capability(BaseModel):
    name: str
    status: CapabilityStatus
    note: str


# Source de vérité de ce que l'application affirme savoir faire. Un statut ne passe à
# « evaluated » qu'avec des résultats publiés dans evaluation/ (voir docs/phase-0-report.md).
CAPABILITIES: list[Capability] = [
    Capability(name=name, status="not_available", note="Pas encore développé.")
    for name in ("chat", "translation", "dictionary", "knowledge", "asr", "tts")
]


@router.get("/capabilities")
def capabilities() -> list[Capability]:
    return CAPABILITIES
