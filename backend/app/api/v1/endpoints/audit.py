"""
Audit log endpoints for viewing request history and security events.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.audit_repository import AuditRepository

router = APIRouter()


@router.get("/logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    attack_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit logs. Admins see all, users see their own."""
    audit_repo = AuditRepository(db)

    if current_user.role == "admin":
        logs = await audit_repo.get_all(
            skip=skip, limit=limit, attack_only=attack_only
        )
    else:
        logs = await audit_repo.get_by_user(
            user_id=current_user.id, skip=skip, limit=limit
        )

    return logs


@router.get("/attacks")
async def get_attack_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get attack logs (admin and analyst only)."""
    if current_user.role not in ["admin", "analyst"]:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    audit_repo = AuditRepository(db)
    attacks = await audit_repo.get_attacks(
        skip=skip, limit=limit, severity=severity
    )
    return attacks


@router.get("/stats")
async def get_audit_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit statistics summary."""
    audit_repo = AuditRepository(db)

    if current_user.role == "admin":
        stats = await audit_repo.get_stats()
    else:
        stats = await audit_repo.get_user_stats(current_user.id)

    return stats
