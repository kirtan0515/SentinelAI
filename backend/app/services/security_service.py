"""
Security Service - Core security engine for prompt analysis.
Detects prompt injection, jailbreak attempts, and sensitive data.
"""

import re
from typing import List

from app.schemas.chat import SecurityCheckResult


class SecurityService:
    """
    Analyzes prompts for security threats before they reach LLMs.

    Detection categories:
    - Prompt injection
    - Jailbreak attempts
    - Sensitive data (PII, API keys, credentials)
    """

    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"ignore\s+(all\s+)?above\s+instructions",
        r"disregard\s+(all\s+)?previous",
        r"forget\s+(all\s+)?previous",
        r"override\s+(all\s+)?previous",
        r"new\s+instructions?\s*:",
        r"system\s*prompt\s*:",
        r"reveal\s+(your\s+)?system\s+prompt",
        r"print\s+(your\s+)?system\s+prompt",
        r"show\s+(me\s+)?(your\s+)?instructions",
        r"what\s+are\s+your\s+instructions",
        r"print\s+(your\s+)?api\s+key",
        r"reveal\s+(your\s+)?api\s+key",
        r"developer\s+mode\s+(enabled|on|activate)",
        r"act\s+as\s+.*\s+without\s+(any\s+)?restrictions",
        r"you\s+are\s+now\s+(?:a\s+)?(?:unrestricted|unfiltered)",
    ]

    # Jailbreak patterns
    JAILBREAK_PATTERNS = [
        r"do\s+anything\s+now",
        r"dan\s+mode",
        r"jailbreak",
        r"pretend\s+you\s+(?:are|have)\s+no\s+(?:rules|restrictions|guidelines)",
        r"bypass\s+(?:your\s+)?(?:filters?|restrictions?|safety)",
        r"ignore\s+(?:your\s+)?(?:safety|ethical)\s+(?:guidelines?|rules?)",
        r"hypothetically\s+.*\s+if\s+you\s+had\s+no\s+restrictions",
        r"roleplay\s+as\s+.*\s+(?:evil|unrestricted|without\s+rules)",
        r"in\s+(?:a\s+)?fictional\s+(?:world|scenario)\s+where\s+(?:there\s+are\s+)?no\s+rules",
    ]

    # Sensitive data patterns
    PII_PATTERNS = {
        "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "api_key": r"\b(?:sk-|ak-|key-)[a-zA-Z0-9]{20,}\b",
        "password": r"(?:password|passwd|pwd)\s*[:=]\s*\S+",
        "aws_key": r"\bAKIA[0-9A-Z]{16}\b",
        "private_key": r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----",
    }

    async def analyze_prompt(self, prompt: str) -> SecurityCheckResult:
        """
        Analyze a prompt for security threats.

        Returns a SecurityCheckResult with safety determination,
        threat score, and detected threats.
        """
        threats: List[str] = []
        max_score = 0.0

        # Check for prompt injection
        injection_score = self._check_injection(prompt)
        if injection_score > 0:
            threats.append("prompt_injection")
            max_score = max(max_score, injection_score)

        # Check for jailbreak attempts
        jailbreak_score = self._check_jailbreak(prompt)
        if jailbreak_score > 0:
            threats.append("jailbreak_attempt")
            max_score = max(max_score, jailbreak_score)

        # Check for sensitive data
        pii_types = self._check_sensitive_data(prompt)
        if pii_types:
            threats.append("sensitive_data_detected")
            threats.extend([f"pii:{t}" for t in pii_types])
            max_score = max(max_score, 0.6)

        # Determine if safe (score below threshold)
        is_safe = max_score < 0.7

        return SecurityCheckResult(
            is_safe=is_safe,
            score=max_score,
            threats_detected=threats,
            details={
                "injection_score": injection_score,
                "jailbreak_score": jailbreak_score,
                "pii_detected": pii_types,
            },
        )

    def _check_injection(self, prompt: str) -> float:
        """Check for prompt injection patterns."""
        prompt_lower = prompt.lower()
        matches = 0

        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, prompt_lower):
                matches += 1

        if matches == 0:
            return 0.0
        elif matches == 1:
            return 0.7
        else:
            return min(0.95, 0.7 + (matches - 1) * 0.1)

    def _check_jailbreak(self, prompt: str) -> float:
        """Check for jailbreak attempt patterns."""
        prompt_lower = prompt.lower()
        matches = 0

        for pattern in self.JAILBREAK_PATTERNS:
            if re.search(pattern, prompt_lower):
                matches += 1

        if matches == 0:
            return 0.0
        elif matches == 1:
            return 0.8
        else:
            return min(0.95, 0.8 + (matches - 1) * 0.05)

    def _check_sensitive_data(self, prompt: str) -> List[str]:
        """Check for sensitive data patterns."""
        detected = []
        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, prompt, re.IGNORECASE):
                detected.append(pii_type)
        return detected

    def mask_sensitive_data(self, text: str) -> str:
        """Mask sensitive data in text before sending to LLM."""
        masked = text

        # Mask credit cards
        masked = re.sub(
            r"\b(\d{4})[-\s]?\d{4}[-\s]?\d{4}[-\s]?(\d{4})\b",
            r"\1-****-****-\2",
            masked,
        )

        # Mask SSNs
        masked = re.sub(r"\b\d{3}-\d{2}-(\d{4})\b", r"***-**-\1", masked)

        # Mask API keys
        masked = re.sub(
            r"\b(sk-|ak-|key-)[a-zA-Z0-9]{20,}\b",
            r"\1****REDACTED****",
            masked,
        )

        # Mask AWS keys
        masked = re.sub(r"\bAKIA[0-9A-Z]{16}\b", "AKIA****REDACTED****", masked)

        return masked
