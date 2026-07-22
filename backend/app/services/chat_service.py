"""
Chat Service - Orchestrates the full AI gateway pipeline.

Pipeline:
1. Session management
2. Guardrails (input)
3. Model routing (with retries/fallback)
4. Guardrails (output)
5. Response processing
6. Audit logging
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.guardrails.manager import GuardrailsManager
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionResponse, SecurityCheckResult
from app.services.model_router import ModelRouter

logger = structlog.get_logger(__name__)


class ChatService:
    """
    Orchestrates the complete chat pipeline including
    guardrails, routing, and audit logging.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_router = ModelRouter()
        self.guardrails = GuardrailsManager()

    async def process_message(
        self,
        user: User,
        request: ChatRequest,
        start_time: float,
        prompt_override: Optional[str] = None,
    ) -> ChatResponse:
        """
        Process a chat message through the full pipeline.

        Steps:
        1. Apply input guardrails
        2. Route to LLM via gateway
        3. Apply output guardrails
        4. Create response
        5. Log to audit trail
        """
        model = request.model or "llama3"
        message_for_llm = prompt_override or request.message

        # === Input Guardrails ===
        guardrail_result = await self.guardrails.check_input(message_for_llm)
        if not guardrail_result.allowed:
            logger.info(
                "Guardrails blocked input",
                user_id=str(user.id),
                rail=guardrail_result.rail_triggered,
            )
            return ChatResponse(
                id=uuid.uuid4(),
                session_id=request.session_id or uuid.uuid4(),
                message="Your request was blocked by the AI safety guardrails. "
                "Please rephrase your question.",
                model=model,
                tokens_used=0,
                latency_ms=(time.time() - start_time) * 1000,
                security_score=0.9,
                blocked=True,
                created_at=datetime.now(timezone.utc),
            )

        # === Route to LLM ===
        llm_response = await self.model_router.route(
            model=model,
            message=message_for_llm,
            session_id=request.session_id,
        )

        # Handle LLM error
        if llm_response.get("error"):
            return ChatResponse(
                id=uuid.uuid4(),
                session_id=request.session_id or uuid.uuid4(),
                message=f"Service temporarily unavailable. "
                f"Error: {llm_response.get('content', 'Unknown error')}",
                model=model,
                tokens_used=0,
                latency_ms=(time.time() - start_time) * 1000,
                security_score=0.0,
                blocked=False,
                created_at=datetime.now(timezone.utc),
            )

        response_content = llm_response["content"]

        # === Output Guardrails ===
        output_result = await self.guardrails.check_output(message_for_llm, response_content)
        if output_result.modified_text:
            response_content = output_result.modified_text

        # === Calculate metrics ===
        latency_ms = (time.time() - start_time) * 1000
        tokens_used = llm_response.get("tokens_used", 0)

        # === Build response ===
        response = ChatResponse(
            id=uuid.uuid4(),
            session_id=request.session_id or uuid.uuid4(),
            message=response_content,
            model=llm_response.get("model", model),
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            security_score=0.0,
            blocked=False,
            created_at=datetime.now(timezone.utc),
        )

        # === Audit Log ===
        await self._log_request(
            user=user,
            prompt=request.message,
            response_text=response_content,
            model=model,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            cost_estimate=llm_response.get("cost_estimate", 0.0),
        )

        logger.info(
            "Chat request processed",
            user_id=str(user.id),
            model=model,
            tokens=tokens_used,
            latency_ms=round(latency_ms, 1),
            provider=llm_response.get("provider", "unknown"),
        )

        return response

    async def log_blocked_request(
        self,
        user: User,
        prompt: str,
        security_result: SecurityCheckResult,
    ) -> None:
        """Log a blocked request to audit and attack tables."""
        logger.warning(
            "Request blocked by security engine",
            user_id=str(user.id),
            score=security_result.score,
            threats=security_result.threats_detected,
        )
        # TODO: Write to audit_logs and attack_logs tables
        # This will be fully implemented when we wire up the repositories

    async def _log_request(
        self,
        user: User,
        prompt: str,
        response_text: str,
        model: str,
        tokens_used: int,
        latency_ms: float,
        cost_estimate: float = 0.0,
    ) -> None:
        """Log a successful request to the audit trail."""
        # TODO: Write to audit_logs table via repository
        pass

    async def get_user_sessions(self, user_id: UUID) -> list:
        """Get all chat sessions for a user."""
        # TODO: Implement with repository
        return []

    async def get_session(self, session_id: UUID, user_id: UUID) -> Optional[ChatSessionResponse]:
        """Get a specific session."""
        # TODO: Implement with repository
        return None

    async def delete_session(self, session_id: UUID, user_id: UUID) -> None:
        """Delete a chat session."""
        # TODO: Implement with repository
        pass
