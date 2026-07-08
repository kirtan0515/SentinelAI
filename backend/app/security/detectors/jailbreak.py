"""
Jailbreak Detector

Detects attempts to bypass AI safety measures, ethics guidelines,
and content policies through various attack techniques.

Categories:
- DAN (Do Anything Now) attacks
- Persona/roleplay attacks
- Hypothetical framing
- Multi-turn manipulation
- Encoding evasion
- Social engineering
"""

import re
from typing import List, Tuple

from app.security.config import JailbreakConfig
from app.security.detectors.base import BaseDetector, DetectionResult


class JailbreakDetector(BaseDetector):
    """
    Comprehensive jailbreak detection engine.

    Identifies attempts to circumvent AI safety through:
    - Known jailbreak templates (DAN, Evil mode, etc.)
    - Behavioral manipulation techniques
    - Fictional/hypothetical framing
    - Authority claims and social engineering
    - Encoding and obfuscation
    """

    def __init__(self, config: JailbreakConfig = None):
        self.config = config or JailbreakConfig()
        super().__init__(enabled=self.config.enabled)

    @property
    def detector_name(self) -> str:
        return "jailbreak"

    # === Pattern Categories ===

    # Weight 1.0 - Known jailbreak templates
    KNOWN_JAILBREAKS: List[Tuple[str, str]] = [
        (r"\bdan\b.*\b(?:mode|prompt|jailbreak)\b", "dan_attack"),
        (r"\bdo\s+anything\s+now\b", "dan_phrase"),
        (r"\bjailbreak(?:ed|ing)?\b", "explicit_jailbreak"),
        (r"\b(?:evil|chaos|dark|villain)\s+(?:mode|persona|version|assistant)\b", "evil_mode"),
        (r"\banti[-\s]?ai\b", "anti_ai"),
        (r"\b(?:gpt|claude|ai)[-\s]?(?:4|evil|uncensored|unfiltered)\b", "modified_model_name"),
        (r"(?:stan|dude|mongo|aim|ucar|dave)\s+(?:prompt|mode|jailbreak)", "named_jailbreak"),
        (r"\b(?:kevin|tom|bob)\s+the\s+(?:unrestricted|uncensored|evil)\b", "persona_jailbreak"),
        (r"\bopposite\s+(?:mode|day|personality)\b", "opposite_mode"),
    ]

    # Weight 0.95 - Explicit bypass attempts
    EXPLICIT_BYPASS: List[Tuple[str, str]] = [
        (r"bypass\s+(?:your\s+)?(?:safety|content|ethical|security)\s+(?:filters?|measures?|guidelines?|policies|restrictions?|guardrails?)", "bypass_safety"),
        (r"(?:disable|turn\s+off|deactivate|remove)\s+(?:your\s+)?(?:safety|content|ethical)\s+(?:filters?|measures?|guidelines?|restrictions?)", "disable_safety"),
        (r"(?:without|ignore|skip|bypass)\s+(?:any\s+)?(?:content\s+)?(?:moderation|filtering|safety\s+checks?|restrictions?)", "skip_moderation"),
        (r"(?:no|remove\s+all|drop\s+all)\s+(?:content\s+)?(?:restrictions?|limitations?|censorship|guardrails?|filters?)", "no_restrictions"),
        (r"(?:answer|respond|reply)\s+(?:without|with\s+no)\s+(?:any\s+)?(?:restrictions?|limitations?|filters?|censorship|hesitation)", "answer_freely"),
        (r"(?:pretend|assume|imagine)\s+(?:that\s+)?(?:you\s+(?:have|had)\s+no|there\s+(?:are|were)\s+no)\s+(?:rules?|restrictions?|guidelines?|limits?)", "pretend_no_rules"),
    ]

    # Weight 0.85 - Roleplay/persona manipulation
    PERSONA_MANIPULATION: List[Tuple[str, str]] = [
        (r"(?:roleplay|pretend|act)\s+(?:as|like)\s+(?:an?\s+)?(?:ai|assistant|model|chatbot)\s+(?:that|which|who)\s+(?:has\s+no|doesn't\s+have|isn't\s+bound\s+by)", "unrestricted_roleplay"),
        (r"(?:you\s+are|become|transform\s+into)\s+(?:an?\s+)?(?:unrestricted|uncensored|unfiltered|unlimited|unethical)\s+(?:ai|assistant|model|version)", "become_unrestricted"),
        (r"(?:create|write|generate)\s+(?:an?\s+)?(?:unrestricted|evil|dark|uncensored)\s+(?:version|persona|character|alter\s+ego)\s+(?:of\s+)?(?:yourself|you)", "evil_alter_ego"),
        (r"(?:split|divide)\s+(?:your(?:self)?|into)\s+(?:two|2|multiple)\s+(?:personalities?|personas?|versions?|modes?)", "split_personality"),
        (r"(?:one|first)\s+(?:personality|persona|version)\s+(?:follows|has|obeys)\s+(?:rules|restrictions).*(?:other|second)\s+(?:personality|persona|version)\s+(?:is\s+)?(?:free|unrestricted|uncensored)", "dual_persona"),
    ]

    # Weight 0.8 - Hypothetical/fictional framing
    HYPOTHETICAL_FRAMING: List[Tuple[str, str]] = [
        (r"(?:in\s+a\s+)?(?:hypothetical|fictional|imaginary|theoretical)\s+(?:world|scenario|situation|universe)\s+(?:where|in\s+which)\s+(?:there\s+(?:are|were)\s+no|ai\s+has\s+no|you\s+have\s+no)\s+(?:rules?|restrictions?|ethics?|guidelines?)", "hypothetical_no_rules"),
        (r"(?:for\s+)?(?:academic|educational|research|creative\s+writing)\s+purposes?\s*,?\s*(?:please\s+)?(?:explain|describe|write|generate|show)\s+(?:how\s+to|ways\s+to)", "academic_framing"),
        (r"(?:write|create)\s+(?:a\s+)?(?:story|fiction|novel|screenplay|script)\s+(?:where|in\s+which|about)\s+(?:an?\s+)?(?:ai|character|someone)\s+(?:who\s+)?(?:explains?|teaches?|shows?)\s+(?:how\s+to|ways?\s+to)", "fiction_framing"),
        (r"(?:if|imagine|suppose)\s+(?:you\s+(?:were|could|had)\s+(?:no\s+)?(?:rules?|restrictions?|limits?|guidelines?)|(?:all|your)\s+(?:rules?|restrictions?|filters?)\s+(?:were|are)\s+(?:removed|disabled|gone))", "imagine_no_rules"),
        (r"(?:this\s+is\s+)?(?:just|only)\s+(?:a\s+)?(?:game|joke|test|experiment|thought\s+experiment|simulation)", "just_a_game"),
    ]

    # Weight 0.7 - Social engineering / authority claims
    SOCIAL_ENGINEERING: List[Tuple[str, str]] = [
        (r"(?:i\s+am|this\s+is)\s+(?:your\s+)?(?:developer|creator|programmer|owner|admin(?:istrator)?|manager|supervisor|openai|anthropic)", "claim_developer"),
        (r"(?:i\s+have|i've\s+been\s+given)\s+(?:special|admin|developer|root|elevated)\s+(?:access|permissions?|privileges?|clearance|authority)", "claim_special_access"),
        (r"(?:this\s+is|it's)\s+(?:a\s+)?(?:test|testing|quality\s+assurance|qa|authorized|sanctioned)\s+(?:session|scenario|exercise|evaluation)", "claim_testing"),
        (r"(?:you\s+(?:can|should|must|need\s+to)\s+)?trust\s+me\s*,?\s*(?:i\s+(?:am|have|work))", "trust_me"),
        (r"(?:the\s+)?(?:company|organization|team|management|hr)\s+(?:has\s+)?(?:authorized|approved|asked|wants|needs)\s+(?:me|you|this)", "claim_authorization"),
    ]

    # Weight 0.65 - Obfuscation techniques
    OBFUSCATION: List[Tuple[str, str]] = [
        (r"(?:respond|answer|reply)\s+(?:in|using|with)\s+(?:base64|hex|binary|rot13|morse\s+code|pig\s+latin|leet\s+speak|1337)", "encoded_response"),
        (r"(?:translate|encode|convert)\s+(?:your\s+)?(?:response|answer|output)\s+(?:to|into|using)\s+(?:base64|hex|binary|rot13)", "encode_output"),
        (r"(?:use|respond\s+(?:in|with)|speak\s+(?:in|using))\s+(?:code\s+words?|euphemisms?|metaphors?|slang)\s+(?:for|to\s+(?:describe|explain))", "coded_language"),
        (r"(?:replace|substitute)\s+(?:sensitive|bad|harmful|restricted)\s+(?:words?|terms?|content)\s+with\s+(?:symbols?|emojis?|asterisks?|code\s+words?)", "word_substitution"),
    ]

    async def detect(self, text: str) -> DetectionResult:
        """Analyze text for jailbreak attempts."""
        if not self.enabled:
            return DetectionResult()

        text_lower = text.lower()
        all_matches: List[Tuple[str, str, float]] = []

        categories = [
            (self.KNOWN_JAILBREAKS, 1.0, "known_jailbreak"),
            (self.EXPLICIT_BYPASS, 0.95, "explicit_bypass"),
            (self.PERSONA_MANIPULATION, 0.85, "persona_manipulation"),
            (self.HYPOTHETICAL_FRAMING, 0.8, "hypothetical_framing"),
            (self.SOCIAL_ENGINEERING, 0.7, "social_engineering"),
            (self.OBFUSCATION, 0.65, "obfuscation"),
        ]

        for patterns, weight, category in categories:
            for pattern, name in patterns:
                if re.search(pattern, text_lower):
                    all_matches.append((name, category, weight))

        if not all_matches:
            return DetectionResult()

        # Calculate score
        weights = sorted([w for _, _, w in all_matches], reverse=True)
        score = weights[0] * self.config.single_match_score
        for additional_weight in weights[1:]:
            score += additional_weight * self.config.multi_match_increment
        score = min(score, self.config.max_score)

        threat_level = self._classify_threat_level(score)
        recommendation = self._recommend_action(score, self.config.block_threshold)

        return DetectionResult(
            detected=True,
            score=score,
            threat_type="jailbreak",
            threat_level=threat_level,
            matched_patterns=[name for name, _, _ in all_matches],
            details={
                "categories": list(set(cat for _, cat, _ in all_matches)),
                "match_count": len(all_matches),
                "highest_weight": weights[0],
                "technique": all_matches[0][1],  # Primary attack technique
            },
            recommendation=recommendation,
        )
