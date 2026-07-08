"""
Base Provider interface.

All LLM providers implement this abstract class to ensure
a consistent interface for the gateway router.
"""

from abc import ABC, abstractmethod
from typing import List

from app.gateway.models import ChatMessage, GatewayResponse


class BaseProvider(ABC):
    """
    Abstract base class for LLM providers.

    Each provider must implement:
    - generate(): Send messages and get a response
    - health_check(): Verify provider availability
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider."""
        pass

    @abstractmethod
    async def generate(
        self,
        model: str,
        messages: List[ChatMessage],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> GatewayResponse:
        """
        Generate a response from the LLM.

        Args:
            model: Model identifier (provider-specific)
            messages: Conversation history
            max_tokens: Maximum response tokens
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter

        Returns:
            GatewayResponse with content and metadata
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is available.

        Returns:
            True if provider is reachable and operational
        """
        pass

    def _format_error_response(
        self, model: str, error: Exception
    ) -> GatewayResponse:
        """Create a standardized error response."""
        return GatewayResponse(
            content="",
            model=model,
            provider=self.provider_name,
            error=True,
            error_message=str(error),
        )
