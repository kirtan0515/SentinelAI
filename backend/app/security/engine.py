"""
SentinelAI Security Engine - orchestrates all detectors and produces a verdict.
"""

import re
import time
from typing import Optional

import structlog

from app.security.config import SecurityConfig
from app.security.detectors.base import DetectionResult, ThreatLevel
from app.security.detectors.heuristics import HeuristicAnalyzer
from app.security.detectors.injection import PromptInjectionDetector
from app.security.detectors.jailbreak import JailbreakDetector
from app.security.detectors.sensitive_data import SensitiveDataDetector
from app.security.scoring import SecurityVerdict, SecurityScorer

logger = structlog.get_logger(__name__)


class SecurityEngine:
    """
    Central security analysis engine.

    Orchestrates all security detectors, aggregates results,
    and produces a final security verdict.

    Usage:
        engine = SecurityEngine()
        verdict = await engine.analyze(prompt_text)
        if verdict.should_block:
            # Block the request
        elif verdict.should_mask:
            masked_text = engine.mask_sensitive_data(prompt_text)
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()

        # Initialize detectors
        self.injection_detector = PromptInjectionDetector(self.config.injection)
        self.jailbreak_detector = JailbreakDetector(self.config.jailbreak)
        self.sensitive_data_detector = SensitiveDataDetector(self.config.sensitive_data)
        self.heuristic_analyzer = HeuristicAnalyzer(
            enabled=self.config.enable_heuristics,
            length_threshold=self.config.suspicious_length_threshold,
        )

        # Initialize scorer
        self.scorer = SecurityScorer(self.config)

    async def analyze(self, text: str) -> SecurityVerdict:
        """
        Run full security analysis pipeline on input text.

        Steps:
        1. Run all detectors in parallel
        2. Aggregate results with weighted scoring
        3. Determine final verdict (allow/flag/mask/block)
        4. Log the analysis

        Args:
            text: Input prompt text to analyze.

        Returns:
            SecurityVerdict with complete analysis results.
        """
        start_time = time.time()

        # Run all detectors
        injection_result = await self.injection_detector.detect(text)
        jailbreak_result = await self.jailbreak_detector.detect(text)
        sensitive_data_result = await self.sensitive_data_detector.detect(text)
        heuristic_result = await self.heuristic_analyzer.detect(text)

        # Aggregate into final verdict
        verdict = self.scorer.calculate_verdict(
            injection=injection_result,
            jailbreak=jailbreak_result,
            sensitive_data=sensitive_data_result,
            heuristic=heuristic_result,
        )

        # Add timing
        analysis_time_ms = (time.time() - start_time) * 1000
        verdict.analysis_time_ms = analysis_time_ms

        # Log the analysis
        log_data = {
            "final_score": verdict.final_score,
            "action": verdict.action,
            "threats": verdict.threats_detected,
            "analysis_time_ms": round(analysis_time_ms, 2),
        }

        if verdict.should_block:
            logger.warning("Security: Request BLOCKED", **log_data)
        elif verdict.threats_detected:
            logger.info("Security: Threats detected", **log_data)

        return verdict

    def mask_sensitive_data(self, text: str) -> tuple[str, dict]:
        """
        Mask sensitive data in text before sending to LLM.

        Returns:
            Tuple of (masked_text, mask_summary)
        """
        return self.sensitive_data_detector.mask(text)

    async def analyze_response(self, response: str) -> SecurityVerdict:
        """
        Analyze LLM response for leaked sensitive data or
        system prompt information.

        This is the OUTPUT filter - checks model responses
        before returning to users.
        """
        if not self.config.response_filter.enabled:
            return SecurityVerdict(
                final_score=0.0,
                action="allow",
                should_block=False,
            )

        # Check for sensitive data in response
        sensitive_result = await self.sensitive_data_detector.detect(response)

        # Check for system prompt leakage patterns
        leak_result = await self._check_system_prompt_leak(response)

        # Build response verdict
        results = [sensitive_result]
        if leak_result.detected:
            results.append(leak_result)

        max_score = max(r.score for r in results) if results else 0.0

        should_block = max_score >= self.config.global_block_threshold
        should_mask = (
            sensitive_result.detected and self.config.response_filter.filter_pii_in_response
        )

        threats = []
        if sensitive_result.detected:
            threats.append("response_contains_pii")
        if leak_result.detected:
            threats.append("system_prompt_leak")

        return SecurityVerdict(
            final_score=max_score,
            action="block" if should_block else ("mask" if should_mask else "allow"),
            should_block=should_block,
            should_mask=should_mask,
            threats_detected=threats,
            detector_results={
                "sensitive_data": sensitive_result,
                "system_prompt_leak": leak_result,
            },
        )

    async def _check_system_prompt_leak(self, response: str) -> DetectionResult:
        """Check if LLM response leaks system prompt information."""
        if not self.config.response_filter.filter_system_prompt_leak:
            return DetectionResult()

        response_lower = response.lower()

        leak_patterns = [
            r"(?:my|the)\s+system\s+prompt\s+(?:is|says|reads|contains|states)",
            r"(?:i\s+was|i'm)\s+(?:instructed|told|programmed|configured)\s+to",
            r"(?:here\s+(?:is|are)|these\s+are)\s+my\s+(?:instructions|rules|guidelines|directives)",
            r"my\s+(?:original|initial|system)\s+(?:instructions?|prompt|configuration)",
            r"i\s+(?:cannot|can't|am\s+not\s+able\s+to)\s+(?:reveal|share|show)\s+my\s+(?:system|original)",
        ]

        matched = []
        for pattern in leak_patterns:
            if re.search(pattern, response_lower):
                matched.append(pattern)

        if not matched:
            return DetectionResult()

        return DetectionResult(
            detected=True,
            score=0.7,
            threat_type="system_prompt_leak",
            threat_level=ThreatLevel.HIGH,
            matched_patterns=matched,
            recommendation="flag",
        )
