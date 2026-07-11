"""Repository layer for the assignments module. Only this module's own code may query its tables."""
import uuid

from fastapi import status
from sqlalchemy import or_, select
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
    intentional re-assignments of the same pair)."""
    result = await session.execute(
        select(Assignment).where(Assignment.employee_id == employee_id, Assignment.skill_id == skill_id)
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
    spoof-defense."""
    stmt = select(Assignment).options(selectinload(Assignment.skill))

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
    `ProgressRepository.get_video_duration` without N+1 queries."""
    stmt = (
        select(Assignment)
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
