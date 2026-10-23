import logging
from typing import Literal

import anthropic
from anthropic.types.beta import BetaAssistantMessageParam, BetaMessage, BetaUserMessageParam

from app.ai.chat import ChatMessage, ChatProviderError, ChatReply
from app.ai.prompts import CHAT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Repli côté serveur si le modèle demandé décline une requête (voir docs/decisions.md, D6).
FALLBACK_BETA = "server-side-fallback-2026-07-01"

Effort = Literal["low", "medium", "high", "xhigh", "max"]


class AnthropicChatProvider:
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

    async def reply(self, messages: list[ChatMessage]) -> ChatReply:
        params = [
            BetaUserMessageParam(role="user", content=m.content)
            if m.role == "user"
            else BetaAssistantMessageParam(role="assistant", content=m.content)
            for m in messages
        ]
        try:
            response = await self._client.beta.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=CHAT_SYSTEM_PROMPT,
                output_config={"effort": self._effort},
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

        return self._to_reply(response)

    def _to_reply(self, response: BetaMessage) -> ChatReply:
        # Journal sans contenu de conversation : identifiants et volumes uniquement.
        logger.info(
            "chat request_id=%s model=%s stop=%s in=%s out=%s",
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
        return ChatReply(
            text=text,
            provider=self.name,
            model=served_model,
            truncated=response.stop_reason == "max_tokens",
        )
