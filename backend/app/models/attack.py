"""
Attack log model for security incident tracking.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AttackLog(Base):
    """Log of detected security attacks."""

    __tablename__ = "attack_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    attack_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # prompt_injection, jailbreak, data_leakage
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # low, medium, high, critical
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    original_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    detection_details: Mapped[str] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # blocked, flagged, allowed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
