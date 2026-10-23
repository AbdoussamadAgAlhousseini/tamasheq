"""Bibliothèque des savoirs : découpage en passages et recherche plein texte filtrée par droits.

Recherche lexicale PostgreSQL (configuration « simple », sans racinisation ni règle propre à
une langue). Une recherche sémantique (pgvector) ne sera ajoutée que si l'évaluation de la
recherche (evaluation/knowledge/) montre qu'elle est nécessaire.
"""

import re
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.governance import record
from app.models import (
    AccessLevel,
    KnowledgeChunk,
    KnowledgeDocument,
    Source,
    Status,
    Theme,
    User,
)
from app.schemas import KnowledgeDocumentIn

MAX_CHUNK = 1200

# Mots-outils français et anglais exclus de la requête, sinon presque tous les passages
# correspondraient. Aucune liste pour le tamasheq : elle devra venir des locuteurs.
STOPWORDS = frozenset(
    """au aux avec ce ces dans de des du elle en et eux il ils je la le les leur lui ma mais me
    même mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes
    toi ton tu un une vos votre vous est sont été être avoir quel quelle quels quelles comment
    pourquoi quand où dont ainsi cette cet the a an and are as at be by for from how in is it of
    on or that this to was what when where which who why with""".split()
)

_WORD = re.compile(r"\w+")


def chunk_text(body: str, max_chars: int = MAX_CHUNK) -> list[str]:
    """Découpe par paragraphes, regroupés jusqu'à `max_chars` ; un paragraphe trop long est
    coupé aux fins de phrase. Le texte n'est jamais modifié, seulement partagé."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    pieces: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            pieces.append(paragraph)
            continue
        current = ""
        for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
            while len(sentence) > max_chars:  # phrase démesurée : coupe franche
                if current:
                    pieces.append(current)
                    current = ""
                pieces.append(sentence[:max_chars])
                sentence = sentence[max_chars:]
            if current and len(current) + 1 + len(sentence) > max_chars:
                pieces.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            pieces.append(current)

    chunks: list[str] = []
    for piece in pieces:
        if chunks and len(chunks[-1]) + 2 + len(piece) <= max_chars:
            chunks[-1] = f"{chunks[-1]}\n\n{piece}"
        else:
            chunks.append(piece)
    return chunks


def create_document(
    session: Session, data: KnowledgeDocumentIn, source: Source, actor: User | None, status: Status
) -> KnowledgeDocument:
    document = KnowledgeDocument(
        title=data.title,
        body=data.body,
        theme=data.theme,
        access_level=data.access_level,
        author_credit=data.author_credit,
        source_id=source.id,
        contributor_id=actor.id if actor and status != Status.RAW else None,
        status=status,
        **data.model_dump(include=set(RIGHTS)),
    )
    for position, text in enumerate(chunk_text(data.body)):
        document.chunks.append(KnowledgeChunk(position=position, text=text))
    session.add(document)
    record(session, document, "create", actor, None)
    return document


RIGHTS = (
    "license",
    "allow_publication",
    "allow_training",
    "consent_reference",
    "distribution_restrictions",
    "collected_on",
    "variant",
    "language",
)


def visible_levels(user: User | None) -> list[AccessLevel]:
    """Le niveau restreint n'est jamais servi par l'API, quel que soit le compte."""
    return [AccessLevel.PUBLIC, AccessLevel.COMMUNITY] if user else [AccessLevel.PUBLIC]


def query_terms(q: str) -> list[str]:
    terms: list[str] = []
    for word in _WORD.findall(q.casefold()):
        if len(word) >= 2 and word not in STOPWORDS and word not in terms:
            terms.append(word)
    return terms[:20]


@dataclass(frozen=True)
class Hit:
    chunk: KnowledgeChunk
    rank: float


def search_chunks(
    session: Session,
    q: str,
    levels: list[AccessLevel],
    theme: Theme | None = None,
    limit: int = 10,
) -> list[Hit]:
    terms = query_terms(q)
    if not terms:
        return []
    # Les termes ne contiennent que des caractères de mot : aucune syntaxe tsquery injectable.
    tsquery = func.to_tsquery("simple", " | ".join(terms))
    rank = func.ts_rank_cd(KnowledgeChunk.tsv, tsquery)
    query = (
        select(KnowledgeChunk, rank)
        .join(KnowledgeDocument)
        .where(
            KnowledgeChunk.tsv.op("@@")(tsquery),
            KnowledgeDocument.status == Status.VALIDATED,
            KnowledgeDocument.allow_publication.is_(True),
            KnowledgeDocument.access_level.in_(levels),
        )
        .options(selectinload(KnowledgeChunk.document).selectinload(KnowledgeDocument.source))
        .order_by(rank.desc(), KnowledgeChunk.id)
        .limit(limit)
    )
    if theme is not None:
        query = query.where(KnowledgeDocument.theme == theme)
    return [Hit(chunk=c, rank=float(r)) for c, r in session.execute(query)]


def visible_document(
    session: Session, document_id: uuid.UUID, levels: list[AccessLevel]
) -> KnowledgeDocument | None:
    return session.scalar(
        select(KnowledgeDocument)
        .where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.status == Status.VALIDATED,
            KnowledgeDocument.allow_publication.is_(True),
            KnowledgeDocument.access_level.in_(levels),
        )
        .options(selectinload(KnowledgeDocument.source))
    )


def list_documents(
    session: Session, levels: list[AccessLevel], theme: Theme | None, limit: int
) -> list[KnowledgeDocument]:
    query = (
        select(KnowledgeDocument)
        .where(
            KnowledgeDocument.status == Status.VALIDATED,
            KnowledgeDocument.allow_publication.is_(True),
            KnowledgeDocument.access_level.in_(levels),
        )
        .options(selectinload(KnowledgeDocument.source))
        .order_by(KnowledgeDocument.title)
        .limit(limit)
    )
    if theme is not None:
        query = query.where(KnowledgeDocument.theme == theme)
    return list(session.scalars(query))
