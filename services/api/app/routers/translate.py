import uuid
from functools import lru_cache
from typing import Annotated, Literal, Self

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.ai.chat import ChatProviderError
from app.ai.translation import AnthropicTranslationProvider, Lang, TranslationProvider
from app.db import get_session
from app.models import Status
from app.ratelimit import SlidingWindowLimiter
from app.routers.chat import get_backend, get_limiter, provider_failure
from app.routers.dictionary import personal_source
from app.routers.lifecycle import Contributor, Created
from app.schemas import CorpusTextIn, Rights
from app.services import corpus, glossary

router = APIRouter(prefix="/api/v1", tags=["traduction"])


@lru_cache
def get_translation_provider() -> TranslationProvider | None:
    backend = get_backend()
    return AnthropicTranslationProvider(backend) if backend else None


class Direction(BaseModel):
    source_lang: Lang
    target_lang: Lang

    @model_validator(mode="after")
    def one_side_is_tamasheq(self) -> Self:
        if self.source_lang == self.target_lang or "taq" not in (
            self.source_lang,
            self.target_lang,
        ):
            raise ValueError("une des deux langues doit être le tamasheq (taq), l'autre différente")
        return self


class TranslateRequest(Direction):
    text: str = Field(min_length=1, max_length=2000)
    variant: str | None = Field(default=None, max_length=200)


class GlossaryRef(BaseModel):
    id: uuid.UUID
    headword: str


class TranslateResponse(BaseModel):
    translation: str
    alternatives: list[str]
    ambiguities: list[str]
    notes: str
    glossary: list[GlossaryRef] = Field(description="Entrées validées du dictionnaire utilisées")
    provider: str
    model: str
    truncated: bool
    status: Literal["experimental"] = "experimental"
    verified: Literal[False] = False


@router.post("/translate")
async def translate(
    body: TranslateRequest,
    request: Request,
    provider: Annotated[TranslationProvider | None, Depends(get_translation_provider)],
    limiter: Annotated[SlidingWindowLimiter, Depends(get_limiter)],
    session: Annotated[Session, Depends(get_session)],
) -> TranslateResponse:
    if provider is None:
        raise HTTPException(
            503, {"code": "not_configured", "message": "Traduction non configurée."}
        )
    if not limiter.allow(request.client.host if request.client else "unknown"):
        raise HTTPException(429, {"code": "rate_limited", "message": "Trop de requêtes."})

    entries = glossary.lookup(session, body.text, body.source_lang)
    session.close()  # aucune requête en base pendant l'appel au modèle
    try:
        result = await provider.translate(
            body.text, body.source_lang, body.target_lang, body.variant, entries
        )
    except ChatProviderError as e:
        raise provider_failure(e) from e
    by_ref = {g.ref: g for g in entries}
    return TranslateResponse(
        translation=result.translation,
        alternatives=result.alternatives,
        ambiguities=result.ambiguities,
        notes=result.notes,
        glossary=[
            GlossaryRef(id=by_ref[r].entry_id, headword=by_ref[r].headword)
            for r in result.glossary_used
        ],
        provider=result.provider,
        model=result.model,
        truncated=result.truncated,
    )


class CorrectionIn(Direction, Rights):
    """Correction proposée par un locuteur : elle entre au corpus comme texte « en attente »,
    avec le côté tamasheq comme texte original."""

    source_text: str = Field(min_length=1, max_length=2000)
    corrected_translation: str = Field(min_length=1, max_length=2000)
    machine_model: str | None = Field(default=None, max_length=100)


@router.post("/translate/corrections", status_code=status.HTTP_201_CREATED)
def propose_correction(
    body: CorrectionIn, user: Contributor, session: Annotated[Session, Depends(get_session)]
) -> Created:
    if body.source_lang == "taq":
        tamasheq, other, other_lang = body.source_text, body.corrected_translation, body.target_lang
    else:
        tamasheq, other, other_lang = body.corrected_translation, body.source_text, body.source_lang
    note = "Correction d'une traduction automatique proposée par un locuteur"
    if body.machine_model:
        note += f" (modèle : {body.machine_model})"
    text = CorpusTextIn.model_validate(
        {
            "text": tamasheq,
            f"translation_{other_lang}": other,
            "notes": note + ".",
            **body.model_dump(include=set(Rights.model_fields)),
        }
    )
    created = corpus.create_text(
        session, text, personal_source(session, user), user, Status.PENDING
    )
    session.commit()
    return Created(id=created.id, status=created.status)
