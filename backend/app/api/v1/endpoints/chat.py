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

    Flow:
    1. Authentication (handled by dependency)
    2. Security Engine (prompt injection, jailbreak, PII detection)
    3. Guardrails check
    4. Model Router → LLM
    5. Response filter
    6. Audit logging
    """
    start_time = time.time()

    # Security check
    security_service = SecurityService()
    security_result = await security_service.analyze_prompt(payload.message)

    if not security_result.is_safe:
        # Log the attack and return blocked response
        chat_service = ChatService(db)
        blocked_response = await chat_service.log_blocked_request(
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
            },
        )

    # Process through AI gateway
    chat_service = ChatService(db)
    response = await chat_service.process_message(
        user=current_user,
        request=payload,
        start_time=start_time,
    )

    return response


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
