"""Service layer for the skills module. Cross-module callers must go
through here (AD-1) -- `content/` no longer imports `Skill` or queries the
`skills` table directly (AD-11)."""
import logging
from uuid import UUID

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.auth.service import require_hr_admin
from app.core.embedding import embed_text
from app.core.errors import AppException
from app.skills import repository
from app.skills.models import Skill
from app.skills.schemas import CreateSkillRequest, SkillResponse

logger = logging.getLogger(__name__)

# Same safe character budget as content/service.py's _build_embedding_text
# (Story 2.2's truncation fix) -- kept as an independent module constant
# rather than imported from content/, since skills/ must not depend on
# content/ (AD-8: dependencies point Content -> Skills, never back).
EMBEDDING_TEXT_MAX_CHARS = 1000


def _build_embedding_text(name: str, description: str | None) -> str:
    """Build the text fed to embed_text() for a Skill, truncated to a safe
    character budget. Mirrors content/'s existing embedding-on-write
    pattern exactly (AD-11 point 4) so Story 6.2 (create) and Story 6.3
    (rename) share one implementation instead of each re-deriving their
    own -- this is the "embedding-write helper" this story is scoped to
    provide; the create/rename endpoints that call it are out of scope
    here."""
    raw = f"{name}: {description or ''}"
    if len(raw) > EMBEDDING_TEXT_MAX_CHARS:
        logger.debug(
            "Truncating embedding text from %d to %d chars for name=%r",
            len(raw), EMBEDDING_TEXT_MAX_CHARS, name,
        )
    return raw[:EMBEDDING_TEXT_MAX_CHARS]


async def list_all_skills(db: AsyncSession) -> list[Skill]:
    """Read-only enumeration of every Skill (the Service API `content/`'s
    batch ingestion job now calls instead of querying `skills` directly,
    AD-11 point 1)."""
    return await repository.list_all_skills(db)


async def get_skill_embedding(db: AsyncSession, skill_id: UUID) -> list[float] | None:
    """A single Skill's embedding, for `content/`'s semantic matching
    (Story 2.4) to consume without importing `Skill` itself."""
    return await repository.get_skill_embedding(db, skill_id)


def _conflict(existing: Skill) -> AppException:
    return AppException(
        status.HTTP_409_CONFLICT,
        error_code="SKILL_NAME_CONFLICT",
        message=f"A skill named '{existing.name}' already exists",
        extra={"existing_skill": {"id": str(existing.id), "name": existing.name}},
    )


async def create_skill_service(
    db: AsyncSession, *, current_user: CurrentUser, request: CreateSkillRequest
) -> SkillResponse:
    """Create a new Skill (Story 6.2, FR-20). HR_ADMIN-only (AD-6), matching
    assignments/service.py's established service-layer require_hr_admin
    gate pattern rather than a router-level Depends.

    Case-insensitive duplicate check first (AC1) -- returns a 409 with the
    existing Skill's id/name for the common (non-racing) case. A functional
    unique index on lower(name) (migration 006, code review 2026-09-09)
    backstops this at the DB level for the concurrent-request race the
    pre-check alone can't close: if two requests for the same
    case-insensitively-equal name interleave between the pre-check and the
    insert, the second insert's IntegrityError is caught below and served
    the same clean 409 rather than propagating as a raw 500.

    Embedding is computed inline here via embed_text(_build_embedding_text(...)),
    mirroring content/service.py's manual_seed_content -- Story 6.1's own
    precedent for this exact composition (not a wrapper function).

    No explicit commit -- repository.create_skill() only flushes, per
    core/db.py::get_db's documented convention (individual repository/
    service functions flush, not commit; get_db commits once the route
    handler completes)."""
    require_hr_admin(current_user)

    existing = await repository.get_skill_by_name_ci(db, request.name)
    if existing is not None:
        raise _conflict(existing)

    embedding = embed_text(_build_embedding_text(request.name, request.description))
    try:
        skill = await repository.create_skill(
            db,
            {
                "name": request.name,
                "description": request.description,
                "embedding": embedding,
                "ever_assigned": False,
            },
        )
    except IntegrityError:
        await db.rollback()
        existing = await repository.get_skill_by_name_ci(db, request.name)
        if existing is None:
            raise
        raise _conflict(existing) from None

    return SkillResponse.model_validate(skill)
