"""Service layer for the assignments module. Cross-module callers must go through here (AD-1)."""
import re

from fastapi import status
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.repository import (
    AssignmentPage,
    _parse_user_id,
    create_assignment,
    find_existing_assignment,
    list_assignments_for_dashboard,
    list_assignments_for_hr,
    list_employees,
    list_skills,
)
from app.assignments.schemas import (
    AssignmentResponse,
    AssignmentStatus,
    CreateAssignmentRequest,
    DashboardAssignmentRow,
    EmployeeResponse,
    SkillResponse,
)
from app.auth.schemas import CurrentUser
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
from app.progress.repository import ProgressRepository
from app.progress.service import ProgressService


class AssignmentsService:
    """Service-layer wrapper for assignments business logic."""

    @staticmethod
    async def list_assignments_for_hr(
        session: AsyncSession,
        hr_admin_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> AssignmentPage:
        """Fetch paginated assignments for an HR Admin (cross-module API per AD-1)."""
        return await list_assignments_for_hr(
            session, hr_admin_id=hr_admin_id, page=page, page_size=page_size
        )


async def list_employees_service(session: AsyncSession, *, search: str | None = None) -> list[EmployeeResponse]:
    employees = await list_employees(session, search=search)
    return [EmployeeResponse.model_validate(employee) for employee in employees]

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


async def list_skills_service(session: AsyncSession, *, search: str | None = None) -> list[SkillResponse]:
    skills = await list_skills(session, search=search)
    return [SkillResponse.model_validate(skill) for skill in skills]


async def create_assignment_service(
    session: AsyncSession, *, current_user: CurrentUser, request: CreateAssignmentRequest
) -> AssignmentResponse:
    """Creates an Assignment on behalf of an HR Admin caller (AC4). Status and
    Provenance cover only the trivial no-progress-yet case (AC6) — a
    freshly created Assignment always has no skill_progress row yet.
    content_id (Story 3.4) is optional — None when no content matched or
    [Assign without content] was used."""
    require_hr_admin(current_user)

    assignment = await create_assignment(
        session,
        employee_id=request.employee_id,
        skill_id=request.skill_id,
        content_id=request.content_id,
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


async def duplicate_check_service(
    session: AsyncSession, *, current_user: CurrentUser, employee_id: uuid.UUID, skill_id: uuid.UUID
) -> list[AssignmentResponse]:
    """Existing Assignment(s) for an (employee_id, skill_id) pair, for the
    modal's Step 2→3 duplicate-detection (Story 3.4 AC5). HR_ADMIN-only
    (code-review fix): unlike the read-only employee/skill directories, this
    reveals whether a specific Employee already has a specific Skill
    assigned — an EMPLOYEE session has no legitimate need to probe another
    employee's assignment existence."""
    require_hr_admin(current_user)
    existing = await find_existing_assignment(session, employee_id=employee_id, skill_id=skill_id)
    return [
        AssignmentResponse(
            id=a.id,
            employee_id=a.employee_id,
            skill_id=a.skill_id,
            content_id=a.content_id,
            assigned_at=a.assigned_at,
            assigned_by=a.assigned_by,
            status=AssignmentStatus.NOT_STARTED,
            provenance="Assigned · Awaiting first watch",
        )
        for a in existing
    ]


async def list_assignment_rows_for_dashboard_service(
    session: AsyncSession, *, current_user: CurrentUser
) -> list[DashboardAssignmentRow]:
    """HR-only read composition for the dashboard list (Story 3.5, expanded
    at user request to derive real per-row Status/Progress rather than the
    original placeholder). Derivation itself lives in `progress/`
    (AD-3: sole derivation authority) — this function only composes the
    already-eager-loaded `employee`/`skill`/`content`/`progress`
    relationships and calls into it, it does not compute anything itself.

    Still not the final Epic 5 grid: no Provenance drill-down (Story 5.2),
    no Needs-Attention staleness threshold (Story 5.3), no live 10-15s
    auto-polling for existing rows (Story 5.4)."""
    require_hr_admin(current_user)
    assignments = await list_assignments_for_dashboard(session)
    rows = []
    for a in assignments:
        watch_seconds = a.progress.watch_position if a.progress else 0
        duration_seconds = ProgressRepository.get_video_duration(a)
        status, percent = ProgressService.derive_dashboard_status_and_percent(watch_seconds, duration_seconds)
        provenance = (
            "Assigned · Awaiting first watch" if a.progress is None else f"Verified · {percent}% watched"
        )
        rows.append(
            DashboardAssignmentRow(
                id=a.id,
                employee_id=a.employee_id,
                employee_name=a.employee.name,
                skill_id=a.skill_id,
                skill_name=a.skill.name,
                assigned_at=a.assigned_at,
                status=status,
                progress_percent=percent,
                provenance=provenance,
            )
        )
    return rows


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
