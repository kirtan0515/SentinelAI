"""
Security Scoring System

Aggregates results from multiple detectors into a unified
security score and action recommendation.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.security.config import SecurityConfig
from app.security.detectors.base import DetectionResult, ThreatLevel


class SecurityVerdict(BaseModel):
    """
    Final security verdict after analyzing a prompt.

    This is the primary output of the security engine,
    consumed by the API layer to determine request handling.
    """

    # Core verdict
    final_score: float = Field(0.0, ge=0.0, le=1.0, description="Composite security score")
    action: str = Field("allow", description="Recommended action: allow, flag, mask, block")
    should_block: bool = Field(False, description="Whether the request should be blocked")
    should_mask: bool = Field(False, description="Whether sensitive data should be masked")

    # Threat details
    threat_level: ThreatLevel = ThreatLevel.NONE
    threats_detected: List[str] = []
    primary_threat: Optional[str] = None

    # Detailed results from each detector
    detector_results: Dict[str, DetectionResult] = {}

    # Metadata
    analysis_time_ms: float = 0.0
    detectors_triggered: List[str] = []

    class Config:
        arbitrary_types_allowed = True


class SecurityScorer:
    """
    Calculates final security verdicts from individual detector results.

    Scoring strategy:
    - Weighted maximum: Each detector contributes based on its configured weight
    - Compounding: Multiple threats increase the final score
    - Thresholds: Global block/flag thresholds determine the action
    """

    def __init__(self, config: SecurityConfig):
        self.config = config

    def calculate_verdict(
        self,
        injection: DetectionResult,
        jailbreak: DetectionResult,
        sensitive_data: DetectionResult,
        heuristic: DetectionResult,
    ) -> SecurityVerdict:
        """
        Calculate final security verdict from detector results.

        Scoring algorithm:
        1. Apply weight to each detector's score
        2. Take the maximum weighted score as the base
        3. Add compounding bonus for multiple detections
        4. Apply global thresholds for action determination
        """
        # Apply weights
        weighted_scores = {
            "injection": injection.score * self.config.injection_weight,
            "jailbreak": jailbreak.score * self.config.jailbreak_weight,
            "sensitive_data": sensitive_data.score * self.config.sensitive_data_weight,
            "heuristic": heuristic.score * 0.5,  # Heuristics are supplementary
        }

        # Base score = max of weighted scores
        max_score = max(weighted_scores.values())

        # Compounding: additional detections increase score
        active_detectors = sum(
            1 for s in weighted_scores.values() if s > 0.1
        )
        compounding_bonus = (active_detectors - 1) * 0.05 if active_detectors > 1 else 0

        final_score = min(max_score + compounding_bonus, 1.0)

        # Determine action
        action = self._determine_action(
            final_score, injection, jailbreak, sensitive_data
        )
        should_block = action == "block"
        should_mask = action == "mask"

        # Collect threats
        threats: List[str] = []
        detectors_triggered: List[str] = []

        if injection.detected:
            threats.append("prompt_injection")
            detectors_triggered.append("injection")
        if jailbreak.detected:
            threats.append("jailbreak")
            detectors_triggered.append("jailbreak")
        if sensitive_data.detected:
            threats.append("sensitive_data")
            detectors_triggered.append("sensitive_data")
        if heuristic.detected:
            threats.append("heuristic_anomaly")
            detectors_triggered.append("heuristic")

        # Primary threat = highest scoring
        primary_threat = None
        if threats:
            score_map = {
                "prompt_injection": weighted_scores["injection"],
                "jailbreak": weighted_scores["jailbreak"],
                "sensitive_data": weighted_scores["sensitive_data"],
                "heuristic_anomaly": weighted_scores["heuristic"],
            }
            primary_threat = max(
                (t for t in threats if t in score_map),
                key=lambda t: score_map.get(t, 0),
                default=threats[0],
            )

        # Threat level
        threat_level = self._classify_threat_level(final_score)

        return SecurityVerdict(
            final_score=round(final_score, 4),
            action=action,
            should_block=should_block,
            should_mask=should_mask,
            threat_level=threat_level,
            threats_detected=threats,
            primary_threat=primary_threat,
            detector_results={
                "injection": injection,
                "jailbreak": jailbreak,
                "sensitive_data": sensitive_data,
                "heuristic": heuristic,
            },
            detectors_triggered=detectors_triggered,
        )

    def _determine_action(
        self,
        score: float,
        injection: DetectionResult,
        jailbreak: DetectionResult,
        sensitive_data: DetectionResult,
    ) -> str:
        """
        Determine the recommended action based on score and context.

        Priority:
        1. Block: Score above threshold, or injection/jailbreak above their thresholds
        2. Mask: Sensitive data detected with masking enabled
        3. Flag: Score above flag threshold
        4. Allow: Everything else
        """
        # Direct blocks for injection or jailbreak above their thresholds
        if injection.score >= self.config.injection.block_threshold:
            return "block"
        if jailbreak.score >= self.config.jailbreak.block_threshold:
            return "block"

        # Global block threshold
        if score >= self.config.global_block_threshold:
            return "block"

        # Sensitive data masking
        if sensitive_data.detected and self.config.sensitive_data.mask_before_llm:
            if sensitive_data.recommendation == "block":
                return "block"
            return "mask"

        # Flag threshold
        if score >= self.config.global_flag_threshold:
            return "flag"

        return "allow"

    def _classify_threat_level(self, score: float) -> ThreatLevel:
        """Map final score to threat level."""
        if score <= 0.0:
            return ThreatLevel.NONE
        elif score <= 0.3:
            return ThreatLevel.LOW
        elif score <= 0.5:
            return ThreatLevel.MEDIUM
        elif score <= 0.7:
            return ThreatLevel.HIGH
        else:
            return ThreatLevel.CRITICAL
