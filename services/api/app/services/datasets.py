"""Exports figés et traçables.

Règles de sélection, volontairement prudentes :
- seuls les contenus validés sont exportés (jamais bruts, en attente, restreints ou retirés) ;
- un export d'entraînement exige l'accord du contributeur (`allow_training`) ET une source dont
  la licence autorise l'entraînement (`license_allows_training`, « inconnu » valant « non ») ;
- un export de publication exige `allow_publication` ;
- tout contenu portant une restriction de diffusion est exclu des exports automatiques.

Chaque élément exporté est enregistré dans `dataset_items` pour retrouver, lors d'un retrait,
les exports concernés.
"""

import hashlib
import json
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.governance import ENTITY, Content
from app.models import (
    CorpusText,
    Dataset,
    DatasetItem,
    DatasetPurpose,
    LexicalEntry,
    LexicalSense,
    Source,
    Status,
    User,
)

Kind = Literal["lexicon", "corpus"]


def _source(source: Source) -> dict[str, Any]:
    return {
        "title": source.title,
        "citation": source.citation,
        "url": source.url,
        "rights_holder": source.rights_holder,
        "license": source.license,
    }


def _common(obj: Content) -> dict[str, Any]:
    return {
        "id": str(obj.id),
        "language": obj.language,
        "variant": obj.variant,
        "license": obj.license,
        "source": _source(obj.source),
        "validated_at": obj.validated_at.isoformat() if obj.validated_at else None,
    }


def serialize_entry(entry: LexicalEntry) -> dict[str, Any]:
    return _common(entry) | {
        "headword": entry.headword,
        "script": entry.headword_script.value,
        "part_of_speech": entry.part_of_speech,
        "spellings": [{"form": s.form, "script": s.script.value} for s in entry.spellings],
        "senses": [
            {
                "definition_fr": s.definition_fr,
                "definition_en": s.definition_en,
                "translation_fr": s.translation_fr,
                "translation_en": s.translation_en,
                "examples": [
                    {
                        "text": e.text,
                        "script": e.script.value,
                        "translation_fr": e.translation_fr,
                        "translation_en": e.translation_en,
                    }
                    for e in s.examples
                ],
            }
            for s in entry.senses
        ],
    }


def serialize_text(text: CorpusText) -> dict[str, Any]:
    return _common(text) | {
        "text": text.original_text,
        "script": text.script.value,
        "tifinagh_text": text.tifinagh_text,
        "translation_fr": text.translation_fr,
        "translation_en": text.translation_en,
    }


def serialize(obj: Content) -> dict[str, Any]:
    return serialize_entry(obj) if isinstance(obj, LexicalEntry) else serialize_text(obj)


def select_items(session: Session, kind: Kind, purpose: DatasetPurpose) -> list[Content]:
    model: type[LexicalEntry] | type[CorpusText] = LexicalEntry if kind == "lexicon" else CorpusText
    query = (
        select(model)
        .join(Source, model.source_id == Source.id)
        .where(model.status == Status.VALIDATED, model.distribution_restrictions.is_(None))
        .order_by(model.id)
    )
    if purpose == DatasetPurpose.TRAINING:
        query = query.where(
            model.allow_training.is_(True), Source.license_allows_training.is_(True)
        )
    else:
        query = query.where(model.allow_publication.is_(True))
    if model is LexicalEntry:
        query = query.options(
            selectinload(LexicalEntry.spellings),
            selectinload(LexicalEntry.senses).selectinload(LexicalSense.examples),
        )
    return list(session.scalars(query))


def export(
    session: Session, kind: Kind, purpose: DatasetPurpose, name: str, actor: User | None
) -> tuple[Dataset, str]:
    items = select_items(session, kind, purpose)
    lines = [json.dumps(serialize(i), ensure_ascii=False, sort_keys=True) for i in items]
    content = "".join(f"{line}\n" for line in lines)
    dataset = Dataset(
        name=name,
        purpose=purpose,
        kind=kind,
        criteria={
            "status": "validated",
            "requires": "allow_training+license_allows_training"
            if purpose == DatasetPurpose.TRAINING
            else "allow_publication",
            "excludes": "distribution_restrictions",
        },
        file_sha256=hashlib.sha256(content.encode()).hexdigest(),
        item_count=len(items),
        created_by=actor.id if actor else None,
    )
    session.add(dataset)
    session.flush()
    session.add_all(
        DatasetItem(dataset_id=dataset.id, entity=ENTITY[type(i)], entity_id=i.id) for i in items
    )
    return dataset, content
