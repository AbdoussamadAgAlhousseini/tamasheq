"""Entrées du dictionnaire utiles à une traduction.

Seules des entrées validées et publiables sont retenues : elles sont transmises au fournisseur
du modèle (décision D6, textes publics uniquement).
"""

import re
import uuid
from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import LexicalEntry, LexicalSense, LexicalSpelling, Status
from app.text import search_key

MAX_ENTRIES = 15
_WORD = re.compile(r"\w+")


@dataclass(frozen=True)
class GlossaryEntry:
    ref: str  # identifiant court donné au modèle (G1, G2…)
    entry_id: uuid.UUID
    headword: str
    other_forms: list[str]
    translations_fr: list[str]
    translations_en: list[str]


def lookup(session: Session, text: str, source_lang: str) -> list[GlossaryEntry]:
    keys = list(dict.fromkeys(search_key(w) for w in _WORD.findall(text)))[:100]
    if not keys:
        return []
    if source_lang == "taq":
        match = or_(
            LexicalEntry.headword_key.in_(keys),
            LexicalEntry.id.in_(
                select(LexicalSpelling.entry_id).where(LexicalSpelling.form_key.in_(keys))
            ),
        )
    else:
        column = LexicalSense.translation_fr if source_lang == "fr" else LexicalSense.translation_en
        match = LexicalEntry.id.in_(
            select(LexicalSense.entry_id).where(func.lower(column).in_(keys))
        )
    entries = session.scalars(
        select(LexicalEntry)
        .where(
            match,
            LexicalEntry.status == Status.VALIDATED,
            LexicalEntry.allow_publication.is_(True),
        )
        .options(selectinload(LexicalEntry.spellings), selectinload(LexicalEntry.senses))
        .order_by(LexicalEntry.headword_key)
        .limit(MAX_ENTRIES)
    )
    return [
        GlossaryEntry(
            ref=f"G{i}",
            entry_id=e.id,
            headword=e.headword,
            other_forms=[s.form for s in e.spellings],
            translations_fr=[s.translation_fr for s in e.senses if s.translation_fr],
            translations_en=[s.translation_en for s in e.senses if s.translation_en],
        )
        for i, e in enumerate(entries, start=1)
    ]
