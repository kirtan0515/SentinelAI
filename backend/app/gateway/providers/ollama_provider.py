"""
Ollama Provider - Local LLM inference (Llama 2, Mistral, CodeLlama, etc.)
"""

import time
from typing import List

import httpx
import structlog

from app.core.config import settings
from app.gateway.models import ChatMessage, GatewayResponse
from app.gateway.providers.base import BaseProvider

logger = structlog.get_logger(__name__)


class OllamaProvider(BaseProvider):
    """
    Ollama local LLM provider.

    Connects to a local or network Ollama instance for
    privacy-focused, on-premises AI inference.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.timeout = 120.0

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def generate(
        self,
        model: str,
        messages: List[ChatMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> GatewayResponse:
        """Generate response using Ollama API."""
        start = time.time()

        try:
            # Format messages for Ollama chat API
            ollama_messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ]

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": ollama_messages,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": temperature,
                            "top_p": top_p,
                        },
                    },
                    timeout=self.timeout,
                )

                if response.status_code != 200:
                    raise Exception(
                        f"Ollama returned status {response.status_code}: {response.text}"
                    )

                data = response.json()

            latency = (time.time() - start) * 1000
            content = data.get("message", {}).get("content", "")
            tokens_input = data.get("prompt_eval_count", 0)
            tokens_output = data.get("eval_count", 0)

            return GatewayResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_total=tokens_input + tokens_output,
                latency_ms=latency,
                finish_reason="stop",
                metadata={"eval_duration_ns": str(data.get("eval_duration", 0))},
            )

        except Exception as e:
            logger.error("Ollama API error", model=model, error=str(e))
            return self._format_error_response(model, e)

    async def health_check(self) -> bool:
        """Check Ollama API availability."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0,
                )
                return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """List available models on the Ollama instance."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []
