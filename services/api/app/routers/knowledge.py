import uuid
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.chat import ChatProviderError
from app.ai.knowledge_qa import AnswerProvider, AnthropicAnswerProvider, Passage
from app.auth import optional_user
from app.db import get_session
from app.models import AccessLevel, KnowledgeDocument, Theme, User
from app.ratelimit import SlidingWindowLimiter
from app.routers.chat import get_backend, get_limiter, provider_failure
from app.routers.lifecycle import add_lifecycle_routes
from app.services import knowledge

router = APIRouter(prefix="/api/v1", tags=["savoirs"])

DB = Annotated[Session, Depends(get_session)]
MaybeUser = Annotated[User | None, Depends(optional_user)]

# Passages transmis au modèle pour une question.
ANSWER_PASSAGES = 6


@lru_cache
def get_answer_provider() -> AnswerProvider | None:
    backend = get_backend()
    return AnthropicAnswerProvider(backend) if backend else None


class SourceOut(BaseModel):
    title: str
    citation: str | None
    url: str | None


class DocumentSummary(BaseModel):
    id: uuid.UUID
    title: str
    theme: Theme
    access_level: AccessLevel
    language: str
    author_credit: str | None
    source: SourceOut
    license: str
    excerpt: str

    @classmethod
    def of(cls, d: KnowledgeDocument, excerpt: str) -> "DocumentSummary":
        return cls(
            id=d.id,
            title=d.title,
            theme=d.theme,
            access_level=d.access_level,
            language=d.language,
            author_credit=d.author_credit,
            source=SourceOut(title=d.source.title, citation=d.source.citation, url=d.source.url),
            license=d.license,
            excerpt=excerpt,
        )


class DocumentOut(DocumentSummary):
    body: str


def _excerpt(text: str, size: int = 300) -> str:
    return text if len(text) <= size else text[:size].rsplit(" ", 1)[0] + " …"


@router.get("/knowledge")
def search_documents(
    session: DB,
    user: MaybeUser,
    q: Annotated[str, Query(max_length=300)] = "",
    theme: Theme | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[DocumentSummary]:
    """Documents visibles : publics pour tous, « communauté » avec un compte, jamais restreints."""
    levels = knowledge.visible_levels(user)
    if not q.strip():
        return [
            DocumentSummary.of(d, _excerpt(d.body))
            for d in knowledge.list_documents(session, levels, theme, limit)
        ]
    seen: dict[uuid.UUID, DocumentSummary] = {}
    for hit in knowledge.search_chunks(session, q, levels, theme, limit * 3):
        doc = hit.chunk.document
        if doc.id not in seen:
            seen[doc.id] = DocumentSummary.of(doc, _excerpt(hit.chunk.text))
    return list(seen.values())[:limit]


@router.get("/knowledge/{document_id}")
def get_document(document_id: uuid.UUID, session: DB, user: MaybeUser) -> DocumentOut:
    doc = knowledge.visible_document(session, document_id, knowledge.visible_levels(user))
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable.")
    return DocumentOut(**DocumentSummary.of(doc, _excerpt(doc.body)).model_dump(), body=doc.body)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class Reference(BaseModel):
    ref: str
    document_id: uuid.UUID
    title: str
    source: SourceOut
    license: str
    passage: str


class AskResponse(BaseModel):
    answer: str | None
    insufficient_documentation: bool
    references: list[Reference] = Field(description="Passages effectivement cités")
    provider: str | None
    model: str | None
    status: Literal["experimental"] = "experimental"
    verified: Literal[False] = False


@router.post("/knowledge/ask")
async def ask(
    body: AskRequest,
    request: Request,
    session: DB,
    provider: Annotated[AnswerProvider | None, Depends(get_answer_provider)],
    limiter: Annotated[SlidingWindowLimiter, Depends(get_limiter)],
) -> AskResponse:
    """Seuls des passages de documents **publics** et validés sont transmis au modèle, quel que
    soit le compte de la personne qui pose la question."""
    if provider is None:
        raise HTTPException(503, {"code": "not_configured", "message": "Réponses non configurées."})
    if not limiter.allow(request.client.host if request.client else "unknown"):
        raise HTTPException(429, {"code": "rate_limited", "message": "Trop de requêtes."})

    hits = knowledge.search_chunks(
        session, body.question, [AccessLevel.PUBLIC], None, ANSWER_PASSAGES
    )
    if not hits:
        # Rien de documenté : pas d'appel au modèle, pas de réponse générée.
        return AskResponse(
            answer=None,
            insufficient_documentation=True,
            references=[],
            provider=None,
            model=None,
        )
    passages = [
        Passage(ref=f"P{i}", title=h.chunk.document.title, text=h.chunk.text)
        for i, h in enumerate(hits, start=1)
    ]
    by_ref = {
        p.ref: Reference(
            ref=p.ref,
            document_id=h.chunk.document.id,
            title=h.chunk.document.title,
            source=SourceOut(
                title=h.chunk.document.source.title,
                citation=h.chunk.document.source.citation,
                url=h.chunk.document.source.url,
            ),
            license=h.chunk.document.license,
            passage=h.chunk.text,
        )
        for p, h in zip(passages, hits, strict=True)
    }
    session.close()  # aucune requête en base pendant l'appel au modèle
    try:
        result = await provider.answer(body.question, passages)
    except ChatProviderError as e:
        raise provider_failure(e) from e
    references = [by_ref[r] for r in result.cited]
    return AskResponse(
        answer=result.text,
        # Une réponse sans aucune citation n'est pas considérée comme fondée.
        insufficient_documentation=result.insufficient or not references,
        references=references,
        provider=result.provider,
        model=result.model,
    )


add_lifecycle_routes(router, "/knowledge", KnowledgeDocument)
