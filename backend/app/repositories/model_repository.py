"""
Model configuration repository.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_config import ModelConfig


class ModelRepository:
    """Repository for AI model configuration operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_enabled(self) -> list[ModelConfig]:
        """Get all enabled models."""
        stmt = select(ModelConfig).where(ModelConfig.is_enabled == True)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_default(self) -> Optional[ModelConfig]:
        """Get the default model."""
        stmt = select(ModelConfig).where(ModelConfig.is_default == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def set_default(self, model_id: UUID) -> Optional[ModelConfig]:
        """Set a model as the default."""
        # Unset current default
        await self.db.execute(
            update(ModelConfig).values(is_default=False)
        )
        # Set new default
        stmt = (
            update(ModelConfig)
            .where(ModelConfig.id == model_id)
            .values(is_default=True)
            .returning(ModelConfig)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
