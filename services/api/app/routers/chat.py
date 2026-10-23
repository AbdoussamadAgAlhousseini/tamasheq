from functools import lru_cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, model_validator

from app.ai.anthropic_backend import AnthropicBackend
from app.ai.anthropic_chat import AnthropicChatProvider
from app.ai.chat import ChatMessage, ChatProvider, ChatProviderError
from app.config import get_settings
from app.ratelimit import SlidingWindowLimiter

router = APIRouter(prefix="/api/v1", tags=["assistant"])

MAX_MESSAGES = 20
MAX_CHARS = 4000


class MessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_CHARS)


class ChatRequest(BaseModel):
    """Historique complet de la session, conservé par le navigateur et jamais stocké ici."""

    messages: list[MessageIn] = Field(min_length=1, max_length=MAX_MESSAGES)

    @model_validator(mode="after")
    def alternating_roles(self) -> "ChatRequest":
        for i, message in enumerate(self.messages):
            expected = "user" if i % 2 == 0 else "assistant"
            if message.role != expected:
                raise ValueError("les messages doivent alterner user/assistant")
        if self.messages[-1].role != "user":
            raise ValueError("le dernier message doit venir de l'utilisateur")
        return self


class ChatResponse(BaseModel):
    reply: str
    provider: str
    model: str
    truncated: bool
    # Rappel contractuel : aucune réponse n'est vérifiée tant que l'évaluation n'est pas publiée.
    status: Literal["experimental"] = "experimental"
    verified: Literal[False] = False


@lru_cache
def get_backend() -> AnthropicBackend | None:
    """Client du modèle, partagé par l'assistant, la traduction et les réponses citées ;
    absent tant qu'aucune clé n'est configurée."""
    settings = get_settings()
    if settings.anthropic_api_key is None:
        return None
    return AnthropicBackend(
        api_key=settings.anthropic_api_key.get_secret_value(),
        model=settings.chat_model,
        effort=settings.chat_effort,
    )


@lru_cache
def get_chat_provider() -> ChatProvider | None:
    backend = get_backend()
    return AnthropicChatProvider(backend) if backend else None


@lru_cache
def get_limiter() -> SlidingWindowLimiter:
    return SlidingWindowLimiter(get_settings().chat_requests_per_minute)


def _error(code: int, kind: str, message: str) -> HTTPException:
    return HTTPException(status_code=code, detail={"code": kind, "message": message})


def provider_failure(e: ChatProviderError) -> HTTPException:
    """Réponse HTTP pour une erreur du fournisseur de modèle (commune à tous les modules IA)."""
    if e.kind == "refused":
        return _error(422, "refused", "Le modèle a refusé de répondre.")
    if e.kind == "unavailable":
        return _error(503, "unavailable", "Service de modèle indisponible.")
    return _error(status.HTTP_502_BAD_GATEWAY, "provider_error", "Erreur du fournisseur.")


@router.post("/chat")
async def chat(
    body: ChatRequest,
    request: Request,
    provider: Annotated[ChatProvider | None, Depends(get_chat_provider)],
    limiter: Annotated[SlidingWindowLimiter, Depends(get_limiter)],
) -> ChatResponse:
    if provider is None:
        raise _error(503, "not_configured", "Assistant non configuré.")
    client = request.client.host if request.client else "unknown"
    if not limiter.allow(client):
        raise _error(429, "rate_limited", "Trop de messages, réessayez dans une minute.")

    try:
        reply = await provider.reply([ChatMessage(m.role, m.content) for m in body.messages])
    except ChatProviderError as e:
        raise provider_failure(e) from e

    return ChatResponse(
        reply=reply.text, provider=reply.provider, model=reply.model, truncated=reply.truncated
    )
