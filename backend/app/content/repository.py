"""Repository layer for the content module. Only this module's own code may query its tables."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import ContentCatalog, Skill


async def get_content_by_id(
    db: AsyncSession, content_id: UUID
) -> ContentCatalog | None:
    """Get a single content item by ID.

    Args:
        db: Async database session
        content_id: UUID of the content item

    Returns:
        ContentCatalog ORM instance or None if not found
    """
    result = await db.execute(select(ContentCatalog).where(ContentCatalog.id == content_id))
    return result.scalar_one_or_none()


async def list_content_by_skill(
    db: AsyncSession, skill_id: UUID
) -> list[ContentCatalog]:
    """Get all content items for a specific skill.

    Args:
        db: Async database session
        skill_id: UUID of the skill

    Returns:
        List of ContentCatalog ORM instances (empty list if no matches)
    """
    result = await db.execute(
        select(ContentCatalog).where(ContentCatalog.skill_id == skill_id)
    )
    return list(result.scalars().all())


async def create_content(db: AsyncSession, content_data: dict) -> ContentCatalog:
    """Create a new content item.

    Args:
        db: Async database session
        content_data: Dictionary with content fields (skill_id, title, description, type, url, embedding, source, content_metadata)

    Returns:
        Created ContentCatalog ORM instance with assigned ID
    """
    content = ContentCatalog(**content_data)
    db.add(content)
    await db.flush()
    await db.refresh(content)
    return content


async def list_all_skills(db: AsyncSession) -> list[Skill]:
    """Read-only enumeration of all Skills, needed by the ingestion job to
    know what to search YouTube for.

    NOTE: `skills` is not in AD-1's "Binds" list -- no module has an
    established owning repository for it yet (Epic 3's Skill Master Data
    story is still backlog). This is a deliberate, narrow, documented
    exception, not a precedent for other cross-table reads. Migrate this
    call to a real Service API once one exists (Story 2.3 Scope Note 2).
    """
    result = await db.execute(select(Skill))
    return list(result.scalars().all())
