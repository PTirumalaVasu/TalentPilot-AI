"""Service layer for the assignments module. Cross-module callers must go through here (AD-1)."""
import re

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.repository import _parse_user_id, create_assignment, list_assignments_for_employee
from app.assignments.schemas import (
    AssignmentContentItem,
    AssignmentResponse,
    AssignmentStatus,
    CreateAssignmentRequest,
    MyAssignmentsResponse,
)
from app.auth.schemas import CurrentUser, Role
from app.auth.service import require_hr_admin
from app.content.service import match_content_for_skill
from app.core.errors import AppException
from app.progress.service import ProgressService

_ISO8601_DURATION_RE = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


def _parse_iso8601_duration_seconds(duration: str | None) -> int | None:
    """Best-effort parse of a YouTube-API ISO-8601 duration (e.g. "PT28M33S")
    into whole seconds. Returns None for missing/unparseable input -- a video
    with an unparseable duration simply can't derive a COMPLETED status
    (Scope Note 6, ProgressService.derive_status's duration_seconds=None path),
    it never raises."""
    if not duration:
        return None
    match = _ISO8601_DURATION_RE.match(duration)
    if not match:
        return None
    hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds


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


async def list_my_assignments(session: AsyncSession, *, current_user: CurrentUser) -> MyAssignmentsResponse:
    """Content Discovery grid data (Story 2.5, FR-4). EMPLOYEE-only --
    HR_ADMIN is rejected with 403, not silently given the unrestricted branch
    list_assignments_for_employee would otherwise offer it. This gate is
    load-bearing for AD-2: looping the per-assignment ProgressService.get_progress
    coaching-shaped read across an HR_ADMIN's unrestricted, org-wide assignment
    set would be the exact bulk/cross-employee raw-progress read AD-2 bans,
    even though each individual call is single-assignment-shaped. Do not
    remove this check to "simplify" the route."""
    if current_user.role != Role.EMPLOYEE:
        raise AppException(
            status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN_NOT_EMPLOYEE",
            message="This action requires an Employee session",
        )

    assignments = await list_assignments_for_employee(session, current_user=current_user)

    items: list[AssignmentContentItem] = []
    for assignment in assignments:
        content = await match_content_for_skill(session, assignment.skill_id)
        progress = await ProgressService.get_progress(session, assignment.id)
        watch_position = progress.watch_position if progress is not None else 0

        duration_seconds = None
        if content is not None and content.metadata:
            duration_seconds = _parse_iso8601_duration_seconds(content.metadata.get("duration"))

        derived_status = ProgressService.derive_status(watch_position, duration_seconds)
        group = "TO_START" if derived_status == "NOT_STARTED" else "IN_PROGRESS"

        items.append(
            AssignmentContentItem(
                assignment_id=assignment.id,
                skill_id=assignment.skill_id,
                skill_name=assignment.skill.name,
                content=content,
                watch_position=watch_position,
                status=derived_status,
                group=group,
            )
        )

    in_progress_count = sum(1 for item in items if item.group == "IN_PROGRESS")
    to_start_count = sum(1 for item in items if item.group == "TO_START")

    return MyAssignmentsResponse(
        total=len(items),
        in_progress_count=in_progress_count,
        to_start_count=to_start_count,
        assignments=items,
    )
