"""Repository layer for the skills module. Only this module's own code may
query the `skills` table directly (AD-1)."""
from uuid import UUID

from sqlalchemy import func, select
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


async def get_skill_by_name_ci(db: AsyncSession, name: str) -> Skill | None:
    """Case-insensitive lookup by name (Story 6.2 AC1's duplicate check).

    The `skills.name` column carries a case-sensitive DB unique constraint
    only (models.py) -- this is the case-insensitive layer the create
    endpoint checks *before* inserting, so a same-name-different-case
    request gets a clean 409 rather than a raw IntegrityError.
    """
    result = await db.execute(select(Skill).where(func.lower(Skill.name) == func.lower(name)))
    return result.scalar_one_or_none()


async def create_skill(db: AsyncSession, skill_data: dict) -> Skill:
    """Create a new Skill.

    Args:
        db: Async database session
        skill_data: Dictionary with Skill fields (name, description, embedding, ever_assigned)

    Returns:
        Created Skill ORM instance with assigned ID
    """
    skill = Skill(**skill_data)
    db.add(skill)
    await db.flush()
    await db.refresh(skill)
    return skill
