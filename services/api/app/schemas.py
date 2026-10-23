"""Schémas d'entrée communs à l'API et aux imports : une donnée importée passe exactement par
les mêmes contrôles qu'une donnée saisie."""

import unicodedata
from datetime import date
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import AccessLevel, Script, Theme
from app.text import detect_script, normalize

Text = Field(min_length=1, max_length=2000)


def checked(value: str, script: Script | None, what: str) -> tuple[str, Script]:
    """Normalise (NFC, espaces) et vérifie que le texte est entièrement dans une écriture."""
    text = normalize(value)
    if not text:
        raise ValueError(f"{what} : texte vide")
    detected = detect_script(text)
    if detected not in ("Latn", "Tfng"):
        raise ValueError(
            f"{what} : écriture {detected!r} ; attendu latin ou tifinagh, pas un mélange"
        )
    if script is not None and script.value != detected:
        raise ValueError(f"{what} : écriture déclarée {script.value}, détectée {detected}")
    return text, Script(detected)


def resolved(script: Script | None) -> Script:
    """Écriture après validation (toujours renseignée par les validateurs ci-dessous)."""
    if script is None:
        raise RuntimeError("écriture non résolue : objet non validé")
    return script


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Rights(Strict):
    """Droits et consentement : publication et entraînement sont deux choix explicites."""

    license: str = Field(min_length=1, max_length=500)
    allow_publication: bool
    allow_training: bool
    consent_reference: str | None = Field(default=None, max_length=500)
    distribution_restrictions: str | None = Field(default=None, max_length=2000)
    collected_on: date | None = None
    variant: str | None = Field(default=None, max_length=200)
    language: str = Field(default="taq", pattern=r"^[a-z]{3}$")


class SpellingIn(Strict):
    form: str = Text
    script: Script | None = None

    @model_validator(mode="after")
    def check(self) -> Self:
        self.form, self.script = checked(self.form, self.script, "graphie")
        return self


class ExampleIn(Strict):
    text: str = Text
    script: Script | None = None
    translation_fr: str | None = Field(default=None, max_length=2000)
    translation_en: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def check(self) -> Self:
        self.text, self.script = checked(self.text, self.script, "exemple")
        return self


class SenseIn(Strict):
    definition_fr: str | None = Field(default=None, max_length=4000)
    definition_en: str | None = Field(default=None, max_length=4000)
    translation_fr: str | None = Field(default=None, max_length=500)
    translation_en: str | None = Field(default=None, max_length=500)
    examples: list[ExampleIn] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def not_empty(self) -> Self:
        if not any(
            (self.definition_fr, self.definition_en, self.translation_fr, self.translation_en)
        ):
            raise ValueError("un sens doit avoir au moins une définition ou une traduction")
        return self


class LexicalEntryIn(Rights):
    headword: str = Field(min_length=1, max_length=200)
    script: Script | None = None
    part_of_speech: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=4000)
    spellings: list[SpellingIn] = Field(default_factory=list, max_length=20)
    senses: list[SenseIn] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def check(self) -> Self:
        self.headword, self.script = checked(self.headword, self.script, "entrée")
        return self


class CorpusTextIn(Rights):
    text: str = Field(min_length=1, max_length=10000)
    script: Script | None = None
    tifinagh_text: str | None = Field(default=None, max_length=10000)
    translation_fr: str | None = Field(default=None, max_length=10000)
    translation_en: str | None = Field(default=None, max_length=10000)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("tifinagh_text")
    @classmethod
    def tifinagh_only(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text, script = checked(value, Script.TFNG, "forme tifinagh")
        return text

    @model_validator(mode="after")
    def check(self) -> Self:
        self.text, self.script = checked(self.text, self.script, "texte")
        return self


class KnowledgeDocumentIn(Rights):
    title: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1, max_length=200_000)
    theme: Theme
    access_level: AccessLevel
    author_credit: str | None = Field(default=None, max_length=300)
    language: str = Field(default="fra", pattern=r"^[a-z]{3}$")

    @model_validator(mode="after")
    def normalized(self) -> Self:
        # Seuls la composition Unicode et les fins de ligne sont normalisées : les paragraphes
        # sont conservés pour le découpage en passages.
        self.title = normalize(self.title)
        self.body = unicodedata.normalize("NFC", self.body.replace("\r\n", "\n")).strip()
        return self
