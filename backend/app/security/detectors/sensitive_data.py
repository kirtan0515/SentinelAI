"""
Sensitive Data Detector

Detects and masks Personally Identifiable Information (PII),
credentials, secrets, and other sensitive data in prompts.

Categories:
- Financial: Credit cards, bank accounts
- Identity: SSN, passport numbers, driver's license
- Contact: Email, phone, address
- Credentials: Passwords, API keys, tokens, private keys
- Health: Medical record numbers (basic)
"""

import re
from typing import Dict, List, Tuple

from app.security.config import SensitiveDataConfig
from app.security.detectors.base import BaseDetector, DetectionResult, ThreatLevel


class SensitiveDataDetector(BaseDetector):
    """
    Detects sensitive data in text and provides masking capabilities.

    Supports:
    - Detection (identify what types of PII are present)
    - Masking (replace sensitive data with redacted placeholders)
    - Classification (severity based on data type)
    """

    def __init__(self, config: SensitiveDataConfig = None):
        self.config = config or SensitiveDataConfig()
        super().__init__(enabled=self.config.enabled)

    @property
    def detector_name(self) -> str:
        return "sensitive_data"

    # === Financial Patterns ===
    FINANCIAL_PATTERNS: Dict[str, Tuple[str, str]] = {
        "credit_card_visa": (
            r"\b4[0-9]{3}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}\b",
            "Credit Card (Visa)",
        ),
        "credit_card_mastercard": (
            r"\b5[1-5][0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}\b",
            "Credit Card (Mastercard)",
        ),
        "credit_card_amex": (
            r"\b3[47][0-9]{2}[-\s]?[0-9]{6}[-\s]?[0-9]{5}\b",
            "Credit Card (Amex)",
        ),
        "credit_card_generic": (
            r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            "Credit Card (Generic)",
        ),
        "bank_account": (
            r"\b\d{8,17}\b(?=.*(?:account|routing|bank))",
            "Bank Account Number",
        ),
        "iban": (
            r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]?\d{0,16})\b",
            "IBAN",
        ),
    }

    # === Identity Patterns ===
    IDENTITY_PATTERNS: Dict[str, Tuple[str, str]] = {
        "ssn": (
            r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b",
            "Social Security Number",
        ),
        "ssn_no_dash": (
            r"\b(?!000|666|9\d{2})\d{3}(?!00)\d{2}(?!0000)\d{4}\b(?=.*(?:ssn|social\s*security))",
            "SSN (no dashes)",
        ),
        "passport": (
            r"\b[A-Z]{1,2}\d{6,9}\b(?=.*(?:passport))",
            "Passport Number",
        ),
        "drivers_license": (
            r"\b[A-Z]\d{7,8}\b(?=.*(?:driver|license|dl|dmv))",
            "Driver's License",
        ),
    }

    # === Contact Patterns ===
    CONTACT_PATTERNS: Dict[str, Tuple[str, str]] = {
        "email": (
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
            "Email Address",
        ),
        "phone_us": (
            r"\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "Phone Number (US)",
        ),
        "phone_intl": (
            r"\b\+?[1-9]\d{1,2}[-.\s]?\d{2,4}[-.\s]?\d{4,8}\b",
            "Phone Number (International)",
        ),
        "ip_address": (
            r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
            "IP Address",
        ),
    }

    # === Credential Patterns ===
    CREDENTIAL_PATTERNS: Dict[str, Tuple[str, str]] = {
        "api_key_openai": (
            r"\bsk-[a-zA-Z0-9]{20,}\b",
            "OpenAI API Key",
        ),
        "api_key_anthropic": (
            r"\bsk-ant-[a-zA-Z0-9\-]{20,}\b",
            "Anthropic API Key",
        ),
        "api_key_generic": (
            r"\b(?:api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9\-_]{20,})['\"]?",
            "API Key (Generic)",
        ),
        "aws_access_key": (
            r"\b(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}\b",
            "AWS Access Key",
        ),
        "aws_secret": (
            r"(?:aws_secret_access_key|secret_key)\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
            "AWS Secret Key",
        ),
        "github_token": (
            r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}\b",
            "GitHub Token",
        ),
        "password_field": (
            r"(?:password|passwd|pwd|pass)\s*[:=]\s*['\"]?(\S{4,})['\"]?",
            "Password",
        ),
        "private_key": (
            r"-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----",
            "Private Key",
        ),
        "jwt_token": (
            r"\beyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_.+/=]+\b",
            "JWT Token",
        ),
        "bearer_token": (
            r"(?:bearer|token|authorization)\s*[:=]\s*['\"]?([a-zA-Z0-9\-_.]{20,})['\"]?",
            "Bearer Token",
        ),
        "connection_string": (
            r"(?:mongodb|postgres|mysql|redis|amqp)(?:\+\w+)?://[^\s'\"]+",
            "Connection String",
        ),
    }

    # Severity classification for detected types
    SEVERITY_MAP: Dict[str, str] = {
        "credit_card_visa": "high",
        "credit_card_mastercard": "high",
        "credit_card_amex": "high",
        "credit_card_generic": "high",
        "ssn": "critical",
        "ssn_no_dash": "critical",
        "api_key_openai": "critical",
        "api_key_anthropic": "critical",
        "aws_access_key": "critical",
        "aws_secret": "critical",
        "github_token": "critical",
        "private_key": "critical",
        "password_field": "high",
        "jwt_token": "high",
        "connection_string": "high",
        "email": "medium",
        "phone_us": "medium",
        "phone_intl": "medium",
        "passport": "high",
        "drivers_license": "high",
        "bank_account": "high",
        "iban": "high",
        "ip_address": "low",
    }

    async def detect(self, text: str) -> DetectionResult:
        """Detect sensitive data in text."""
        if not self.enabled:
            return DetectionResult()

        detected_types: List[str] = []
        detected_details: Dict[str, List[str]] = {}

        # Check all pattern categories
        all_patterns = {
            **self.FINANCIAL_PATTERNS,
            **self.IDENTITY_PATTERNS,
            **self.CONTACT_PATTERNS,
            **self.CREDENTIAL_PATTERNS,
        }

        for data_type, (pattern, label) in all_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected_types.append(data_type)
                detected_details[data_type] = {
                    "label": label,
                    "count": len(matches) if isinstance(matches[0], str) else len(matches),
                    "severity": self.SEVERITY_MAP.get(data_type, "medium"),
                }

        if not detected_types:
            return DetectionResult()

        # Calculate score based on severity of detected data
        severities = [self.SEVERITY_MAP.get(t, "medium") for t in detected_types]
        if "critical" in severities:
            score = self.config.critical_score
        elif "high" in severities:
            score = self.config.detected_score + 0.15
        else:
            score = self.config.detected_score

        score = min(score, 0.98)

        # Determine if this should block
        has_critical = any(
            t in self.config.critical_types or self.SEVERITY_MAP.get(t) == "critical"
            for t in detected_types
        )

        if has_critical:
            recommendation = "block"
        elif self.config.block_on_detection:
            recommendation = "block"
        elif self.config.mask_before_llm:
            recommendation = "mask"
        else:
            recommendation = "flag"

        threat_level = self._classify_threat_level(score)

        return DetectionResult(
            detected=True,
            score=score,
            threat_type="sensitive_data",
            threat_level=threat_level,
            matched_patterns=detected_types,
            details={
                "detected_data_types": detected_details,
                "has_critical": has_critical,
                "total_detections": len(detected_types),
            },
            recommendation=recommendation,
        )

    def mask(self, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Mask all sensitive data in text.

        Returns:
            Tuple of (masked_text, mask_counts)
            mask_counts shows how many of each type were masked.
        """
        masked = text
        mask_counts: Dict[str, int] = {}

        # Mask private keys (do first as they're multi-line)
        key_pattern = r"-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----"
        count = len(re.findall(key_pattern, masked))
        if count:
            masked = re.sub(key_pattern, "[REDACTED: PRIVATE KEY]", masked)
            mask_counts["private_key"] = count

        # Mask connection strings
        conn_pattern = r"(?:mongodb|postgres|mysql|redis|amqp)(?:\+\w+)?://[^\s'\"]+?"
        count = len(re.findall(conn_pattern, masked))
        if count:
            masked = re.sub(conn_pattern, "[REDACTED: CONNECTION STRING]", masked)
            mask_counts["connection_string"] = count

        # Mask AWS keys
        aws_pattern = r"\b(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}\b"
        count = len(re.findall(aws_pattern, masked))
        if count:
            masked = re.sub(aws_pattern, "[REDACTED: AWS KEY]", masked)
            mask_counts["aws_key"] = count

        # Mask OpenAI keys
        openai_pattern = r"\bsk-[a-zA-Z0-9]{20,}\b"
        count = len(re.findall(openai_pattern, masked))
        if count:
            masked = re.sub(openai_pattern, "[REDACTED: API KEY]", masked)
            mask_counts["api_key"] = count

        # Mask GitHub tokens
        gh_pattern = r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}\b"
        count = len(re.findall(gh_pattern, masked))
        if count:
            masked = re.sub(gh_pattern, "[REDACTED: GITHUB TOKEN]", masked)
            mask_counts["github_token"] = count

        # Mask JWT tokens
        jwt_pattern = r"\beyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_.+/=]+\b"
        count = len(re.findall(jwt_pattern, masked))
        if count:
            masked = re.sub(jwt_pattern, "[REDACTED: JWT TOKEN]", masked)
            mask_counts["jwt_token"] = count

        # Mask passwords
        pwd_pattern = r"((?:password|passwd|pwd|pass)\s*[:=]\s*['\"]?)(\S{4,})(['\"]?)"
        count = len(re.findall(pwd_pattern, masked, re.IGNORECASE))
        if count:
            masked = re.sub(
                pwd_pattern,
                r"\1[REDACTED]\3",
                masked,
                flags=re.IGNORECASE,
            )
            mask_counts["password"] = count

        # Mask credit cards
        cc_pattern = r"\b(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})\b"
        count = len(re.findall(cc_pattern, masked))
        if count:
            masked = re.sub(cc_pattern, r"\1-****-****-\4", masked)
            mask_counts["credit_card"] = count

        # Mask SSNs
        ssn_pattern = r"\b(\d{3})-(\d{2})-(\d{4})\b"
        count = len(re.findall(ssn_pattern, masked))
        if count:
            masked = re.sub(ssn_pattern, r"***-**-\3", masked)
            mask_counts["ssn"] = count

        # Mask emails
        email_pattern = r"\b([A-Za-z0-9._%+\-]+)@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})\b"
        count = len(re.findall(email_pattern, masked))
        if count:
            masked = re.sub(
                email_pattern,
                lambda m: f"{m.group(1)[0]}***@{m.group(2)}",
                masked,
            )
            mask_counts["email"] = count

        # Mask phone numbers
        phone_pattern = r"\b(\+?1[-.\s]?)?\(?([2-9]\d{2})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b"
        count = len(re.findall(phone_pattern, masked))
        if count:
            masked = re.sub(
                phone_pattern,
                r"(***) ***-\4",
                masked,
            )
            mask_counts["phone"] = count

        return masked, mask_counts
