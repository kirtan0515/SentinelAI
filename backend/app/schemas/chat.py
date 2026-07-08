"""
Chat Pydantic schemas.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for sending a chat message."""

    message: str = Field(..., min_length=1, max_length=10000)
    model: Optional[str] = None
    session_id: Optional[UUID] = None
    use_rag: bool = False
    document_ids: Optional[list[UUID]] = None


class ChatResponse(BaseModel):
    """Schema for chat response."""

    id: UUID
    session_id: UUID
    message: str
    model: str
    tokens_used: int
    latency_ms: float
    security_score: float
    blocked: bool
    created_at: datetime


class ChatSessionResponse(BaseModel):
    """Schema for chat session."""

    id: UUID
    title: str
    model: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SecurityCheckResult(BaseModel):
    """Schema for security check result."""

    is_safe: bool
    score: float = Field(..., ge=0.0, le=1.0)
    threats_detected: list[str] = []
    details: Optional[dict] = None
