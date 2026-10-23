"""Réponses fondées sur les passages de la bibliothèque des savoirs, avec citations."""

from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError

from app.ai.anthropic_backend import AnthropicBackend
from app.ai.chat import ChatMessage, ChatProviderError
from app.ai.prompts import KNOWLEDGE_SYSTEM_PROMPT


@dataclass(frozen=True)
class Passage:
    ref: str  # P1, P2…
    title: str
    text: str


@dataclass(frozen=True)
class Answer:
    text: str
    cited: list[str]
    insufficient: bool
    provider: str
    model: str
    truncated: bool


class AnswerProvider(Protocol):
    name: str

    async def answer(self, question: str, passages: list[Passage]) -> Answer: ...


class _Output(BaseModel):
    answer: str
    citations: list[str]
    insufficient_documentation: bool


def _escape(text: str) -> str:
    # Empêche un passage de fermer la balise qui l'encadre.
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_message(question: str, passages: list[Passage]) -> str:
    blocks = "\n".join(
        f'<passage id="{p.ref}" title="{_escape(p.title)}">\n{_escape(p.text)}\n</passage>'
        for p in passages
    )
    return f"<documents>\n{blocks}\n</documents>\n\n<question>\n{_escape(question)}\n</question>"


def schema(refs: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "citations": {"type": "array", "items": {"type": "string", "enum": refs}},
            "insufficient_documentation": {"type": "boolean"},
        },
        "required": ["answer", "citations", "insufficient_documentation"],
        "additionalProperties": False,
    }


class AnthropicAnswerProvider:
    name = "anthropic"

    def __init__(self, backend: AnthropicBackend) -> None:
        self._backend = backend

    async def answer(self, question: str, passages: list[Passage]) -> Answer:
        refs = [p.ref for p in passages]
        completion = await self._backend.complete(
            KNOWLEDGE_SYSTEM_PROMPT,
            [ChatMessage("user", build_message(question, passages))],
            json_schema=schema(refs),
        )
        try:
            output = _Output.model_validate_json(completion.text)
        except ValidationError as e:
            raise ChatProviderError("unavailable", "invalid structured output") from e
        return Answer(
            text=output.answer.strip(),
            cited=[r for r in dict.fromkeys(output.citations) if r in refs],
            insufficient=output.insufficient_documentation,
            provider=self.name,
            model=completion.model,
            truncated=completion.truncated,
        )
