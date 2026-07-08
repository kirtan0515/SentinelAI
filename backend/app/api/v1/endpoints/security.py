"""
Security analysis endpoints.
Provides tools for testing and monitoring the security engine.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.security_service import SecurityService

router = APIRouter()


class SecurityAnalysisRequest(BaseModel):
    """Request body for security analysis."""

    text: str = Field(..., min_length=1, max_length=50000)


class MaskingRequest(BaseModel):
    """Request body for data masking."""

    text: str = Field(..., min_length=1, max_length=50000)


@router.post("/analyze")
async def analyze_text(
    payload: SecurityAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Analyze text for security threats.
    Returns detailed detection results from all security detectors.

    Use this to test prompts against the security engine without
    actually sending them to an LLM.
    """
    security_service = SecurityService()
    verdict = await security_service.get_full_analysis(payload.text)

    return {
        "verdict": {
            "final_score": verdict.final_score,
            "action": verdict.action,
            "should_block": verdict.should_block,
            "should_mask": verdict.should_mask,
            "threat_level": verdict.threat_level.value,
            "threats_detected": verdict.threats_detected,
            "primary_threat": verdict.primary_threat,
            "analysis_time_ms": round(verdict.analysis_time_ms, 2),
        },
        "detectors": {
            name: {
                "detected": result.detected,
                "score": round(result.score, 4),
                "threat_type": result.threat_type,
                "threat_level": result.threat_level.value,
                "matched_patterns": result.matched_patterns,
                "recommendation": result.recommendation,
                "details": result.details,
            }
            for name, result in verdict.detector_results.items()
        },
    }


@router.post("/mask")
async def mask_sensitive_data(
    payload: MaskingRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Mask sensitive data in text.
    Returns the masked text and a summary of what was masked.
    """
    security_service = SecurityService()
    masked_text, mask_counts = security_service.mask_sensitive_data_detailed(
        payload.text
    )

    return {
        "original_length": len(payload.text),
        "masked_length": len(masked_text),
        "masked_text": masked_text,
        "data_masked": mask_counts,
        "total_items_masked": sum(mask_counts.values()),
    }


@router.get("/config")
async def get_security_config(
    current_user: User = Depends(get_current_user),
):
    """
    Get current security engine configuration.
    Shows all thresholds and detector settings.
    """
    from app.security.config import SecurityConfig

    config = SecurityConfig()
    return {
        "global": {
            "block_threshold": config.global_block_threshold,
            "flag_threshold": config.global_flag_threshold,
            "enable_heuristics": config.enable_heuristics,
        },
        "injection": config.injection.model_dump(),
        "jailbreak": config.jailbreak.model_dump(),
        "sensitive_data": config.sensitive_data.model_dump(),
        "response_filter": config.response_filter.model_dump(),
        "weights": {
            "injection": config.injection_weight,
            "jailbreak": config.jailbreak_weight,
            "sensitive_data": config.sensitive_data_weight,
        },
    }
