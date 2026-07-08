"""
Model Router - Routes requests to the appropriate LLM provider.
Supports OpenAI, Anthropic, Google Gemini, and Ollama.
"""

from typing import Optional
from uuid import UUID

from app.core.config import settings


class ModelRouter:
    """
    Routes AI requests to the correct provider based on model selection.
    Provides a unified interface regardless of the underlying LLM.
    """

    PROVIDER_MAP = {
        "gpt-4": "openai",
        "gpt-3.5-turbo": "openai",
        "gpt-4-turbo": "openai",
        "claude-3-sonnet": "anthropic",
        "claude-3-haiku": "anthropic",
        "claude-3-opus": "anthropic",
        "gemini-pro": "google",
        "gemini-pro-vision": "google",
        "llama2": "ollama",
        "mistral": "ollama",
        "codellama": "ollama",
    }

    async def route(
        self,
        model: str,
        message: str,
        session_id: Optional[UUID] = None,
    ) -> dict:
        """Route a message to the appropriate LLM provider."""
        provider = self.PROVIDER_MAP.get(model, "openai")

        if provider == "openai":
            return await self._call_openai(model, message)
        elif provider == "anthropic":
            return await self._call_anthropic(model, message)
        elif provider == "google":
            return await self._call_google(model, message)
        elif provider == "ollama":
            return await self._call_ollama(model, message)
        else:
            raise ValueError(f"Unknown provider for model: {model}")

    async def _call_openai(self, model: str, message: str) -> dict:
        """Call OpenAI API."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": message}],
                max_tokens=4096,
            )
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "model": model,
                "provider": "openai",
            }
        except Exception as e:
            return {
                "content": f"Error calling OpenAI: {str(e)}",
                "tokens_used": 0,
                "model": model,
                "provider": "openai",
                "error": True,
            }

    async def _call_anthropic(self, model: str, message: str) -> dict:
        """Call Anthropic API."""
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = await client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": message}],
            )
            return {
                "content": response.content[0].text,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "model": model,
                "provider": "anthropic",
            }
        except Exception as e:
            return {
                "content": f"Error calling Anthropic: {str(e)}",
                "tokens_used": 0,
                "model": model,
                "provider": "anthropic",
                "error": True,
            }

    async def _call_google(self, model: str, message: str) -> dict:
        """Call Google Gemini API."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.GOOGLE_API_KEY)
            gen_model = genai.GenerativeModel(model)
            response = await gen_model.generate_content_async(message)
            return {
                "content": response.text,
                "tokens_used": 0,  # Gemini doesn't always return token counts
                "model": model,
                "provider": "google",
            }
        except Exception as e:
            return {
                "content": f"Error calling Google Gemini: {str(e)}",
                "tokens_used": 0,
                "model": model,
                "provider": "google",
                "error": True,
            }

    async def _call_ollama(self, model: str, message: str) -> dict:
        """Call Ollama (local LLM) API."""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.OLLAMA_HOST}/api/generate",
                    json={"model": model, "prompt": message, "stream": False},
                    timeout=120.0,
                )
                data = response.json()
                return {
                    "content": data.get("response", ""),
                    "tokens_used": data.get("eval_count", 0),
                    "model": model,
                    "provider": "ollama",
                }
        except Exception as e:
            return {
                "content": f"Error calling Ollama: {str(e)}",
                "tokens_used": 0,
                "model": model,
                "provider": "ollama",
                "error": True,
            }
