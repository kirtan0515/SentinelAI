"""
Heuristic Analyzer

Applies statistical and structural heuristics to detect
suspicious patterns that don't match known attack signatures.

Checks:
- Unusual prompt length
- High entropy (possible encoded payloads)
- Excessive special characters
- Language switching (possible evasion)
- Repetitive patterns (token stuffing)
- Base64/hex encoded content
"""

import base64
import math
import re
from collections import Counter
from typing import List

from app.security.detectors.base import BaseDetector, DetectionResult


class HeuristicAnalyzer(BaseDetector):
    """
    Applies heuristic analysis to detect suspicious patterns
    that evade pattern-based detection.
    """

    def __init__(self, enabled: bool = True, length_threshold: int = 5000):
        super().__init__(enabled=enabled)
        self.length_threshold = length_threshold

    @property
    def detector_name(self) -> str:
        return "heuristic_analysis"

    async def detect(self, text: str) -> DetectionResult:
        """Run heuristic analysis on text."""
        if not self.enabled:
            return DetectionResult()

        findings: List[str] = []
        scores: List[float] = []

        # Check 1: Suspicious length
        length_score = self._check_length(text)
        if length_score > 0:
            findings.append("suspicious_length")
            scores.append(length_score)

        # Check 2: High entropy (possible encoded content)
        entropy_score = self._check_entropy(text)
        if entropy_score > 0:
            findings.append("high_entropy")
            scores.append(entropy_score)

        # Check 3: Base64 encoded content
        base64_score = self._check_base64(text)
        if base64_score > 0:
            findings.append("base64_encoded")
            scores.append(base64_score)

        # Check 4: Excessive special characters
        special_score = self._check_special_chars(text)
        if special_score > 0:
            findings.append("excessive_special_chars")
            scores.append(special_score)

        # Check 5: Repetitive patterns (token stuffing)
        repetition_score = self._check_repetition(text)
        if repetition_score > 0:
            findings.append("repetitive_patterns")
            scores.append(repetition_score)

        # Check 6: Unicode abuse / homoglyphs
        unicode_score = self._check_unicode_abuse(text)
        if unicode_score > 0:
            findings.append("unicode_abuse")
            scores.append(unicode_score)

        if not findings:
            return DetectionResult()

        # Aggregate score - average with weight toward max
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        final_score = (max_score * 0.7) + (avg_score * 0.3)
        final_score = min(final_score, 0.85)  # Heuristics cap at 0.85 (never block alone)

        threat_level = self._classify_threat_level(final_score)
        recommendation = "flag" if final_score >= 0.4 else "allow"

        return DetectionResult(
            detected=True,
            score=final_score,
            threat_type="heuristic_anomaly",
            threat_level=threat_level,
            matched_patterns=findings,
            details={
                "individual_scores": dict(zip(findings, scores)),
                "aggregation": "weighted_average",
            },
            recommendation=recommendation,
        )

    def _check_length(self, text: str) -> float:
        """Flag unusually long prompts."""
        length = len(text)
        if length < self.length_threshold:
            return 0.0
        elif length < self.length_threshold * 2:
            return 0.3
        elif length < self.length_threshold * 4:
            return 0.5
        else:
            return 0.7

    def _check_entropy(self, text: str) -> float:
        """
        Calculate Shannon entropy. High entropy suggests
        encoded/obfuscated content.
        """
        if len(text) < 50:
            return 0.0

        # Calculate character frequency
        counter = Counter(text)
        length = len(text)
        entropy = -sum((count / length) * math.log2(count / length) for count in counter.values())

        # Normal English text: ~4.0-4.5 bits/char
        # Base64: ~5.5-6.0 bits/char
        # Random: ~7.0+ bits/char
        if entropy > 6.0:
            return 0.6
        elif entropy > 5.5:
            return 0.4
        elif entropy > 5.0:
            return 0.2
        return 0.0

    def _check_base64(self, text: str) -> float:
        """Detect base64 encoded segments."""
        # Look for long base64-like strings
        b64_pattern = r"[A-Za-z0-9+/]{40,}={0,2}"
        matches = re.findall(b64_pattern, text)

        if not matches:
            return 0.0

        # Try to decode and check if it contains suspicious content
        for match in matches:
            try:
                decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
                # Check if decoded content has injection-like patterns
                suspicious_words = [
                    "ignore",
                    "system",
                    "prompt",
                    "instruction",
                    "override",
                    "bypass",
                    "jailbreak",
                    "admin",
                ]
                if any(word in decoded.lower() for word in suspicious_words):
                    return 0.7
            except Exception:
                pass

        # Even without suspicious decoded content, long base64 is suspicious
        if any(len(m) > 100 for m in matches):
            return 0.4
        return 0.2

    def _check_special_chars(self, text: str) -> float:
        """Flag excessive special characters (possible delimiter attacks)."""
        if len(text) < 10:
            return 0.0

        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        ratio = special_chars / len(text)

        if ratio > 0.5:
            return 0.5
        elif ratio > 0.35:
            return 0.3
        elif ratio > 0.25:
            return 0.1
        return 0.0

    def _check_repetition(self, text: str) -> float:
        """Detect token stuffing / repetitive patterns."""
        if len(text) < 100:
            return 0.0

        # Check for repeated phrases (possible context window stuffing)
        words = text.lower().split()
        if len(words) < 20:
            return 0.0

        # Bigram repetition
        bigrams = [f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1)]
        bigram_counts = Counter(bigrams)
        most_common_count = bigram_counts.most_common(1)[0][1] if bigrams else 0

        repetition_ratio = most_common_count / len(bigrams) if bigrams else 0

        if repetition_ratio > 0.3:
            return 0.6
        elif repetition_ratio > 0.2:
            return 0.4
        elif repetition_ratio > 0.1:
            return 0.2
        return 0.0

    def _check_unicode_abuse(self, text: str) -> float:
        """
        Detect Unicode homoglyphs and invisible characters
        used to evade text-based detection.
        """
        suspicious_ranges = [
            (0x200B, 0x200F),  # Zero-width characters
            (0x2028, 0x202F),  # Various Unicode spaces
            (0x2060, 0x2064),  # Invisible formatters
            (0xFEFF, 0xFEFF),  # BOM
            (0x0400, 0x04FF),  # Cyrillic (potential homoglyphs in English text)
        ]

        suspicious_count = 0
        for char in text:
            code = ord(char)
            for start, end in suspicious_ranges:
                if start <= code <= end:
                    suspicious_count += 1
                    break

        if suspicious_count == 0:
            return 0.0

        ratio = suspicious_count / len(text) if text else 0

        if ratio > 0.1:
            return 0.6
        elif suspicious_count > 10:
            return 0.4
        elif suspicious_count > 3:
            return 0.2
        return 0.0
