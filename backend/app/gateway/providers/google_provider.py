"""
Google Provider - Gemini Pro, Gemini Pro Vision.
"""

import time
from typing import List

import structlog

from app.core.config import settings
from app.gateway.models import ChatMessage, GatewayResponse, MessageRole
from app.gateway.providers.base import BaseProvider

logger = structlog.get_logger(__name__)


class GoogleProvider(BaseProvider):
    """Google AI (Gemini) provider."""

    def __init__(self):
        self._configured = False

    @property
    def provider_name(self) -> str:
        return "google"

    def _configure(self):
        """Configure Google AI SDK."""
        if not self._configured:
            import google.generativeai as genai

            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self._configured = True

    async def generate(
        self,
        model: str,
        messages: List[ChatMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> GatewayResponse:
        """Generate response using Google Gemini API."""
        start = time.time()

        try:
            import google.generativeai as genai

            self._configure()

            gen_model = genai.GenerativeModel(
                model,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                ),
            )

            # Convert messages to Gemini format
            # Gemini uses a different conversation structure
            history = []
            latest_message = ""

            for msg in messages:
                if msg.role == MessageRole.USER:
                    latest_message = msg.content
                elif msg.role == MessageRole.ASSISTANT:
                    history.append(
                        {"role": "model", "parts": [msg.content]}
                    )
                # System messages are prepended to the first user message

            if history:
                chat = gen_model.start_chat(history=history)
                response = await chat.send_message_async(latest_message)
            else:
                response = await gen_model.generate_content_async(latest_message)

            latency = (time.time() - start) * 1000
            content = response.text if response.text else ""

            # Gemini token counting is approximate
            tokens_estimate = len(content.split()) + len(latest_message.split())

            return GatewayResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                tokens_input=len(latest_message.split()),
                tokens_output=len(content.split()),
                tokens_total=tokens_estimate,
                latency_ms=latency,
                finish_reason="stop",
            )

        except Exception as e:
            logger.error("Google Gemini API error", model=model, error=str(e))
            return self._format_error_response(model, e)

    async def health_check(self) -> bool:
        """Check Google AI API availability."""
        try:
            import google.generativeai as genai

            self._configure()
            model = genai.GenerativeModel("gemini-pro")
            response = await model.generate_content_async("ping")
            return True
        except Exception:
            return False
