"""Repository layer for the content module. Only this module's own code may query its tables."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import ContentCatalog, Skill

# Cosine similarity a Content match must clear to be recommended (Story 2.4,
# AD-7). Plain module constant, not a Settings field -- mirrors
# core/embedding.py's MODEL_NAME/EMBEDDING_DIM (no other module-tunable
# numeric constant is env-configurable either).
SIMILARITY_THRESHOLD = 0.7


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
        select(ContentCatalog)
        .where(ContentCatalog.skill_id == skill_id)
        # Deterministic order: real "best match" ranking now lives in
        # find_best_matching_content() below (Story 2.4); this listing is
        # still used as-is by list_content_for_skill()/ingestion de-dup, so
        # keep it stable across identical requests regardless.
        .order_by(ContentCatalog.ingested_at, ContentCatalog.id)
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


async def get_skill_embedding(db: AsyncSession, skill_id: UUID) -> list[float] | None:
    """Read a Skill's embedding for matching (Story 2.4).

    No `skills/` module/service exists yet (Story 3.2 is still backlog), so
    this reads `Skill` directly from `app.assignments.models` -- the same
    physical-location/logical-ownership split already established for
    `ContentCatalog` above. Read-only, single-column; writes to `skills`
    remain out of scope here.

    Returns:
        The embedding as a plain list[float], or None if the Skill doesn't exist.
    """
    result = await db.execute(select(Skill.embedding).where(Skill.id == skill_id))
    embedding = result.scalar_one_or_none()
    return embedding.tolist() if embedding is not None else None


async def find_best_matching_content(
    db: AsyncSession,
    skill_id: UUID,
    skill_embedding: list[float],
    threshold: float = SIMILARITY_THRESHOLD,
) -> ContentCatalog | None:
    """Filter-then-rank Content for a Skill (Story 2.4, AD-7).

    Pre-filters to the given skill_id, ranks by pgvector cosine distance
    (computed once and reused for the WHERE/ORDER BY clauses below), and
    returns only the single top match if it clears `threshold` similarity.
    `ContentCatalog.id` is an explicit tie-break so ties resolve
    deterministically (AC6) rather than by incidental row-fetch order.

    Returns:
        The best-matching ContentCatalog ORM instance, or None if no
        Content for this skill clears the threshold (including when the
        skill has zero Content rows at all).
    """
    distance = ContentCatalog.embedding.cosine_distance(skill_embedding)
    stmt = (
        select(ContentCatalog)
        .where(ContentCatalog.skill_id == skill_id, distance < (1 - threshold))
        .order_by(distance.asc(), ContentCatalog.id.asc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
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
