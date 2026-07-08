"""
SentinelAI AI Gateway

Production-grade multi-model router with:
- Provider abstraction (OpenAI, Anthropic, Google, Ollama)
- Retry with exponential backoff
- Circuit breaker pattern
- Fallback model support
- Conversation history management
- Token counting and cost estimation
- Rate limiting per user/IP
"""

from app.gateway.router import GatewayRouter
from app.gateway.models import GatewayRequest, GatewayResponse, ModelInfo

__all__ = ["GatewayRouter", "GatewayRequest", "GatewayResponse", "ModelInfo"]
