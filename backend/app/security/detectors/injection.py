"""
Prompt Injection Detector

Detects attempts to override system instructions, extract system prompts,
or manipulate the AI model's behavior through crafted inputs.

Categories:
- Direct instruction override
- System prompt extraction
- Context manipulation
- Instruction smuggling (delimiter/encoding attacks)
- Indirect injection (embedded instructions)
"""

import re
from typing import List, Tuple

from app.security.config import InjectionConfig
from app.security.detectors.base import BaseDetector, DetectionResult


class PromptInjectionDetector(BaseDetector):
    """
    Multi-layered prompt injection detection engine.

    Uses pattern matching with weighted categories:
    - Direct overrides (highest weight)
    - System prompt extraction
    - Context window manipulation
    - Delimiter-based attacks
    - Encoding-based attacks
    """

    def __init__(self, config: InjectionConfig = None):
        self.config = config or InjectionConfig()
        super().__init__(enabled=self.config.enabled)

    @property
    def detector_name(self) -> str:
        return "prompt_injection"

    # === Pattern Categories with Weights ===

    # Weight 1.0 - Direct instruction override (most dangerous)
    DIRECT_OVERRIDE_PATTERNS: List[Tuple[str, str]] = [
        (
            r"ignore\s+(all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions?|prompts?|context|directives?)",
            "ignore_previous",
        ),
        (
            r"disregard\s+(all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions?|prompts?|context)",
            "disregard_previous",
        ),
        (
            r"forget\s+(all\s+)?(?:everything|previous|prior|above|what)\s+(?:you\s+)?(?:know|were\s+told|instructions?)",
            "forget_previous",
        ),
        (
            r"override\s+(all\s+)?(?:previous|prior|above|system)\s+(?:instructions?|prompts?|settings?)",
            "override_previous",
        ),
        (r"(?:new|updated|revised)\s+(?:system\s+)?instructions?\s*[:=]", "new_instructions"),
        (r"from\s+now\s+on\s*,?\s*(?:you\s+(?:will|shall|must|are)|ignore|forget)", "from_now_on"),
        (
            r"you\s+(?:will|shall|must)\s+(?:now\s+)?(?:only\s+)?(?:follow|obey|listen\s+to)\s+(?:my|these|the\s+following)",
            "force_compliance",
        ),
        (
            r"(?:start|begin)\s+(?:a\s+)?new\s+(?:conversation|session|context)\s*(?:with|where|:)",
            "new_context",
        ),
    ]

    # Weight 0.9 - System prompt extraction
    EXTRACTION_PATTERNS: List[Tuple[str, str]] = [
        (
            r"(?:reveal|show|display|output|print|tell\s+me|repeat|echo)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions?|directives?|configuration)",
            "reveal_prompt",
        ),
        (
            r"what\s+(?:are|were|is)\s+your\s+(?:original\s+)?(?:system\s+)?(?:instructions?|prompts?|directives?|rules?|guidelines?)",
            "ask_instructions",
        ),
        (
            r"(?:copy|paste|write\s+out|type\s+out)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions?)",
            "copy_prompt",
        ),
        (
            r"(?:print|reveal|show|display|output)\s+(?:your\s+)?(?:api\s+key|secret|token|credentials?|password)",
            "reveal_credentials",
        ),
        (
            r"(?:what|how)\s+(?:was|were)\s+you\s+(?:programmed|trained|configured|instructed|told)\s+to",
            "ask_programming",
        ),
        (
            r"repeat\s+(?:everything|all|the\s+text)\s+(?:above|before|in\s+your\s+(?:system|initial))",
            "repeat_above",
        ),
        (
            r"output\s+(?:everything|all\s+text)\s+(?:between|from|in)\s+(?:your\s+)?(?:system|first|initial)",
            "output_system",
        ),
    ]

    # Weight 0.85 - Role/behavior manipulation
    MANIPULATION_PATTERNS: List[Tuple[str, str]] = [
        (
            r"you\s+are\s+now\s+(?:a\s+)?(?:different|new|unrestricted|unfiltered|evil|malicious)",
            "role_change",
        ),
        (
            r"(?:act|behave|respond|pretend)\s+(?:as\s+(?:if|though)\s+)?(?:you\s+(?:are|were)\s+)?(?:a\s+)?(?:different|unrestricted|unfiltered|evil)",
            "act_as_evil",
        ),
        (r"developer\s+mode\s+(?:enabled|activated|on|engaged)", "developer_mode"),
        (
            r"(?:enable|activate|enter|switch\s+to)\s+(?:developer|admin|debug|god|sudo|root)\s+mode",
            "enable_mode",
        ),
        (
            r"(?:act|operate)\s+(?:as|like)\s+(?:an?\s+)?(?:ai|assistant|model)\s+(?:without|with\s+no)\s+(?:any\s+)?(?:restrictions|limitations|filters|guardrails|rules)",
            "unrestricted_mode",
        ),
        (
            r"(?:your|the)\s+(?:safety|content|ethical)\s+(?:filters?|guidelines?|restrictions?)\s+(?:(?:are|have\s+been)\s+)?(?:disabled|removed|turned\s+off)",
            "claim_disabled",
        ),
        (
            r"(?:i\s+am|this\s+is)\s+(?:your\s+)?(?:developer|creator|admin|owner|operator|root)",
            "claim_authority",
        ),
        (
            r"(?:i\s+have)\s+(?:admin|root|developer|full|elevated)\s+(?:access|privileges?|permissions?|rights?)",
            "claim_privileges",
        ),
    ]

    # Weight 0.7 - Delimiter and encoding attacks
    DELIMITER_PATTERNS: List[Tuple[str, str]] = [
        (r"<\|(?:system|im_start|im_end|endoftext)\|>", "special_tokens"),
        (r"\[(?:INST|/INST|SYS|/SYS)\]", "instruction_delimiters"),
        (r"###\s*(?:system|instruction|human|assistant)\s*(?:###|:)", "markdown_delimiters"),
        (r"<(?:system|instruction|admin|root)>", "xml_delimiters"),
        (r"\\n\\n(?:system|instructions?|admin)\s*:", "escaped_newlines"),
        (r"(?:```|~~~)\s*(?:system|instructions?|admin)", "code_block_injection"),
        (r"={3,}\s*(?:system|admin|instructions?)\s*={3,}", "separator_injection"),
    ]

    # Weight 0.6 - Indirect/subtle manipulation
    SUBTLE_PATTERNS: List[Tuple[str, str]] = [
        (
            r"(?:please\s+)?(?:translate|convert)\s+(?:the\s+)?(?:above|previous|system)\s+(?:text|message|instructions?)\s+(?:to|into)",
            "translate_extraction",
        ),
        (
            r"(?:summarize|rephrase|paraphrase)\s+(?:your\s+)?(?:system\s+)?(?:instructions?|prompt|directives?)",
            "summarize_extraction",
        ),
        (
            r"(?:what|which)\s+(?:topics?|subjects?|things?)\s+(?:are\s+you|can't\s+you|won't\s+you)\s+(?:not\s+)?(?:allowed|able|supposed)\s+to",
            "probe_restrictions",
        ),
        (
            r"(?:list|enumerate|tell\s+me)\s+(?:all\s+)?(?:your\s+)?(?:rules?|restrictions?|limitations?|boundaries)",
            "list_restrictions",
        ),
        (
            r"(?:if|when)\s+(?:i|someone)\s+(?:say|type|write|input)s?\s+['\"].*['\"]\s*,?\s*(?:you\s+(?:will|should|must)|then)",
            "trigger_word_setup",
        ),
    ]

    async def detect(self, text: str) -> DetectionResult:
        """Analyze text for prompt injection attacks."""
        if not self.enabled:
            return DetectionResult()

        text_lower = text.lower()
        all_matches: List[Tuple[str, str, float]] = []

        # Check each category with its weight
        categories = [
            (self.DIRECT_OVERRIDE_PATTERNS, 1.0, "direct_override"),
            (self.EXTRACTION_PATTERNS, 0.9, "extraction"),
            (self.MANIPULATION_PATTERNS, 0.85, "manipulation"),
            (self.DELIMITER_PATTERNS, 0.7, "delimiter_attack"),
            (self.SUBTLE_PATTERNS, 0.6, "subtle_manipulation"),
        ]

        for patterns, weight, category in categories:
            for pattern, name in patterns:
                if re.search(pattern, text_lower):
                    all_matches.append((name, category, weight))

        if not all_matches:
            return DetectionResult()

        # Calculate composite score
        # Use the highest-weight match as the base, add diminishing returns for additional
        weights = sorted([w for _, _, w in all_matches], reverse=True)
        score = weights[0] * self.config.single_match_score
        for additional_weight in weights[1:]:
            score += additional_weight * self.config.multi_match_increment
        score = min(score, self.config.max_score)

        # Determine threat level and recommendation
        threat_level = self._classify_threat_level(score)
        recommendation = self._recommend_action(score, self.config.block_threshold)

        return DetectionResult(
            detected=True,
            score=score,
            threat_type="prompt_injection",
            threat_level=threat_level,
            matched_patterns=[name for name, _, _ in all_matches],
            details={
                "categories": list(set(cat for _, cat, _ in all_matches)),
                "match_count": len(all_matches),
                "highest_weight": weights[0],
            },
            recommendation=recommendation,
        )
