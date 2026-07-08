"""
Base detector interface and shared detection result model.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ThreatLevel(str, Enum):
    """Severity classification for detected threats."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionResult(BaseModel):
    """
    Standardized result from any security detector.

    Attributes:
        detected: Whether a threat was identified
        score: Confidence score 0.0 (safe) to 1.0 (definite threat)
        threat_type: Category of threat detected
        threat_level: Severity classification
        matched_patterns: Which patterns triggered detection
        details: Additional context about the detection
        recommendation: Suggested action (block, flag, allow)
    """

    detected: bool = False
    score: float = Field(0.0, ge=0.0, le=1.0)
    threat_type: str = ""
    threat_level: ThreatLevel = ThreatLevel.NONE
    matched_patterns: list[str] = []
    details: dict = {}
    recommendation: str = "allow"  # allow, flag, block


class BaseDetector(ABC):
    """
    Abstract base class for all security detectors.

    Each detector:
    - Analyzes input text for a specific category of threats
    - Returns a standardized DetectionResult
    - Is independently configurable
    - Can be enabled/disabled at runtime
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    @abstractmethod
    async def detect(self, text: str) -> DetectionResult:
        """
        Analyze text for threats.

        Args:
            text: The prompt or response text to analyze.

        Returns:
            DetectionResult with threat assessment.
        """
        pass

    @property
    @abstractmethod
    def detector_name(self) -> str:
        """Unique name for this detector."""
        pass

    def _classify_threat_level(self, score: float) -> ThreatLevel:
        """Map a score to a threat level."""
        if score <= 0.0:
            return ThreatLevel.NONE
        elif score <= 0.3:
            return ThreatLevel.LOW
        elif score <= 0.6:
            return ThreatLevel.MEDIUM
        elif score <= 0.85:
            return ThreatLevel.HIGH
        else:
            return ThreatLevel.CRITICAL

    def _recommend_action(self, score: float, block_threshold: float = 0.7) -> str:
        """Determine recommended action based on score."""
        if score >= block_threshold:
            return "block"
        elif score >= 0.4:
            return "flag"
        return "allow"
