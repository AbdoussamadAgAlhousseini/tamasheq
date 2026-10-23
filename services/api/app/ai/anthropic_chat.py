from app.ai.anthropic_backend import AnthropicBackend
from app.ai.chat import ChatMessage, ChatReply
from app.ai.prompts import CHAT_SYSTEM_PROMPT


class AnthropicChatProvider:
    name = "anthropic"

    def __init__(self, backend: AnthropicBackend) -> None:
        self._backend = backend

    async def reply(self, messages: list[ChatMessage]) -> ChatReply:
        completion = await self._backend.complete(CHAT_SYSTEM_PROMPT, messages)
        return ChatReply(
            text=completion.text,
            provider=self.name,
            model=completion.model,
            truncated=completion.truncated,
        )
