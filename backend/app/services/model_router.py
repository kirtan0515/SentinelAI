"""
Model Router - Facade for the AI Gateway.

This module provides backward compatibility while delegating
to the production gateway router under app/gateway/.
"""

from typing import Optional
from uuid import UUID

from app.gateway.models import ChatMessage, GatewayRequest, MessageRole
from app.gateway.router import GatewayRouter


class ModelRouter:
    """
    Facade that wraps the GatewayRouter for backward compatibility.

    The full gateway supports:
    - Multi-provider routing (OpenAI, Anthropic, Google, Ollama)
    - Retry with exponential backoff
    - Circuit breaker per provider
    - Automatic fallback to alternate models
    - Cost estimation
    """

    def __init__(self):
        self._gateway = GatewayRouter()

    async def route(
        self,
        model: str,
        message: str,
        session_id: Optional[UUID] = None,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[list] = None,
    ) -> dict:
        """
        Route a message to the appropriate LLM provider.

        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-sonnet")
            message: User message to send
            session_id: Optional session for conversation tracking
            system_prompt: Optional system prompt
            conversation_history: Optional previous messages

        Returns:
            Dict with content, tokens_used, model, provider, error status
        """
        # Build message list
        messages = []

        if system_prompt:
            messages.append(ChatMessage(role=MessageRole.SYSTEM, content=system_prompt))

        if conversation_history:
            for msg in conversation_history:
                role = MessageRole(msg.get("role", "user"))
                messages.append(ChatMessage(role=role, content=msg.get("content", "")))

        messages.append(ChatMessage(role=MessageRole.USER, content=message))

        # Route through gateway
        request = GatewayRequest(model=model, messages=messages)
        response = await self._gateway.route(request)

        # Convert to legacy dict format
        return {
            "content": response.content if not response.error else response.error_message,
            "tokens_used": response.tokens_total,
            "model": response.model,
            "provider": response.provider,
            "error": response.error,
            "latency_ms": response.latency_ms,
            "cost_estimate": response.cost_estimate,
            "tokens_input": response.tokens_input,
            "tokens_output": response.tokens_output,
        }

    def get_available_models(self) -> list:
        """Get list of supported models."""
        return self._gateway.get_available_models()

    def get_provider_health(self) -> dict:
        """Get health status of all providers."""
        return self._gateway.get_provider_health()
