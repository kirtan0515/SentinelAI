"""
OpenAI Provider - GPT-4, GPT-3.5 Turbo, etc.
"""

import time
from typing import List

import structlog

from app.core.config import settings
from app.gateway.models import ChatMessage, GatewayResponse
from app.gateway.providers.base import BaseProvider

logger = structlog.get_logger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI API provider supporting GPT-4 and GPT-3.5."""

    def __init__(self):
        self._client = None

    @property
    def provider_name(self) -> str:
        return "openai"

    def _get_client(self):
        """Lazy-initialize the OpenAI client."""
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def generate(
        self,
        model: str,
        messages: List[ChatMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> GatewayResponse:
        """Generate response using OpenAI API."""
        start = time.time()

        try:
            client = self._get_client()

            # Convert to OpenAI message format
            openai_messages = [{"role": msg.role.value, "content": msg.content} for msg in messages]

            response = await client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )

            latency = (time.time() - start) * 1000
            content = response.choices[0].message.content or ""
            tokens_input = response.usage.prompt_tokens if response.usage else 0
            tokens_output = response.usage.completion_tokens if response.usage else 0

            return GatewayResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_total=tokens_input + tokens_output,
                latency_ms=latency,
                finish_reason=response.choices[0].finish_reason or "stop",
            )

        except Exception as e:
            logger.error("OpenAI API error", model=model, error=str(e))
            return self._format_error_response(model, e)

    async def health_check(self) -> bool:
        """Check OpenAI API availability."""
        try:
            client = self._get_client()
            # Use a minimal request to verify connectivity
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False
