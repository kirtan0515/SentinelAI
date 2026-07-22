"""
Audit repository - Data access layer for audit logs and attack logs.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.attack import AttackLog


class AuditRepository:
    """Repository for audit and attack log operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_audit_log(self, **kwargs) -> AuditLog:
        """Create an audit log entry."""
        log = AuditLog(**kwargs)
        self.db.add(log)
        await self.db.flush()
        return log

    async def create_attack_log(self, **kwargs) -> AttackLog:
        """Create an attack log entry."""
        log = AttackLog(**kwargs)
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        attack_only: bool = False,
    ) -> list[AuditLog]:
        """Get all audit logs."""
        stmt = select(AuditLog)
        if attack_only:
            stmt = stmt.where(AuditLog.attack_detected == True)
        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get audit logs for a specific user."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_attacks(
        self,
        skip: int = 0,
        limit: int = 50,
        severity: Optional[str] = None,
    ) -> list[AttackLog]:
        """Get attack logs with optional severity filter."""
        stmt = select(AttackLog)
        if severity:
            stmt = stmt.where(AttackLog.severity == severity)
        stmt = stmt.order_by(AttackLog.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_stats(self) -> dict:
        """Get system-wide audit statistics."""
        total_requests = await self.db.scalar(select(func.count(AuditLog.id)))
        blocked_requests = await self.db.scalar(
            select(func.count(AuditLog.id)).where(AuditLog.blocked == True)
        )
        attacks_detected = await self.db.scalar(select(func.count(AttackLog.id)))

        return {
            "total_requests": total_requests or 0,
            "blocked_requests": blocked_requests or 0,
            "attacks_detected": attacks_detected or 0,
            "block_rate": ((blocked_requests / total_requests * 100) if total_requests else 0),
        }

    async def get_user_stats(self, user_id: UUID) -> dict:
        """Get user-specific audit statistics."""
        total = await self.db.scalar(
            select(func.count(AuditLog.id)).where(AuditLog.user_id == user_id)
        )
        blocked = await self.db.scalar(
            select(func.count(AuditLog.id)).where(
                AuditLog.user_id == user_id, AuditLog.blocked == True
            )
        )

        return {
            "total_requests": total or 0,
            "blocked_requests": blocked or 0,
        }
