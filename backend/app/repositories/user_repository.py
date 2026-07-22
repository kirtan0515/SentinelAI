"""
User repository - Data access layer for user operations.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository pattern for User model database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        email: str,
        username: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        role: str = "user",
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: str | UUID) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        role: Optional[str] = None,
    ) -> list[User]:
        """Get all users with optional filtering."""
        stmt = select(User)
        if role:
            stmt = stmt.where(User.role == role)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        """Update user fields."""
        stmt = update(User).where(User.id == user_id).values(**kwargs).returning(User)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        stmt = update(User).where(User.id == user_id).values(last_login=datetime.now(timezone.utc))
        await self.db.execute(stmt)

    async def update_password(self, user_id: UUID, hashed_password: str) -> None:
        """Update user password."""
        stmt = update(User).where(User.id == user_id).values(hashed_password=hashed_password)
        await self.db.execute(stmt)

    async def update_role(self, user_id: UUID, role: str) -> Optional[User]:
        """Update user role."""
        return await self.update(user_id, role=role)

    async def set_active(self, user_id: UUID, is_active: bool) -> Optional[User]:
        """Enable or disable a user account."""
        return await self.update(user_id, is_active=is_active)
