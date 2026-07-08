"""
Security Service - Facade for the security engine.

This service provides the high-level interface used by API endpoints.
It delegates to the modular security engine under app/security/.
"""

from typing import Optional

from app.schemas.chat import SecurityCheckResult
from app.security.config import SecurityConfig
from app.security.engine import SecurityEngine
from app.security.filters.response_filter import ResponseFilter
from app.security.scoring import SecurityVerdict


class SecurityService:
    """
    High-level security service consumed by the API layer.

    Provides:
    - Prompt analysis (input filtering)
    - Response filtering (output filtering)
    - Data masking
    - Security configuration management
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.engine = SecurityEngine(self.config)
        self.response_filter = ResponseFilter(self.config.response_filter)

    async def analyze_prompt(self, prompt: str) -> SecurityCheckResult:
        """
        Analyze a prompt for security threats.

        This is the primary entry point for input security checks.
        Returns the simplified SecurityCheckResult for API compatibility.
        """
        verdict = await self.engine.analyze(prompt)
        return self._verdict_to_check_result(verdict)

    async def get_full_analysis(self, prompt: str) -> SecurityVerdict:
        """
        Get detailed security analysis (for internal/admin use).

        Returns the full SecurityVerdict with detector-level details.
        """
        return await self.engine.analyze(prompt)

    async def filter_response(self, response: str) -> tuple[str, dict]:
        """
        Filter an LLM response before returning to the user.

        Returns:
            Tuple of (filtered_text, metadata)
        """
        return await self.response_filter.filter_response(response)

    def mask_sensitive_data(self, text: str) -> str:
        """
        Mask sensitive data in text before sending to LLM.

        Returns the masked text with PII/credentials replaced.
        """
        masked_text, _ = self.engine.mask_sensitive_data(text)
        return masked_text

    def mask_sensitive_data_detailed(self, text: str) -> tuple[str, dict]:
        """
        Mask sensitive data with detailed report of what was masked.

        Returns:
            Tuple of (masked_text, mask_counts)
        """
        return self.engine.mask_sensitive_data(text)

    def _verdict_to_check_result(self, verdict: SecurityVerdict) -> SecurityCheckResult:
        """Convert internal SecurityVerdict to API-facing SecurityCheckResult."""
        return SecurityCheckResult(
            is_safe=not verdict.should_block,
            score=verdict.final_score,
            threats_detected=verdict.threats_detected,
            details={
                "action": verdict.action,
                "threat_level": verdict.threat_level.value,
                "primary_threat": verdict.primary_threat,
                "detectors_triggered": verdict.detectors_triggered,
                "analysis_time_ms": round(verdict.analysis_time_ms, 2),
                "should_mask": verdict.should_mask,
            },
        )
