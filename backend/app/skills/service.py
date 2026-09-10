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
from app.skills.schemas import CreateSkillRequest, SkillResponse, UpdateSkillRequest

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


async def get_skill_by_id(db: AsyncSession, skill_id: UUID) -> Skill | None:
    """A single Skill (or None), for `content/`'s live content-lookup
    endpoint (Story 6.6) to run its own 404 check without importing
    `skills.repository`/`Skill` directly (AD-1). Mirrors
    get_skill_embedding's existing thin-wrapper shape."""
    return await repository.get_skill_by_id(db, skill_id)


async def mark_ever_assigned(db: AsyncSession, skill_id: UUID) -> None:
    """Set the one-way `ever_assigned` lock flag (Story 6.4 AC1, AD-11
    point 3). Same shape as `content.service.match_content_for_skill`: no
    `current_user`, no auth check here -- the only caller,
    `assignments.service.create_assignment_service`, already gated on
    `require_hr_admin` before reaching this. Idempotent by construction
    (repository.mark_ever_assigned's conditional UPDATE) -- safe to call
    on an already-locked Skill (AC2)."""
    await repository.mark_ever_assigned(db, skill_id)


def _conflict(existing: Skill) -> AppException:
    return AppException(
        status.HTTP_409_CONFLICT,
        error_code="SKILL_NAME_CONFLICT",
        message=f"A skill named '{existing.name}' already exists",
        extra={"existing_skill": {"id": str(existing.id), "name": existing.name}},
    )


def _rename_conflict(existing: Skill) -> AppException:
    # Deliberately no `extra` payload -- AC1 (rename) explicitly rules out
    # the "redirect to existing skill" affordance create's 409 carries
    # (Story 6.2); there's no sensible "use existing skill" merge action
    # when renaming into another Skill's name.
    return AppException(
        status.HTTP_409_CONFLICT,
        error_code="SKILL_NAME_CONFLICT",
        message=f"A skill named '{existing.name}' already exists",
    )


def _not_found() -> AppException:
    return AppException(status.HTTP_404_NOT_FOUND, error_code="SKILL_NOT_FOUND", message="Skill not found")


def _locked() -> AppException:
    # Exact wording from Story 6.3's AC2 -- never a silent no-op, never a
    # 404 (the Skill exists, the action is disallowed and the caller is
    # told why).
    return AppException(
        status.HTTP_403_FORBIDDEN,
        error_code="SKILL_LOCKED",
        message="Skill has been assigned to an Employee and can no longer be edited or deleted",
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


async def update_skill_service(
    db: AsyncSession, *, current_user: CurrentUser, skill_id: UUID, request: UpdateSkillRequest
) -> SkillResponse:
    """Rename/re-describe a Skill (Story 6.3 AC1). HR_ADMIN-only, permanently
    locked once `ever_assigned` is true (AC2, AD-11 point 2 -- a one-way
    gate skills/ enforces locally, never re-derived from assignments/).

    Only fields actually present in the request are touched
    (`exclude_unset=True`) -- omitting a field leaves it unchanged, matching
    standard PATCH semantics. The duplicate check excludes the Skill's own
    row (AC1: resubmitting a Skill's current name is not a conflict with
    itself), and the embedding is only recomputed if `name` or `description`
    actually changes value, not merely because the field was present in the
    request body.
    """
    require_hr_admin(current_user)

    skill = await repository.get_skill_by_id(db, skill_id)
    if skill is None:
        raise _not_found()
    if skill.ever_assigned:
        raise _locked()

    fields = request.model_dump(exclude_unset=True)
    new_name = fields.get("name", skill.name)
    new_description = fields.get("description", skill.description)
    name_changed = "name" in fields and new_name != skill.name
    description_changed = "description" in fields and new_description != skill.description

    if name_changed:
        existing = await repository.get_skill_by_name_ci(db, new_name)
        if existing is not None and existing.id != skill.id:
            raise _rename_conflict(existing)

    updates: dict = {}
    if name_changed:
        updates["name"] = new_name
    if description_changed:
        updates["description"] = new_description
    if name_changed or description_changed:
        updates["embedding"] = embed_text(_build_embedding_text(new_name, new_description))

    if not updates:
        return SkillResponse.model_validate(skill)

    try:
        skill = await repository.update_skill(db, skill, updates)
    except IntegrityError:
        # Same concurrent-rename race as create_skill_service's insert path
        # -- migration 006's functional unique index on lower(name) is the
        # DB-level backstop this pre-check alone can't fully close.
        await db.rollback()
        existing = await repository.get_skill_by_name_ci(db, new_name)
        if existing is None or existing.id == skill_id:
            raise
        raise _rename_conflict(existing) from None

    return SkillResponse.model_validate(skill)


async def delete_skill_service(db: AsyncSession, *, current_user: CurrentUser, skill_id: UUID) -> None:
    """Hard-delete a Skill and its attached Content (Story 6.3 AC3/AC4).
    HR_ADMIN-only, permanently locked once `ever_assigned` is true (AC2)."""
    require_hr_admin(current_user)

    skill = await repository.get_skill_by_id(db, skill_id)
    if skill is None:
        raise _not_found()
    if skill.ever_assigned:
        raise _locked()

    try:
        await repository.delete_skill(db, skill_id)
    except IntegrityError:
        # ever_assigned=false is only as reliable as whatever sets it true
        # (Story 6.4, deferred per this story's review) -- if a real
        # Assignment/Content still references this Skill despite the flag
        # reading false, the DB's own RESTRICT FK is the real authority.
        # Converting that violation to the same 403 a caller would have
        # seen had the flag been accurate is more honest than a raw 500.
        await db.rollback()
        raise _locked() from None
