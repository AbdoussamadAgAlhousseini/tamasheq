import enum
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Computed,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.db import Base


def _enum(cls: type[enum.Enum], name: str) -> Enum:
    return Enum(cls, name=name, values_callable=lambda e: [m.value for m in e])


class Role(enum.StrEnum):
    """Rôles applicatifs. Les droits précis seront définis avec la gouvernance des données."""

    CONTRIBUTOR = "contributor"
    REVIEWER = "reviewer"
    ADMIN = "admin"


class User(Base):
    """Compte utilisateur. Le pseudonyme est l'identifiant public ; l'e-mail n'est jamais publié."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    pseudonym: Mapped[str] = mapped_column(String(64), unique=True)
    role: Mapped[Role] = mapped_column(_enum(Role, "user_role"), default=Role.CONTRIBUTOR)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApiToken(Base):
    """Jeton d'accès. Seule l'empreinte SHA-256 est stockée ; le jeton n'est montré qu'une fois."""

    __tablename__ = "api_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()


class Status(enum.StrEnum):
    RAW = "raw"  # importé ou saisi, pas encore soumis à relecture
    PENDING = "pending"  # en attente de validation
    VALIDATED = "validated"  # validé par un réviseur autre que le contributeur
    RESTRICTED = "restricted"  # jamais publié ni exporté sans autorisation particulière
    WITHDRAWN = "withdrawn"  # retiré par son contributeur ou par l'administration


class Script(enum.StrEnum):
    LATN = "Latn"
    TFNG = "Tfng"


class SourceKind(enum.StrEnum):
    CONTRIBUTION = "contribution"
    INTERVIEW = "interview"
    RECORDING = "recording"
    PUBLICATION = "publication"
    DICTIONARY = "dictionary"
    DATASET = "dataset"
    OTHER = "other"


class Source(Base):
    """Provenance d'un ensemble de données, avec ses droits."""

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text)
    kind: Mapped[SourceKind] = mapped_column(_enum(SourceKind, "source_kind"))
    citation: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    rights_holder: Mapped[str | None] = mapped_column(Text)
    # Licence ou régime de droits tel qu'énoncé (identifiant SPDX ou texte).
    license: Mapped[str] = mapped_column(Text)
    # La licence ou l'accord autorise-t-il l'entraînement ? None : non établi (traité comme non).
    license_allows_training: Mapped[bool | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrthographyConvention(Base):
    """Convention d'écriture (décision D4), enregistrée comme donnée et non codée en dur."""

    __tablename__ = "orthography_conventions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    script: Mapped[Script] = mapped_column(_enum(Script, "script"))
    description: Mapped[str | None] = mapped_column(Text)
    reference: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Governed:
    """Champs de provenance, de droits et de validation communs aux contenus linguistiques.

    Autoriser la publication et autoriser l'entraînement sont deux décisions distinctes ;
    toutes deux valent « non » par défaut.
    """

    language: Mapped[str] = mapped_column(String(8), default="taq")
    variant: Mapped[str | None] = mapped_column(Text)
    collected_on: Mapped[date | None] = mapped_column(Date)
    license: Mapped[str] = mapped_column(Text)
    consent_reference: Mapped[str | None] = mapped_column(Text)
    allow_publication: Mapped[bool] = mapped_column(default=False)
    allow_training: Mapped[bool] = mapped_column(default=False)
    distribution_restrictions: Mapped[str | None] = mapped_column(Text)
    status: Mapped[Status] = mapped_column(_enum(Status, "content_status"), default=Status.PENDING)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @declared_attr
    def source_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(ForeignKey("sources.id"))

    @declared_attr
    def contributor_id(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(ForeignKey("users.id"))

    @declared_attr
    def validated_by(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(ForeignKey("users.id"))


class LexicalEntry(Governed, Base):
    """Entrée du dictionnaire. `headword` est la forme d'origine, jamais modifiée (contrainte
    en base) ; les autres graphies sont des LexicalSpelling."""

    __tablename__ = "lexical_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    headword: Mapped[str] = mapped_column(Text)
    headword_script: Mapped[Script] = mapped_column(_enum(Script, "script"))
    headword_key: Mapped[str] = mapped_column(Text, index=True)
    part_of_speech: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    source: Mapped[Source] = relationship()
    spellings: Mapped[list["LexicalSpelling"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan", order_by="LexicalSpelling.form"
    )
    senses: Mapped[list["LexicalSense"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan", order_by="LexicalSense.position"
    )


class LexicalSpelling(Base):
    """Graphie d'une entrée, dans une écriture et selon une convention éventuelle."""

    __tablename__ = "lexical_spellings"
    __table_args__ = (UniqueConstraint("entry_id", "script", "form"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lexical_entries.id"))
    form: Mapped[str] = mapped_column(Text)
    form_key: Mapped[str] = mapped_column(Text, index=True)
    script: Mapped[Script] = mapped_column(_enum(Script, "script"))
    convention_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("orthography_conventions.id")
    )
    validated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    entry: Mapped[LexicalEntry] = relationship(back_populates="spellings")


class LexicalSense(Base):
    __tablename__ = "lexical_senses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lexical_entries.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    definition_fr: Mapped[str | None] = mapped_column(Text)
    definition_en: Mapped[str | None] = mapped_column(Text)
    translation_fr: Mapped[str | None] = mapped_column(Text)
    translation_en: Mapped[str | None] = mapped_column(Text)

    entry: Mapped[LexicalEntry] = relationship(back_populates="senses")
    examples: Mapped[list["LexicalExample"]] = relationship(
        back_populates="sense", cascade="all, delete-orphan"
    )


class LexicalExample(Base):
    __tablename__ = "lexical_examples"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sense_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lexical_senses.id"))
    text: Mapped[str] = mapped_column(Text)
    script: Mapped[Script] = mapped_column(_enum(Script, "script"))
    translation_fr: Mapped[str | None] = mapped_column(Text)
    translation_en: Mapped[str | None] = mapped_column(Text)

    sense: Mapped[LexicalSense] = relationship(back_populates="examples")


class CorpusText(Governed, Base):
    """Unité de corpus (phrase, énoncé, court texte). `original_text` n'est jamais modifié."""

    __tablename__ = "corpus_texts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    original_text: Mapped[str] = mapped_column(Text)
    script: Mapped[Script] = mapped_column(_enum(Script, "script"))
    normalized_text: Mapped[str] = mapped_column(Text)
    tifinagh_text: Mapped[str | None] = mapped_column(Text)  # forme tifinagh validée
    translation_fr: Mapped[str | None] = mapped_column(Text)
    translation_en: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    source: Mapped[Source] = relationship()


class AccessLevel(enum.StrEnum):
    PUBLIC = "public"  # lisible par tous ; seul niveau transmis à un modèle externe
    COMMUNITY = "community"  # personnes ayant un compte
    RESTRICTED = "restricted"  # jamais servi par l'API ; accès décidé hors ligne


class Theme(enum.StrEnum):
    ORAL_HISTORY = "oral_history"
    PROVERBS = "proverbs"
    CULTURE = "culture"
    PASTORALISM = "pastoralism"
    ENVIRONMENT = "environment"
    PLANTS = "plants"
    TOPONYMY = "toponymy"
    CRAFTS = "crafts"
    INTERGENERATIONAL = "intergenerational"  # savoirs des femmes, des jeunes et des anciens
    LANGUAGE = "language"


class KnowledgeDocument(Governed, Base):
    """Document de la bibliothèque des savoirs. `body` n'est jamais modifié (contrainte en base)."""

    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    theme: Mapped[Theme] = mapped_column(_enum(Theme, "knowledge_theme"))
    access_level: Mapped[AccessLevel] = mapped_column(_enum(AccessLevel, "access_level"))
    # Nom à créditer, seulement si la personne a accepté d'être identifiée.
    author_credit: Mapped[str | None] = mapped_column(Text)

    source: Mapped[Source] = relationship()
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="KnowledgeChunk.position"
    )


class KnowledgeChunk(Base):
    """Passage d'un document, unité de recherche et de citation."""

    __tablename__ = "knowledge_chunks"
    __table_args__ = (Index("ix_knowledge_chunks_tsv", "tsv", postgresql_using="gin"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_documents.id"))
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    # Configuration « simple » : aucune racinisation ni liste de mots propre à une langue,
    # valable pour le tamasheq comme pour le français et l'anglais.
    tsv: Mapped[Any] = mapped_column(
        TSVECTOR, Computed("to_tsvector('simple'::regconfig, text)", persisted=True)
    )

    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")


class AudioRecording(Governed, Base):
    """Enregistrement vocal consenti. Trois autorisations distinctes : publication
    (`allow_publication`), entraînement de la reconnaissance vocale (`allow_training`) et
    synthèse d'une voix à partir de celle de la personne (`allow_voice_synthesis`).

    Au retrait, le fichier audio est supprimé ; ces métadonnées restent pour la trace."""

    __tablename__ = "audio_recordings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    storage_key: Mapped[str | None] = mapped_column(String(255), unique=True)
    mime_type: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[float] = mapped_column()
    sha256: Mapped[str] = mapped_column(String(64))
    # Phrase lue (collecte de type Common Voice), si l'enregistrement en lit une.
    prompt_text_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("corpus_texts.id"))
    # Transcription de référence, saisie ou corrigée par une personne.
    transcription: Mapped[str | None] = mapped_column(Text)
    allow_voice_synthesis: Mapped[bool] = mapped_column(default=False)
    file_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    source: Mapped[Source] = relationship()
    prompt: Mapped[CorpusText | None] = relationship()


class Revision(Base):
    """Journal append-only de toutes les modifications de contenu (avant / après)."""

    __tablename__ = "revisions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[uuid.UUID] = mapped_column(index=True)
    action: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    reason: Mapped[str | None] = mapped_column(Text)


class DatasetPurpose(enum.StrEnum):
    TRAINING = "training"
    PUBLICATION = "publication"


class Dataset(Base):
    """Export figé. Ses éléments sont enregistrés pour retrouver où une contribution retirée a
    été utilisée."""

    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    purpose: Mapped[DatasetPurpose] = mapped_column(_enum(DatasetPurpose, "dataset_purpose"))
    kind: Mapped[str] = mapped_column(String(32))
    criteria: Mapped[dict[str, Any]] = mapped_column(JSONB)
    file_sha256: Mapped[str] = mapped_column(String(64))
    item_count: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DatasetItem(Base):
    __tablename__ = "dataset_items"

    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), primary_key=True)
    entity: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, index=True)
