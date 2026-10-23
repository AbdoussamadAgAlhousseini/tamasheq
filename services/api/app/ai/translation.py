"""Traduction expérimentale tamasheq ⇄ français / anglais, appuyée sur le dictionnaire validé."""

import json
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ValidationError

from app.ai.anthropic_backend import AnthropicBackend
from app.ai.chat import ChatMessage, ChatProviderError
from app.ai.prompts import TRANSLATION_SYSTEM_PROMPT
from app.services.glossary import GlossaryEntry

Lang = Literal["taq", "fr", "en"]
LANG_NAMES: dict[str, str] = {"taq": "Tamasheq", "fr": "French", "en": "English"}


@dataclass(frozen=True)
class Translation:
    translation: str
    alternatives: list[str]
    ambiguities: list[str]
    notes: str
    glossary_used: list[str]  # références G1, G2… effectivement fournies
    provider: str
    model: str
    truncated: bool


class TranslationProvider(Protocol):
    name: str

    async def translate(
        self,
        text: str,
        source: Lang,
        target: Lang,
        variant: str | None,
        glossary: list[GlossaryEntry],
    ) -> Translation: ...


class _Output(BaseModel):
    translation: str
    alternatives: list[str]
    ambiguities: list[str]
    notes: str
    glossary_used: list[str]


SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "translation": {"type": "string"},
        "alternatives": {"type": "array", "items": {"type": "string"}},
        "ambiguities": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
        "glossary_used": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["translation", "alternatives", "ambiguities", "notes", "glossary_used"],
    "additionalProperties": False,
}


def build_message(
    text: str, source: Lang, target: Lang, variant: str | None, glossary: list[GlossaryEntry]
) -> str:
    parts = [f"Translate from {LANG_NAMES[source]} to {LANG_NAMES[target]}."]
    if variant:
        parts.append(f"Requested Tamasheq variety: {variant}.")
    if glossary:
        entries = [
            {
                "ref": g.ref,
                "tamasheq": [g.headword, *g.other_forms],
                "french": g.translations_fr,
                "english": g.translations_en,
            }
            for g in glossary
        ]
        parts.append(
            "Validated glossary entries (JSON):\n" + json.dumps(entries, ensure_ascii=False)
        )
    else:
        parts.append("No validated glossary entry matches this text.")
    parts.append(f"<source_text>\n{text}\n</source_text>")
    return "\n\n".join(parts)


class AnthropicTranslationProvider:
    name = "anthropic"

    def __init__(self, backend: AnthropicBackend) -> None:
        self._backend = backend

    async def translate(
        self,
        text: str,
        source: Lang,
        target: Lang,
        variant: str | None,
        glossary: list[GlossaryEntry],
    ) -> Translation:
        message = build_message(text, source, target, variant, glossary)
        completion = await self._backend.complete(
            TRANSLATION_SYSTEM_PROMPT, [ChatMessage("user", message)], json_schema=SCHEMA
        )
        try:
            output = _Output.model_validate_json(completion.text)
        except ValidationError as e:
            raise ChatProviderError("unavailable", "invalid structured output") from e
        known = {g.ref for g in glossary}
        return Translation(
            translation=output.translation.strip(),
            alternatives=[a.strip() for a in output.alternatives if a.strip()],
            ambiguities=[a.strip() for a in output.ambiguities if a.strip()],
            notes=output.notes.strip(),
            glossary_used=[r for r in dict.fromkeys(output.glossary_used) if r in known],
            provider=self.name,
            model=completion.model,
            truncated=completion.truncated,
        )
