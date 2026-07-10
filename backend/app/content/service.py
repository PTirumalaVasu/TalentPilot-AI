"""Service layer for the content module. Cross-module callers must go through here (AD-1)."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.content import repository
from app.content.schemas import ContentResponse


async def get_content(db: AsyncSession, content_id: UUID) -> ContentResponse | None:
    """Get a single content item by ID.

    Args:
        db: Async database session
        content_id: UUID of the content item

    Returns:
        ContentResponse (Pydantic) or None if not found
    """
    content_orm = await repository.get_content_by_id(db, content_id)
    if content_orm is None:
        return None

    return ContentResponse.model_validate(content_orm)


async def list_content_for_skill(
    db: AsyncSession, skill_id: UUID
) -> list[ContentResponse]:
    """Get all content items for a specific skill.

    Args:
        db: Async database session
        skill_id: UUID of the skill

    Returns:
        List of ContentResponse (Pydantic), empty list if no matches
    """
    content_orms = await repository.list_content_by_skill(db, skill_id)
    return [ContentResponse.model_validate(orm) for orm in content_orms]
