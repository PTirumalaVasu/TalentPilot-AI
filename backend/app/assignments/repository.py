"""Repository layer for the assignments module. Only this module's own code may query its tables."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import Assignment
from app.auth.schemas import CurrentUser, Role


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
    duplicate-detection (Story 3.4) — does not enforce uniqueness."""
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
    stmt = select(Assignment)

    if current_user.role == Role.EMPLOYEE:
        stmt = stmt.where(Assignment.employee_id == uuid.UUID(current_user.user_id))
    elif requested_employee_id is not None:
        stmt = stmt.where(Assignment.employee_id == requested_employee_id)

    result = await session.execute(stmt)
    return list(result.scalars().all())
