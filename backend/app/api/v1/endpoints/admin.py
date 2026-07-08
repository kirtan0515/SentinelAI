"""
Admin endpoints for user management and system configuration.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserResponse

router = APIRouter()


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    user_repo = UserRepository(db)
    users = await user_repo.get_all(skip=skip, limit=limit, role=role)
    return users


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    role: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role (admin only)."""
    valid_roles = ["user", "analyst", "admin"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}",
        )

    user_repo = UserRepository(db)
    user = await user_repo.update_role(user_id, role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {"message": f"User role updated to {role}"}


@router.put("/users/{user_id}/disable")
async def disable_user(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Disable a user account (admin only)."""
    user_repo = UserRepository(db)
    user = await user_repo.set_active(user_id, False)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {"message": "User account disabled"}


@router.put("/users/{user_id}/enable")
async def enable_user(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enable a user account (admin only)."""
    user_repo = UserRepository(db)
    user = await user_repo.set_active(user_id, True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {"message": "User account enabled"}


@router.get("/stats")
async def get_system_stats(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get system-wide statistics (admin only)."""
    # TODO: Implement comprehensive stats from audit logs
    return {
        "total_users": 0,
        "active_sessions": 0,
        "total_requests": 0,
        "blocked_attacks": 0,
        "models_available": 4,
    }
