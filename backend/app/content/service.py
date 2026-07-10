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


async def match_content_for_skill(db: AsyncSession, skill_id: UUID) -> ContentResponse | None:
    """Recommend the single best-matching Content for a Skill (Story 2.4).

    Public entrypoint for the filter-then-rank matching logic -- the
    intended caller is a future assignment-creation flow (Story 3.4/3.5),
    which today always passes content_id=None (see
    app.assignments.service.create_assignment_service). A None result here
    means "no recommendation yet", not an error -- callers should treat it
    that way, not surface it to HR as a failure.

    Returns:
        ContentResponse for the best match, or None if the Skill doesn't
        exist or no Content clears the similarity threshold.
    """
    skill_embedding = await repository.get_skill_embedding(db, skill_id)
    if skill_embedding is None:
        return None

    content_orm = await repository.find_best_matching_content(db, skill_id, skill_embedding)
    if content_orm is None:
        return None

    return ContentResponse.model_validate(content_orm)
