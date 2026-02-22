"""Repository for Recommendation model."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import Recommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    """Repository for Recommendation model."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Recommendation)
