"""
Guardrails Manager

Manages NeMo Guardrails configuration and execution.
Provides a clean interface for input/output rail checks.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)

# Path to guardrails config
GUARDRAILS_CONFIG_DIR = Path(__file__).parent / "config"


class GuardrailsResult:
    """Result of a guardrails check."""

    def __init__(
        self,
        allowed: bool,
        modified_text: Optional[str] = None,
        rail_triggered: Optional[str] = None,
        details: Optional[Dict] = None,
    ):
        self.allowed = allowed
        self.modified_text = modified_text
        self.rail_triggered = rail_triggered
        self.details = details or {}


class GuardrailsManager:
    """
    Manages NVIDIA NeMo Guardrails.

    Supports:
    - Input rails: Check prompts before they reach the LLM
    - Output rails: Check responses before they reach the user
    - Custom Colang rules for enterprise policies
    - Graceful fallback when NeMo is not installed
    """

    def __init__(self):
        self._rails = None
        self._enabled = False
        self._initialize()

    def _initialize(self):
        """Initialize NeMo Guardrails if available."""
        try:
            from nemoguardrails import RailsConfig, LLMRails

            config_path = str(GUARDRAILS_CONFIG_DIR)

            if os.path.exists(config_path) and os.path.exists(
                os.path.join(config_path, "config.yml")
            ):
                config = RailsConfig.from_path(config_path)
                self._rails = LLMRails(config)
                self._enabled = True
                logger.info("NeMo Guardrails initialized successfully")
            else:
                logger.info(
                    "NeMo Guardrails config not found, using built-in rules",
                    config_path=config_path,
                )
        except ImportError:
            logger.info("NeMo Guardrails not installed, using built-in security engine only")
        except Exception as e:
            logger.warning(
                "Failed to initialize NeMo Guardrails",
                error=str(e),
            )

    @property
    def is_enabled(self) -> bool:
        """Whether NeMo Guardrails is active."""
        return self._enabled

    async def check_input(self, message: str) -> GuardrailsResult:
        """
        Apply input guardrails to a user message.

        If NeMo is not available, falls back to the built-in
        security engine (which is always active regardless).
        """
        if not self._enabled:
            return GuardrailsResult(allowed=True)

        try:
            response = await self._rails.generate_async(
                messages=[{"role": "user", "content": message}]
            )

            # Check if the rail blocked the message
            content = response.get("content", "")

            # NeMo returns a refusal message if rails trigger
            blocked_indicators = [
                "I'm sorry",
                "I cannot",
                "I can't help with",
                "not able to assist",
            ]

            is_blocked = any(
                indicator.lower() in content.lower() for indicator in blocked_indicators
            )

            if is_blocked:
                return GuardrailsResult(
                    allowed=False,
                    rail_triggered="input_rail",
                    details={"nemo_response": content},
                )

            return GuardrailsResult(allowed=True)

        except Exception as e:
            logger.error("Guardrails input check failed", error=str(e))
            # Fail open - if guardrails error, allow the request
            # (security engine is the primary defense)
            return GuardrailsResult(
                allowed=True,
                details={"error": str(e), "fallback": True},
            )

    async def check_output(self, prompt: str, response: str) -> GuardrailsResult:
        """
        Apply output guardrails to an LLM response.

        Checks if the response violates any output policies.
        """
        if not self._enabled:
            return GuardrailsResult(allowed=True, modified_text=response)

        try:
            # NeMo output rails check
            result = await self._rails.generate_async(
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response},
                ]
            )

            output_content = result.get("content", response)

            return GuardrailsResult(
                allowed=True,
                modified_text=output_content,
            )

        except Exception as e:
            logger.error("Guardrails output check failed", error=str(e))
            return GuardrailsResult(
                allowed=True,
                modified_text=response,
                details={"error": str(e), "fallback": True},
            )

    async def get_status(self) -> Dict:
        """Get guardrails status and configuration."""
        return {
            "enabled": self._enabled,
            "config_path": str(GUARDRAILS_CONFIG_DIR),
            "has_config": os.path.exists(GUARDRAILS_CONFIG_DIR / "config.yml"),
        }
