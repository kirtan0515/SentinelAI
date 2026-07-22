"""
AI Chat endpoints - the core gateway.
All requests flow through the security pipeline before reaching LLMs.
"""

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionResponse
from app.services.chat_service import ChatService
from app.services.security_service import SecurityService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message through the AI Security Gateway.

    Security Pipeline:
    1. Authentication (handled by dependency)
    2. Input Security Analysis (prompt injection, jailbreak, PII)
    3. Sensitive Data Masking (mask PII before LLM)
    4. Model Router → LLM
    5. Response Security Filter (output analysis)
    6. Audit Logging
    """
    start_time = time.time()
    security_service = SecurityService()

    # === STEP 1: Input Security Analysis ===
    security_result = await security_service.analyze_prompt(payload.message)

    if not security_result.is_safe:
        # Log the blocked request
        chat_service = ChatService(db)
        await chat_service.log_blocked_request(
            user=current_user,
            prompt=payload.message,
            security_result=security_result,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Request blocked by security engine",
                "threats": security_result.threats_detected,
                "score": security_result.score,
                "action": security_result.details.get("action", "block"),
                "primary_threat": security_result.details.get("primary_threat"),
            },
        )

    # === STEP 2: Sensitive Data Masking ===
    # If PII detected but below block threshold, mask before sending to LLM
    prompt_for_llm = payload.message
    if security_result.details and security_result.details.get("should_mask"):
        prompt_for_llm = security_service.mask_sensitive_data(payload.message)

    # === STEP 3: Process through AI Gateway ===
    chat_service = ChatService(db)
    response = await chat_service.process_message(
        user=current_user,
        request=payload,
        prompt_override=prompt_for_llm,
        start_time=start_time,
    )

    # === STEP 4: Response Security Filter ===
    filtered_message, filter_metadata = await security_service.filter_response(response.message)
    response.message = filtered_message
    response.security_score = security_result.score

    return response


@router.post("/analyze")
async def analyze_prompt_security(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Analyze a prompt's security without sending to LLM.
    Returns detailed security analysis for debugging/testing.
    """
    security_service = SecurityService()
    verdict = await security_service.get_full_analysis(payload.message)

    return {
        "final_score": verdict.final_score,
        "action": verdict.action,
        "should_block": verdict.should_block,
        "should_mask": verdict.should_mask,
        "threat_level": verdict.threat_level.value,
        "threats_detected": verdict.threats_detected,
        "primary_threat": verdict.primary_threat,
        "detectors_triggered": verdict.detectors_triggered,
        "analysis_time_ms": round(verdict.analysis_time_ms, 2),
        "detector_details": {
            name: {
                "detected": result.detected,
                "score": result.score,
                "threat_level": result.threat_level.value,
                "matched_patterns": result.matched_patterns,
                "recommendation": result.recommendation,
            }
            for name, result in verdict.detector_results.items()
        },
    }


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's chat sessions."""
    chat_service = ChatService(db)
    return await chat_service.get_user_sessions(current_user.id)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific chat session with messages."""
    chat_service = ChatService(db)
    session = await chat_service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session."""
    chat_service = ChatService(db)
    await chat_service.delete_session(session_id, current_user.id)
