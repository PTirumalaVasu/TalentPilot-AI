"""Repository layer for the assignments module. Only this module's own code may query its tables."""
import uuid
from datetime import datetime, timezone

from fastapi import status
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.assignments.models import Assignment, Employee, Skill
from app.auth.schemas import CurrentUser, Role
from app.core.errors import AppException


def _parse_user_id(current_user: CurrentUser) -> uuid.UUID:
    """CurrentUser.user_id is only guaranteed non-empty (auth/service.py) —
    not guaranteed UUID-shaped. Today's mock accounts always issue real
    Employee UUIDs (Story 3.1 code-review fix, core/seed_ids.py), but nothing
    upstream enforces that for a future non-mock auth source. Fail as a clean
    400 here rather than an uncaught ValueError -> generic 500."""
    try:
        return uuid.UUID(current_user.user_id)
    except (ValueError, AttributeError, TypeError) as exc:
        raise AppException(
            status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_USER_ID",
            message="Session user_id is not a valid identifier",
        ) from exc


async def get_employee_by_id(session: AsyncSession, employee_id: uuid.UUID) -> Employee | None:
    """Single-employee lookup by primary key -- used by the auth module's
    GET /api/auth/me (via get_employee_by_id_service, AD-1) to resolve a
    session's own display name/email. `employees` is owned by this module,
    so cross-module callers must go through the service layer for this too."""
    return await session.get(Employee, employee_id)


async def list_employees(session: AsyncSession, *, search: str | None = None) -> list[Employee]:
    """Read-only employee directory listing — not scoped by caller identity;
    any authenticated session (EMPLOYEE or HR_ADMIN) can see the roster. This
    is distinct from Assignment reads, which Story 1.3/1.5's hard-scoping
    guidance governs; the employee directory itself has no such requirement."""
    stmt = select(Employee)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Employee.name.ilike(pattern), Employee.email.ilike(pattern)))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_skills(session: AsyncSession, *, search: str | None = None) -> list[Skill]:
    """Read-only skill directory listing for the assignment modal's Step 2
    (Skill) combobox — no scoping (skills aren't employee-owned data)."""
    stmt = select(Skill)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Skill.name.ilike(pattern), Skill.description.ilike(pattern)))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_assignment(
    session: AsyncSession,
    *,
    employee_id: uuid.UUID,
    skill_id: uuid.UUID,
    content_id: uuid.UUID | None,
    assigned_by: uuid.UUID,
) -> Assignment:
    """Insert a new Assignment row. (employee_id, skill_id) is intentionally not
    unique-constrained (AC2) — each call creates a distinct row even if the pair
    already exists."""
    assignment = Assignment(
        employee_id=employee_id,
        skill_id=skill_id,
        content_id=content_id,
        assigned_by=assigned_by,
    )
    session.add(assignment)
    await session.flush()
    return assignment


async def find_existing_assignment(
    session: AsyncSession, *, employee_id: uuid.UUID, skill_id: uuid.UUID
) -> list[Assignment]:
    """Returns all existing Assignment rows for (employee_id, skill_id), for
    duplicate-detection (Story 3.4) — does not enforce uniqueness. Unordered:
    do not treat result[0] as "the" existing assignment (AC2 permits multiple
    intentional re-assignments of the same pair). Excludes soft-deleted rows
    (Story 3.7) — a deleted prior Assignment must not surface as a duplicate
    blocking/flagging a fresh re-assignment of the same pair."""
    result = await session.execute(
        select(Assignment).where(
            Assignment.employee_id == employee_id,
            Assignment.skill_id == skill_id,
            Assignment.active.is_(True),
        )
    )
    return list(result.scalars().all())


async def list_assignments_for_employee(
    session: AsyncSession,
    *,
    current_user: CurrentUser,
    requested_employee_id: uuid.UUID | None = None,
) -> list[Assignment]:
    """Hard-scoped per Story 1.3's AC6 forward-reference: EMPLOYEE sessions are
    always scoped to their own employee_id in the WHERE clause, silently
    ignoring any requested_employee_id override. HR_ADMIN sessions are
    unrestricted; requested_employee_id acts as a real filter for them, not a
    spoof-defense. Excludes soft-deleted rows (Story 3.7) -- this feeds
    Content Discovery (FR-4), so a deleted Assignment disappears from the
    Employee's own list too, not just HR's."""
    stmt = select(Assignment).options(selectinload(Assignment.skill)).where(Assignment.active.is_(True))

    if current_user.role == Role.EMPLOYEE:
        stmt = stmt.where(Assignment.employee_id == _parse_user_id(current_user))
    elif requested_employee_id is not None:
        stmt = stmt.where(Assignment.employee_id == requested_employee_id)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_assignments_for_dashboard(session: AsyncSession) -> list[Assignment]:
    """All Assignments org-wide with employee/skill/content/progress
    eager-loaded, for the HR dashboard read (Story 3.5). Unlike
    list_assignments_for_employee, this is unconditionally unrestricted here
    — the HR-only gate lives in the service layer
    (list_assignment_rows_for_dashboard_service), matching
    duplicate_check_service's established pattern — since this function has
    no other/future EMPLOYEE-facing caller to protect against.

    `content`/`progress` are eager-loaded (not just `employee`/`skill`) so
    the service layer can derive real per-row Status/Progress via
    `ProgressService.derive_dashboard_status_and_percent` +
    `ProgressRepository.get_video_duration` without N+1 queries.

    Excludes soft-deleted rows (Story 3.7)."""
    stmt = (
        select(Assignment)
        .where(Assignment.active.is_(True))
        .options(
            selectinload(Assignment.employee),
            selectinload(Assignment.skill),
            selectinload(Assignment.content),
            selectinload(Assignment.progress),
        )
        .order_by(Assignment.assigned_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


class AssignmentPage:
    """Paginated assignment list response."""

    def __init__(self, assignments: list[Assignment], total_count: int):
        self.assignments = assignments
        self.total_count = total_count


async def list_assignments_for_hr(
    session: AsyncSession,
    *,
    hr_admin_id: uuid.UUID,
    page: int = 1,
    page_size: int = 50,
) -> AssignmentPage:
    """Fetch all Assignments created by an HR Admin with pagination.

    Returns assignments sorted by assigned_at DESC (newest first).
    Joins with Employee and Skill for eager loading of relationships.

    This is the function behind the live `GET /api/dashboard` path
    (DashboardService.get_dashboard_assignments -> AssignmentsService.list_assignments_for_hr
    -> here), so excluding soft-deleted rows (Story 3.7) here -- in both the
    count and the page query -- is what keeps pagination counts and the
    dashboard grid correct. The filter is expressed once (`base_filters`,
    code review patch 4) rather than duplicated across both statements, so a
    future edit to one can't silently drift from the other.
    """
    from sqlalchemy import desc
    from sqlalchemy.orm import selectinload

    base_filters = (Assignment.assigned_by == hr_admin_id, Assignment.active.is_(True))

    # Count total assignments for this HR Admin
    count_stmt = select(func.count(Assignment.id)).where(*base_filters)
    count_result = await session.execute(count_stmt)
    total_count = count_result.scalar() or 0

    # Fetch paginated assignments with eager-loaded relationships
    stmt = (
        select(Assignment)
        .where(*base_filters)
        .order_by(desc(Assignment.assigned_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .options(
            selectinload(Assignment.employee),
            selectinload(Assignment.skill),
            selectinload(Assignment.content),
        )
    )

    result = await session.execute(stmt)
    assignments = list(result.scalars().all())

    return AssignmentPage(assignments=assignments, total_count=total_count)


async def soft_delete_assignment(
    session: AsyncSession, *, assignment_id: uuid.UUID, deleted_by: uuid.UUID
) -> bool:
    """Atomically soft-deletes an Assignment via a conditional
    `UPDATE ... WHERE active = true` (Story 3.7 code review patch 1) --
    never physically removes the row; skill_progress/assignment_overrides
    rows referencing it are untouched, per the locked
    sprint-change-proposal-2026-07-13.md decision (soft delete, mirroring
    assignment_overrides.active from Story 5.5b).

    The DB-level conditional UPDATE, not a Python-side read-then-write
    check, is what makes double-delete idempotency (AC7) race-safe: two
    concurrent DELETE requests for the same assignment_id can no longer
    both observe active=True and both overwrite deleted_at/deleted_by --
    only the first to commit actually changes anything; the second's
    UPDATE matches zero rows and is a true no-op. Caller is responsible
    for scoping/access-checking the assignment before calling this (see
    get_assignment_scoped_to_hr_admin).

    Returns True if this call performed the soft-delete, False if the
    Assignment was already inactive (idempotent no-op)."""
    result = await session.execute(
        update(Assignment)
        .where(Assignment.id == assignment_id, Assignment.active.is_(True))
        .values(active=False, deleted_at=datetime.now(timezone.utc), deleted_by=deleted_by)
    )
    await session.flush()
    return result.rowcount > 0


async def get_assignment_scoped_to_hr_admin(
    session: AsyncSession, *, assignment_id: uuid.UUID, hr_admin_id: uuid.UUID
) -> Assignment | None:
    """Hard-scoped single-assignment fetch for the Provenance Drill-Down
    endpoint (Story 5.2, AC6) — mirrors `list_assignments_for_hr`'s
    `assigned_by == hr_admin_id` scoping (AD-6), but for one row instead of a
    page. Returns `None` for both "doesn't exist" and "exists but a
    different HR Admin created it" — the caller raises a uniform 403 for
    both, never leaking which case it was (same pattern as Story 4-5's
    `get_assignment_with_scope`)."""
    stmt = (
        select(Assignment)
        .where(Assignment.id == assignment_id, Assignment.assigned_by == hr_admin_id)
        .options(
            selectinload(Assignment.employee),
            selectinload(Assignment.skill),
            selectinload(Assignment.content),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
