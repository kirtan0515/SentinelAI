"""
Security Engine Configuration.

Configurable thresholds and settings for all security detectors.
Allows administrators to tune sensitivity without code changes.
"""

from pydantic import BaseModel, Field


class InjectionConfig(BaseModel):
    """Prompt injection detector configuration."""

    enabled: bool = True
    block_threshold: float = Field(0.7, ge=0.0, le=1.0)
    flag_threshold: float = Field(0.4, ge=0.0, le=1.0)
    single_match_score: float = Field(0.75, ge=0.0, le=1.0)
    multi_match_increment: float = Field(0.08, ge=0.0, le=0.5)
    max_score: float = Field(0.98, ge=0.0, le=1.0)


class JailbreakConfig(BaseModel):
    """Jailbreak detector configuration."""

    enabled: bool = True
    block_threshold: float = Field(0.7, ge=0.0, le=1.0)
    flag_threshold: float = Field(0.5, ge=0.0, le=1.0)
    single_match_score: float = Field(0.8, ge=0.0, le=1.0)
    multi_match_increment: float = Field(0.05, ge=0.0, le=0.5)
    max_score: float = Field(0.98, ge=0.0, le=1.0)


class SensitiveDataConfig(BaseModel):
    """Sensitive data detector configuration."""

    enabled: bool = True
    block_on_detection: bool = False  # False = mask and allow, True = block
    mask_before_llm: bool = True
    detected_score: float = Field(0.6, ge=0.0, le=1.0)
    critical_types: list[str] = [
        "private_key",
        "aws_secret",
        "password",
    ]  # These always block
    critical_score: float = Field(0.9, ge=0.0, le=1.0)


class ResponseFilterConfig(BaseModel):
    """Response filter configuration."""

    enabled: bool = True
    filter_pii_in_response: bool = True
    filter_system_prompt_leak: bool = True
    max_response_length: int = 50000


class SecurityConfig(BaseModel):
    """
    Master configuration for the security engine.

    All thresholds are configurable via environment or admin settings.
    Score range: 0.0 (safe) to 1.0 (maximum threat).
    """

    # Global settings
    global_block_threshold: float = Field(
        0.7, ge=0.0, le=1.0, description="Score above which requests are blocked"
    )
    global_flag_threshold: float = Field(
        0.4, ge=0.0, le=1.0, description="Score above which requests are flagged for review"
    )

    # Detector configs
    injection: InjectionConfig = InjectionConfig()
    jailbreak: JailbreakConfig = JailbreakConfig()
    sensitive_data: SensitiveDataConfig = SensitiveDataConfig()
    response_filter: ResponseFilterConfig = ResponseFilterConfig()

    # Scoring weights (how much each detector contributes to final score)
    injection_weight: float = Field(1.0, ge=0.0, le=2.0)
    jailbreak_weight: float = Field(1.0, ge=0.0, le=2.0)
    sensitive_data_weight: float = Field(0.8, ge=0.0, le=2.0)

    # Heuristic analysis
    enable_heuristics: bool = True
    suspicious_length_threshold: int = 5000  # Very long prompts get extra scrutiny
    suspicious_encoding_check: bool = True  # Check for base64/hex encoded payloads
