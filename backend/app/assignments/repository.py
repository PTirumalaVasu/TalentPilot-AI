"""Repository layer for the assignments module. Only this module's own code may query its tables."""
import uuid

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.assignments.models import Assignment
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
