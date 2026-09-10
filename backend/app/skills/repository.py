"""Repository layer for the skills module. Only this module's own code may
query the `skills` table directly (AD-1)."""
from uuid import UUID

from sqlalchemy import delete, func, select, update
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


async def get_skill_by_id(db: AsyncSession, skill_id: UUID) -> Skill | None:
    """Lookup by primary key (Story 6.3's edit/delete lock check needs the
    current row -- name, description, embedding, ever_assigned -- before
    deciding whether the request is even allowed)."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    return result.scalar_one_or_none()


async def update_skill(db: AsyncSession, skill: Skill, updates: dict) -> Skill:
    """Apply field updates to an already-loaded Skill and persist them
    (Story 6.3 AC1). Caller (service) has already resolved which fields to
    set and, if `embedding` is included, recomputed it."""
    for field, value in updates.items():
        setattr(skill, field, value)
    await db.flush()
    await db.refresh(skill)
    return skill


async def delete_skill(db: AsyncSession, skill_id: UUID) -> None:
    """Hard delete a Skill row (Story 6.3 AC3).

    Issued as a Core-level `delete()` rather than `db.delete(<ORM object>)`
    so the ORM's unit-of-work never loads/touches the `content_items`
    relationship. `content_catalog.skill_id`'s FK now carries
    `ON DELETE CASCADE` (migration 007) -- deleting the Skill row also
    deletes its attached Content rows atomically at the DB level (AC4),
    without `skills/` ever querying the `content_catalog` table directly
    (AD-1/AD-8: `skills/` must not depend on `content/`).
    """
    await db.execute(delete(Skill).where(Skill.id == skill_id))


async def mark_ever_assigned(db: AsyncSession, skill_id: UUID) -> None:
    """Set a Skill's one-way `ever_assigned` lock flag (Story 6.4 AC1,
    AD-11 point 3). `assignments/` calls this after successfully creating
    an Assignment for the Skill.

    A single conditional UPDATE, not a SELECT-then-UPDATE: matching zero
    rows (already True, or a nonexistent skill_id) is a silent, idempotent
    success (AC2) -- never raises.

    No trailing flush(): this is a Core-level UPDATE, already sent to the
    DB synchronously by execute() -- there's no pending ORM-tracked object
    for flush() to synchronize (unlike update_skill's pattern, which
    mutates a loaded ORM object and needs it).
    """
    await db.execute(
        update(Skill).where(Skill.id == skill_id, Skill.ever_assigned.is_(False)).values(ever_assigned=True)
    )
