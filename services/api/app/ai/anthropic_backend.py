"""Accès au modèle Anthropic, partagé par l'assistant, la traduction et les réponses citées.

Regroupe en un seul endroit : le repli côté serveur, la gestion des refus, la classification
des erreurs et la journalisation sans contenu.
"""

import logging
from dataclasses import dataclass
from typing import Any, Literal

import anthropic
from anthropic.types.beta import (
    BetaAssistantMessageParam,
    BetaMessage,
    BetaOutputConfigParam,
    BetaUserMessageParam,
)

from app.ai.chat import ChatMessage, ChatProviderError

logger = logging.getLogger(__name__)

# Repli côté serveur si le modèle demandé décline une requête (voir docs/decisions.md, D11).
FALLBACK_BETA = "server-side-fallback-2026-07-01"

Effort = Literal["low", "medium", "high", "xhigh", "max"]


@dataclass(frozen=True)
class Completion:
    text: str
    model: str
    truncated: bool


class AnthropicBackend:
    name = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str,
        effort: Effort,
        max_tokens: int = 16000,
        client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        self._client = client or anthropic.AsyncAnthropic(api_key=api_key, timeout=90.0)
        self._model = model
        self._effort = effort
        self._max_tokens = max_tokens

    async def complete(
        self,
        system: str,
        messages: list[ChatMessage],
        json_schema: dict[str, Any] | None = None,
    ) -> Completion:
        """Envoie la requête ; avec `json_schema`, la réponse est un JSON conforme au schéma."""
        params = [
            BetaUserMessageParam(role="user", content=m.content)
            if m.role == "user"
            else BetaAssistantMessageParam(role="assistant", content=m.content)
            for m in messages
        ]
        output_config: BetaOutputConfigParam = {"effort": self._effort}
        if json_schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": json_schema}
        try:
            response = await self._client.beta.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system,
                output_config=output_config,
                betas=[FALLBACK_BETA],
                fallbacks="default",
                messages=params,
            )
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            logger.error("Clé API Anthropic refusée (%s)", type(e).__name__)
            raise ChatProviderError("misconfigured", "credentials rejected") from e
        except (anthropic.NotFoundError, anthropic.BadRequestError) as e:
            logger.error("Requête rejetée par Anthropic : %s", e.message)
            raise ChatProviderError("misconfigured", "request rejected") from e
        except (anthropic.RateLimitError, anthropic.APIConnectionError) as e:
            raise ChatProviderError("unavailable", type(e).__name__) from e
        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                raise ChatProviderError("unavailable", f"HTTP {e.status_code}") from e
            logger.error("Erreur Anthropic HTTP %s : %s", e.status_code, e.message)
            raise ChatProviderError("misconfigured", f"HTTP {e.status_code}") from e
        return self._to_completion(response)

    def _to_completion(self, response: BetaMessage) -> Completion:
        # Journal sans contenu : identifiants et volumes uniquement.
        logger.info(
            "anthropic request_id=%s model=%s stop=%s in=%s out=%s",
            getattr(response, "_request_id", None),
            response.model,
            response.stop_reason,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        if response.stop_reason == "refusal":
            raise ChatProviderError("refused", "declined by safety classifiers")

        # En cas de repli, le texte qui précède le dernier bloc « fallback » appartient au modèle
        # qui a décliné : seule la suite constitue la réponse.
        served_model = response.model
        texts: list[str] = []
        for block in response.content:
            if block.type == "fallback":
                served_model = block.to.model
                texts = []
            elif block.type == "text":
                texts.append(block.text)

        text = "".join(texts).strip()
        if not text:
            raise ChatProviderError("unavailable", "empty reply")
        return Completion(
            text=text, model=served_model, truncated=response.stop_reason == "max_tokens"
        )
