"""Gateway router — routes requests to LLM providers with retry/fallback."""

import asyncio
import time
from typing import Dict, List, Optional

import structlog

from app.gateway.circuit_breaker import CircuitBreaker
from app.gateway.models import (
    ChatMessage,
    GatewayRequest,
    GatewayResponse,
    MessageRole,
    ModelInfo,
    Provider,
    SUPPORTED_MODELS,
)
from app.gateway.providers.anthropic_provider import AnthropicProvider
from app.gateway.providers.base import BaseProvider
from app.gateway.providers.google_provider import GoogleProvider
from app.gateway.providers.ollama_provider import OllamaProvider
from app.gateway.providers.openai_provider import OpenAIProvider

logger = structlog.get_logger(__name__)


# Default fallback chains per provider
FALLBACK_CHAINS: Dict[str, List[str]] = {
    "gpt-4": ["gpt-4-turbo", "gpt-3.5-turbo"],
    "gpt-4-turbo": ["gpt-4", "gpt-3.5-turbo"],
    "gpt-3.5-turbo": ["gpt-4-turbo"],
    "claude-3-opus": ["claude-3-sonnet", "claude-3-haiku"],
    "claude-3-sonnet": ["claude-3-haiku", "claude-3-opus"],
    "claude-3-haiku": ["claude-3-sonnet"],
    "gemini-pro": ["gpt-3.5-turbo"],
    "llama2": ["mistral", "llama3"],
    "mistral": ["llama2", "llama3"],
    "codellama": ["llama2", "mistral"],
    "llama3": ["llama2", "mistral"],
}


class GatewayRouter:
    """
    Central AI gateway router.

    Manages multiple LLM providers, handles routing decisions,
    retries, fallbacks, and cost tracking.
    """

    def __init__(self):
        # Initialize providers
        self._providers: Dict[str, BaseProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "google": GoogleProvider(),
            "ollama": OllamaProvider(),
        }

        # Circuit breaker
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
        )

        # Retry config
        self._max_retries = 3
        self._base_delay = 1.0  # seconds
        self._max_delay = 30.0

    async def route(self, request: GatewayRequest) -> GatewayResponse:
        """
        Route a request through the gateway.

        Pipeline:
        1. Resolve model to provider
        2. Check circuit breaker
        3. Attempt request with retries
        4. Fall back to alternate models if needed
        5. Calculate cost estimate
        """
        model_info = self._get_model_info(request.model)
        if not model_info:
            return GatewayResponse(
                content="",
                model=request.model,
                provider="unknown",
                error=True,
                error_message=f"Unsupported model: {request.model}. "
                f"Available: {list(SUPPORTED_MODELS.keys())}",
            )

        # Try primary model
        response = await self._attempt_with_retries(
            model=request.model,
            model_info=model_info,
            messages=request.messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
        )

        # If primary failed, try fallbacks
        if response.error:
            fallback_response = await self._try_fallbacks(
                primary_model=request.model,
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
            )
            if fallback_response and not fallback_response.error:
                fallback_response.metadata["fallback_from"] = request.model
                response = fallback_response

        # Calculate cost estimate
        if not response.error:
            response.cost_estimate = self._estimate_cost(
                model_info, response.tokens_input, response.tokens_output
            )

        return response

    async def route_simple(
        self,
        model: str,
        message: str,
        system_prompt: Optional[str] = None,
    ) -> GatewayResponse:
        """
        Simplified routing for single-message requests.
        Convenience wrapper around the full route() method.
        """
        messages = []
        if system_prompt:
            messages.append(ChatMessage(role=MessageRole.SYSTEM, content=system_prompt))
        messages.append(ChatMessage(role=MessageRole.USER, content=message))

        request = GatewayRequest(
            model=model,
            messages=messages,
        )
        return await self.route(request)

    async def _attempt_with_retries(
        self,
        model: str,
        model_info: ModelInfo,
        messages: List[ChatMessage],
        max_tokens: int,
        temperature: float,
        top_p: float,
    ) -> GatewayResponse:
        """Attempt a request with exponential backoff retries."""
        provider_name = model_info.provider.value
        provider = self._providers.get(provider_name)

        if not provider:
            return GatewayResponse(
                content="",
                model=model,
                provider=provider_name,
                error=True,
                error_message=f"Provider not configured: {provider_name}",
            )

        # Check circuit breaker
        if not self._circuit_breaker.can_execute(provider_name):
            return GatewayResponse(
                content="",
                model=model,
                provider=provider_name,
                error=True,
                error_message=f"Provider {provider_name} circuit is OPEN (too many failures)",
            )

        # Retry loop
        last_error = None
        for attempt in range(self._max_retries):
            try:
                # Use the actual model ID for the API call
                api_model_id = model_info.id

                response = await provider.generate(
                    model=api_model_id,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                )

                if not response.error:
                    self._circuit_breaker.record_success(provider_name)
                    response.model = model  # Use user-facing model name
                    return response

                last_error = response.error_message

            except Exception as e:
                last_error = str(e)

            # Wait before retry (exponential backoff)
            if attempt < self._max_retries - 1:
                delay = min(
                    self._base_delay * (2**attempt),
                    self._max_delay,
                )
                logger.warning(
                    "Gateway: retrying",
                    model=model,
                    provider=provider_name,
                    attempt=attempt + 1,
                    delay=delay,
                    error=last_error,
                )
                await asyncio.sleep(delay)

        # All retries failed
        self._circuit_breaker.record_failure(provider_name)

        return GatewayResponse(
            content="",
            model=model,
            provider=provider_name,
            error=True,
            error_message=f"All {self._max_retries} attempts failed. Last error: {last_error}",
        )

    async def _try_fallbacks(
        self,
        primary_model: str,
        messages: List[ChatMessage],
        max_tokens: int,
        temperature: float,
        top_p: float,
    ) -> Optional[GatewayResponse]:
        """Try fallback models when primary fails."""
        fallbacks = FALLBACK_CHAINS.get(primary_model, [])

        for fallback_model in fallbacks:
            model_info = self._get_model_info(fallback_model)
            if not model_info:
                continue

            # Check if fallback provider circuit is open
            provider_name = model_info.provider.value
            if not self._circuit_breaker.can_execute(provider_name):
                continue

            logger.info(
                "Gateway: trying fallback",
                primary=primary_model,
                fallback=fallback_model,
            )

            response = await self._attempt_with_retries(
                model=fallback_model,
                model_info=model_info,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )

            if not response.error:
                return response

        return None

    def _get_model_info(self, model: str) -> Optional[ModelInfo]:
        """Look up model metadata."""
        return SUPPORTED_MODELS.get(model)

    def _estimate_cost(
        self, model_info: ModelInfo, tokens_input: int, tokens_output: int
    ) -> float:
        """Estimate cost in USD for the request."""
        input_cost = (tokens_input / 1000) * model_info.cost_per_1k_input
        output_cost = (tokens_output / 1000) * model_info.cost_per_1k_output
        return round(input_cost + output_cost, 6)

    def get_available_models(self) -> List[Dict]:
        """Get list of all available models with metadata."""
        return [
            {
                "id": model_id,
                "provider": info.provider.value,
                "display_name": info.display_name,
                "max_tokens": info.max_tokens,
                "supports_vision": info.supports_vision,
                "is_local": info.is_local,
                "cost_per_1k_input": info.cost_per_1k_input,
                "cost_per_1k_output": info.cost_per_1k_output,
            }
            for model_id, info in SUPPORTED_MODELS.items()
        ]

    def get_provider_health(self) -> Dict[str, str]:
        """Get circuit breaker state for all providers."""
        states = self._circuit_breaker.get_all_states()
        result = {}
        for provider_name in self._providers:
            state = states.get(provider_name, "closed")
            result[provider_name] = state.value if hasattr(state, "value") else str(state)
        return result
