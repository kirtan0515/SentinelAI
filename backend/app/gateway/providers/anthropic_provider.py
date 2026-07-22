"""
Anthropic Provider - Claude 3 Opus, Sonnet, Haiku.
"""

import time
from typing import List

import structlog

from app.core.config import settings
from app.gateway.models import ChatMessage, GatewayResponse, MessageRole
from app.gateway.providers.base import BaseProvider

logger = structlog.get_logger(__name__)


class AnthropicProvider(BaseProvider):
    """Anthropic API provider supporting Claude 3 models."""

    def __init__(self):
        self._client = None

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _get_client(self):
        """Lazy-initialize the Anthropic client."""
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    async def generate(
        self,
        model: str,
        messages: List[ChatMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> GatewayResponse:
        """Generate response using Anthropic API."""
        start = time.time()

        try:
            client = self._get_client()

            # Separate system message from conversation
            system_message = None
            conversation_messages = []

            for msg in messages:
                if msg.role == MessageRole.SYSTEM:
                    system_message = msg.content
                else:
                    conversation_messages.append({"role": msg.role.value, "content": msg.content})

            # Build request kwargs
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": conversation_messages,
                "temperature": temperature,
                "top_p": top_p,
            }
            if system_message:
                kwargs["system"] = system_message

            response = await client.messages.create(**kwargs)

            latency = (time.time() - start) * 1000
            content = response.content[0].text if response.content else ""
            tokens_input = response.usage.input_tokens
            tokens_output = response.usage.output_tokens

            return GatewayResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_total=tokens_input + tokens_output,
                latency_ms=latency,
                finish_reason=response.stop_reason or "end_turn",
            )

        except Exception as e:
            logger.error("Anthropic API error", model=model, error=str(e))
            return self._format_error_response(model, e)

    async def health_check(self) -> bool:
        """Check Anthropic API availability."""
        try:
            client = self._get_client()
            response = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False
