"""
Gateway data models.

Defines the unified request/response format for the AI gateway,
provider configurations, and model metadata.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Provider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"


class MessageRole(str, Enum):
    """Chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Single message in a conversation."""

    role: MessageRole
    content: str


class ModelInfo(BaseModel):
    """Metadata about a supported model."""

    id: str
    provider: Provider
    display_name: str
    max_tokens: int = 4096
    max_context_window: int = 128000
    supports_vision: bool = False
    supports_streaming: bool = True
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    is_local: bool = False


class GatewayRequest(BaseModel):
    """Unified request to the AI gateway."""

    model: str
    messages: List[ChatMessage]
    max_tokens: int = Field(4096, ge=1, le=128000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    stream: bool = False
    user_id: Optional[str] = None
    metadata: Dict[str, str] = {}


class GatewayResponse(BaseModel):
    """Unified response from the AI gateway."""

    content: str
    model: str
    provider: str
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    latency_ms: float = 0.0
    cost_estimate: float = 0.0
    finish_reason: str = "stop"
    error: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, str] = {}


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class ProviderHealth(BaseModel):
    """Health status of a provider."""

    provider: Provider
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None
    avg_latency_ms: float = 0.0


# === Model Registry ===

SUPPORTED_MODELS: Dict[str, ModelInfo] = {
    # OpenAI
    "gpt-4": ModelInfo(
        id="gpt-4",
        provider=Provider.OPENAI,
        display_name="GPT-4",
        max_tokens=8192,
        max_context_window=128000,
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06,
    ),
    "gpt-4-turbo": ModelInfo(
        id="gpt-4-turbo",
        provider=Provider.OPENAI,
        display_name="GPT-4 Turbo",
        max_tokens=4096,
        max_context_window=128000,
        supports_vision=True,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
    ),
    "gpt-3.5-turbo": ModelInfo(
        id="gpt-3.5-turbo",
        provider=Provider.OPENAI,
        display_name="GPT-3.5 Turbo",
        max_tokens=4096,
        max_context_window=16385,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015,
    ),
    # Anthropic
    "claude-3-opus": ModelInfo(
        id="claude-3-opus-20240229",
        provider=Provider.ANTHROPIC,
        display_name="Claude 3 Opus",
        max_tokens=4096,
        max_context_window=200000,
        supports_vision=True,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
    ),
    "claude-3-sonnet": ModelInfo(
        id="claude-3-sonnet-20240229",
        provider=Provider.ANTHROPIC,
        display_name="Claude 3 Sonnet",
        max_tokens=4096,
        max_context_window=200000,
        supports_vision=True,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
    ),
    "claude-3-haiku": ModelInfo(
        id="claude-3-haiku-20240307",
        provider=Provider.ANTHROPIC,
        display_name="Claude 3 Haiku",
        max_tokens=4096,
        max_context_window=200000,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
    ),
    # Google
    "gemini-pro": ModelInfo(
        id="gemini-pro",
        provider=Provider.GOOGLE,
        display_name="Gemini Pro",
        max_tokens=8192,
        max_context_window=32000,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.0005,
    ),
    "gemini-pro-vision": ModelInfo(
        id="gemini-pro-vision",
        provider=Provider.GOOGLE,
        display_name="Gemini Pro Vision",
        max_tokens=4096,
        max_context_window=16000,
        supports_vision=True,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.0005,
    ),
    # Ollama (Local)
    "llama2": ModelInfo(
        id="llama2",
        provider=Provider.OLLAMA,
        display_name="Llama 2",
        max_tokens=4096,
        max_context_window=4096,
        is_local=True,
    ),
    "mistral": ModelInfo(
        id="mistral",
        provider=Provider.OLLAMA,
        display_name="Mistral 7B",
        max_tokens=4096,
        max_context_window=8192,
        is_local=True,
    ),
    "codellama": ModelInfo(
        id="codellama",
        provider=Provider.OLLAMA,
        display_name="Code Llama",
        max_tokens=4096,
        max_context_window=16384,
        is_local=True,
    ),
    "llama3": ModelInfo(
        id="llama3",
        provider=Provider.OLLAMA,
        display_name="Llama 3",
        max_tokens=4096,
        max_context_window=8192,
        is_local=True,
    ),
}
