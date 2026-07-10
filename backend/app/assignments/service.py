"""Service layer for the assignments module. Cross-module callers must go through here (AD-1)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.repository import _parse_user_id, create_assignment
from app.assignments.schemas import AssignmentResponse, AssignmentStatus, CreateAssignmentRequest
from app.auth.schemas import CurrentUser
from app.auth.service import require_hr_admin


async def create_assignment_service(
    session: AsyncSession, *, current_user: CurrentUser, request: CreateAssignmentRequest
) -> AssignmentResponse:
    """Creates an Assignment on behalf of an HR Admin caller (AC4). Status and
    Provenance cover only the trivial no-progress-yet case (AC6) — a
    freshly created Assignment always has no skill_progress row yet.
    content_id is not yet wired here (AC3's schema has no content_id input);
    Story 3.4/3.5 add the AI-matched content lookup on top of this function."""
    require_hr_admin(current_user)

    assignment = await create_assignment(
        session,
        employee_id=request.employee_id,
        skill_id=request.skill_id,
        content_id=None,
        assigned_by=_parse_user_id(current_user),
    )

    return AssignmentResponse(
        id=assignment.id,
        employee_id=assignment.employee_id,
        skill_id=assignment.skill_id,
        content_id=assignment.content_id,
        assigned_at=assignment.assigned_at,
        assigned_by=assignment.assigned_by,
        status=AssignmentStatus.NOT_STARTED,
        provenance="Assigned · Awaiting first watch",
    )
