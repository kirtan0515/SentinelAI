"""
Chat Service - Orchestrates the AI gateway pipeline.
"""

import time
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionResponse, SecurityCheckResult
from app.services.model_router import ModelRouter


class ChatService:
    """
    Orchestrates the chat pipeline:
    1. Session management
    2. Model routing
    3. Response processing
    4. Audit logging
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_router = ModelRouter()

    async def process_message(
        self,
        user: User,
        request: ChatRequest,
        start_time: float,
        prompt_override: Optional[str] = None,
    ) -> ChatResponse:
        """Process a chat message through the full pipeline."""
        # Determine model
        model = request.model or "gpt-4"

        # Use masked prompt if provided, otherwise original
        message_for_llm = prompt_override or request.message

        # Route to appropriate LLM
        llm_response = await self.model_router.route(
            model=model,
            message=message_for_llm,
            session_id=request.session_id,
        )

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # TODO: Store in database, create audit log
        # For now, return structured response
        import uuid

        return ChatResponse(
            id=uuid.uuid4(),
            session_id=request.session_id or uuid.uuid4(),
            message=llm_response["content"],
            model=model,
            tokens_used=llm_response.get("tokens_used", 0),
            latency_ms=latency_ms,
            security_score=0.0,
            blocked=False,
            created_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ),
        )

    async def log_blocked_request(
        self,
        user: User,
        prompt: str,
        security_result: SecurityCheckResult,
    ) -> None:
        """Log a blocked request to audit and attack tables."""
        # TODO: Implement audit logging
        pass

    async def get_user_sessions(self, user_id: UUID) -> list:
        """Get all chat sessions for a user."""
        # TODO: Implement with repository
        return []

    async def get_session(
        self, session_id: UUID, user_id: UUID
    ) -> Optional[ChatSessionResponse]:
        """Get a specific session."""
        # TODO: Implement with repository
        return None

    async def delete_session(self, session_id: UUID, user_id: UUID) -> None:
        """Delete a chat session."""
        # TODO: Implement with repository
        pass
