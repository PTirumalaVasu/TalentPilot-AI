"""Repository layer for the skills module. Only this module's own code may
query the `skills` table directly (AD-1)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.skills.models import Skill


async def list_all_skills(db: AsyncSession) -> list[Skill]:
    """Read-only enumeration of every Skill.

    Relocated from `content/repository.py` (Story 2.3's documented, narrow
    AD-1 exception -- `skills` had no owning module yet) now that `skills/`
    is the table's real owner (AD-11). `content/`'s batch ingestion job
    (needs the full list to know what to search YouTube for) reaches this
    via `skills.service.list_all_skills()`, never this repository function
    directly.
    """
    result = await db.execute(select(Skill))
    return list(result.scalars().all())


async def get_skill_embedding(db: AsyncSession, skill_id: UUID) -> list[float] | None:
    """Read a single Skill's embedding for semantic content matching.

    Relocated from `content/repository.py` (Story 2.4's documented,
    physical-location/logical-ownership split -- Skill lived in
    `assignments/models.py` with no owning module yet). Read-only,
    single-column; writes to `skills` remain out of scope here.

    Returns:
        The embedding as a plain list[float], or None if the Skill doesn't exist.
    """
    result = await db.execute(select(Skill.embedding).where(Skill.id == skill_id))
    embedding = result.scalar_one_or_none()
    return embedding.tolist() if embedding is not None else None
