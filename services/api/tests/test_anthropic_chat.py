import asyncio
from typing import Any

import anthropic
import httpx2
import pytest
from anthropic.types.beta import BetaMessage

from app.ai.anthropic_backend import FALLBACK_BETA, AnthropicBackend
from app.ai.anthropic_chat import AnthropicChatProvider
from app.ai.chat import ChatMessage, ChatProviderError
from app.ai.prompts import CHAT_SYSTEM_PROMPT


def message(content: list[dict[str, Any]], stop_reason: str = "end_turn") -> BetaMessage:
    return BetaMessage.model_validate(
        {
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "model": "claude-opus-5-5",
            "content": content,
            "stop_reason": stop_reason,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
    )


class StubMessages:
    def __init__(self, result: BetaMessage | Exception) -> None:
        self.result = result
        self.kwargs: dict[str, Any] = {}

    async def create(self, **kwargs: Any) -> BetaMessage:
        self.kwargs = kwargs
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class StubClient:
    def __init__(self, result: BetaMessage | Exception) -> None:
        self.messages = StubMessages(result)
        self.beta = self


def provider(result: BetaMessage | Exception) -> tuple[AnthropicChatProvider, StubMessages]:
    client = StubClient(result)
    return (
        AnthropicChatProvider(
            AnthropicBackend("k", "claude-opus-5-5", "medium", client=client)  # type: ignore[arg-type]
        ),
        client.messages,
    )


def run(p: AnthropicChatProvider) -> Any:
    return asyncio.run(p.reply([ChatMessage("user", "Bonjour")]))


def test_request_shape() -> None:
    p, stub = provider(message([{"type": "text", "text": "Salut"}]))
    reply = run(p)
    assert reply.text == "Salut"
    assert reply.model == "claude-opus-5-5"
    assert not reply.truncated
    assert stub.kwargs["system"] == CHAT_SYSTEM_PROMPT
    assert stub.kwargs["output_config"] == {"effort": "medium"}
    assert stub.kwargs["fallbacks"] == "default"
    assert stub.kwargs["betas"] == [FALLBACK_BETA]
    assert stub.kwargs["messages"] == [{"role": "user", "content": "Bonjour"}]
    assert (
        "thinking" not in stub.kwargs
    )  # toujours actif sur ce modèle ; « disabled » serait une 400


def test_thinking_blocks_are_not_shown() -> None:
    p, _ = provider(
        message(
            [
                {"type": "thinking", "thinking": "", "signature": "s"},
                {"type": "text", "text": "Réponse"},
            ]
        )
    )
    assert run(p).text == "Réponse"


def test_fallback_keeps_only_the_serving_model_output() -> None:
    p, _ = provider(
        message(
            [
                {"type": "text", "text": "début abandonné"},
                {
                    "type": "fallback",
                    "from": {"model": "claude-opus-5-5"},
                    "to": {"model": "claude-opus-5"},
                    "trigger": {"type": "refusal"},
                },
                {"type": "text", "text": "réponse du repli"},
            ]
        )
    )
    reply = run(p)
    assert reply.text == "réponse du repli"
    assert reply.model == "claude-opus-5"


def test_refusal() -> None:
    p, _ = provider(message([], stop_reason="refusal"))
    with pytest.raises(ChatProviderError) as error:
        run(p)
    assert error.value.kind == "refused"


def test_truncated_reply_is_flagged() -> None:
    p, _ = provider(message([{"type": "text", "text": "coupé"}], stop_reason="max_tokens"))
    assert run(p).truncated


def _status_error(cls: type[anthropic.APIStatusError], code: int) -> anthropic.APIStatusError:
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls("erreur", response=httpx2.Response(code, request=request), body=None)


@pytest.mark.parametrize(
    ("error", "kind"),
    [
        (_status_error(anthropic.AuthenticationError, 401), "misconfigured"),
        (_status_error(anthropic.NotFoundError, 404), "misconfigured"),
        (_status_error(anthropic.RateLimitError, 429), "unavailable"),
        (_status_error(anthropic.InternalServerError, 500), "unavailable"),
    ],
)
def test_error_mapping(error: Exception, kind: str) -> None:
    p, _ = provider(error)
    with pytest.raises(ChatProviderError) as raised:
        run(p)
    assert raised.value.kind == kind
