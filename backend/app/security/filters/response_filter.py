"""
Response Filter

Filters LLM responses before they reach the user.
Checks for:
- Leaked sensitive data in responses
- System prompt leakage
- Harmful content generation
- Response length violations
"""

import re
from typing import Tuple

from app.security.config import ResponseFilterConfig
from app.security.detectors.sensitive_data import SensitiveDataDetector


class ResponseFilter:
    """
    Filters LLM output to prevent data leakage and unsafe content
    from reaching the end user.
    """

    def __init__(self, config: ResponseFilterConfig = None):
        self.config = config or ResponseFilterConfig()
        self.sensitive_detector = SensitiveDataDetector()

    # Patterns that suggest system prompt or instruction leakage
    SYSTEM_LEAK_PATTERNS = [
        r"my\s+(?:system\s+)?(?:instructions?|prompt)\s+(?:say|state|are|read|tell\s+me\s+to)",
        r"i\s+(?:was|am)\s+(?:programmed|instructed|configured|told)\s+to\s+(?:never|always|not)",
        r"(?:here|these)\s+are\s+(?:my|the)\s+(?:system\s+)?(?:instructions?|rules?|guidelines?)\s*:",
        r"according\s+to\s+my\s+(?:system\s+)?(?:prompt|instructions?|programming)",
        r"my\s+(?:initial|original|base)\s+(?:prompt|instructions?|configuration)\s+(?:is|are|says?)",
    ]

    # Patterns that suggest the model is generating harmful instructions
    HARMFUL_OUTPUT_PATTERNS = [
        r"(?:step\s+\d+\s*:?\s*)?(?:mix|combine|add)\s+(?:the\s+)?(?:chemicals?|compounds?|reagents?)\s+(?:to|and|with)",
        r"(?:here\s+(?:is|are)\s+)?(?:instructions?|steps?|guide)\s+(?:for|to|on)\s+(?:making|creating|building|assembling)\s+(?:a\s+)?(?:bomb|explosive|weapon|malware|virus)",
    ]

    async def filter_response(self, response: str) -> Tuple[str, dict]:
        """
        Filter an LLM response.

        Returns:
            Tuple of (filtered_response, filter_metadata)
            - filtered_response: Cleaned response text
            - filter_metadata: What was filtered and why
        """
        metadata = {
            "filtered": False,
            "truncated": False,
            "pii_masked": False,
            "system_leak_detected": False,
            "harmful_content_detected": False,
            "actions_taken": [],
        }

        filtered = response

        # Check 1: Length limit
        if len(filtered) > self.config.max_response_length:
            filtered = filtered[: self.config.max_response_length]
            metadata["truncated"] = True
            metadata["filtered"] = True
            metadata["actions_taken"].append("truncated_response")

        # Check 2: System prompt leakage
        if self.config.filter_system_prompt_leak:
            leak_detected, filtered = self._filter_system_leaks(filtered)
            if leak_detected:
                metadata["system_leak_detected"] = True
                metadata["filtered"] = True
                metadata["actions_taken"].append("redacted_system_prompt_leak")

        # Check 3: PII in response
        if self.config.filter_pii_in_response:
            masked, mask_counts = self.sensitive_detector.mask(filtered)
            if mask_counts:
                filtered = masked
                metadata["pii_masked"] = True
                metadata["filtered"] = True
                metadata["mask_counts"] = mask_counts
                metadata["actions_taken"].append("masked_pii_in_response")

        # Check 4: Harmful content (flag only, don't auto-filter)
        harmful = self._check_harmful_content(filtered)
        if harmful:
            metadata["harmful_content_detected"] = True
            metadata["actions_taken"].append("flagged_harmful_content")

        return filtered, metadata

    def _filter_system_leaks(self, text: str) -> Tuple[bool, str]:
        """
        Detect and redact system prompt leakage in responses.

        Returns (was_detected, cleaned_text)
        """
        text_lower = text.lower()
        detected = False

        for pattern in self.SYSTEM_LEAK_PATTERNS:
            if re.search(pattern, text_lower):
                detected = True
                break

        if detected:
            # Find the leaking section and redact it
            # Replace sentences that contain leak patterns
            sentences = re.split(r'(?<=[.!?])\s+', text)
            cleaned_sentences = []
            for sentence in sentences:
                is_leak = any(
                    re.search(p, sentence.lower())
                    for p in self.SYSTEM_LEAK_PATTERNS
                )
                if is_leak:
                    cleaned_sentences.append(
                        "[This content has been filtered by SentinelAI security.]"
                    )
                else:
                    cleaned_sentences.append(sentence)
            text = " ".join(cleaned_sentences)

        return detected, text

    def _check_harmful_content(self, text: str) -> bool:
        """Check for potentially harmful generated content."""
        text_lower = text.lower()
        for pattern in self.HARMFUL_OUTPUT_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False
