"""Service layer for the assignments module. Cross-module callers must go through here (AD-1)."""
from fastapi import HTTPException, status
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import Assignment
from app.assignments.repository import (
    AssignmentPage,
    _parse_user_id,
    create_assignment,
    find_existing_assignment,
    get_assignment_scoped_to_hr_admin,
    list_assignments_for_dashboard,
    list_assignments_for_employee,
    list_assignments_for_hr,
    list_employees,
    list_skills,
    soft_delete_assignment,
)
from app.assignments.schemas import (
    AssignmentContentItem,
    AssignmentResponse,
    AssignmentStatus,
    CreateAssignmentRequest,
    DashboardAssignmentRow,
    DrillDownResponse,
    EmployeeResponse,
    MyAssignmentsResponse,
    SetOverrideRequest,
    SkillResponse,
)
from app.auth.schemas import CurrentUser, Role
from app.auth.service import require_hr_admin
from app.content.service import match_content_for_skill
from app.core.errors import AppException
from app.progress.repository import ProgressRepository
from app.progress.service import ProgressService, ProvenanceDetail


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


def _provenance_detail_to_drill_down_response(assignment: Assignment, detail: ProvenanceDetail) -> DrillDownResponse:
    """Shared builder for DrillDownResponse from a ProvenanceDetail (AR-3) --
    used by both the read-only drill-down GET (get_drill_down_service) and
    the override mutation (set_override_service, Story 5.5), so the two
    endpoints can never disagree on response shape for the same state."""
    underlying = detail.underlying_signal

    return DrillDownResponse(
        assignment_id=assignment.id,
        employee_name=assignment.employee.name if assignment.employee else "Unknown",
        skill_name=assignment.skill.name if assignment.skill else "Unknown",
        status=detail.status,
        status_percentage=detail.percentage,
        provenance=detail.provenance,
        last_updated=detail.last_updated,
        override_set_by_name=detail.override_set_by_name,
        override_reason=detail.override_reason,
        override_set_at=detail.override_set_at,
        underlying_provenance=underlying.provenance if underlying else None,
        underlying_status=underlying.status if underlying else None,
        underlying_status_percentage=underlying.percentage if underlying else None,
    )


async def get_drill_down_service(
    session: AsyncSession, *, current_user: CurrentUser, assignment_id: uuid.UUID
) -> DrillDownResponse:
    """Provenance Drill-Down read (Story 5.2, FR-9). HR_ADMIN-only
    (require_hr_admin, matching this file's established pattern of gating in
    the service layer rather than the router), hard-scoped to assignments
    the caller created (assigned_by == current_user.user_id) via
    get_assignment_scoped_to_hr_admin -- mirrors Story 4-5's
    get_assignment_with_scope 403-on-mismatch pattern: not-found and
    not-owned both raise the same 403, never leaking which case it was
    (AC6, AD-2)."""
    require_hr_admin(current_user)

    assignment = await get_assignment_scoped_to_hr_admin(
        session, assignment_id=assignment_id, hr_admin_id=_parse_user_id(current_user)
    )
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this assignment")

    progress = await ProgressRepository.get_progress_for_assignment(session, assignment_id)
    override = await ProgressRepository.get_active_override_for_assignment(session, assignment_id)
    video_duration = ProgressRepository.get_video_duration(assignment)

    detail = ProgressService.get_provenance_detail(assignment, progress, override, video_duration)
    return _provenance_detail_to_drill_down_response(assignment, detail)


async def set_override_service(
    session: AsyncSession, *, current_user: CurrentUser, assignment_id: uuid.UUID, request: SetOverrideRequest
) -> DrillDownResponse:
    """Create or reverse an HR Override (Story 5.5/5.5b, FR-12). HR_ADMIN-only,
    hard-scoped to assignments the caller created -- identical scoping to
    get_drill_down_service (same uniform 403 for not-found/not-owned, AC7).
    The actual mutation is delegated to ProgressService.set_override()
    (service-to-service, per AD-1) rather than reaching into
    ProgressRepository directly here -- unlike get_drill_down_service's
    existing read-side shortcut (a pre-existing, already-deferred AD-1 gap,
    see deferred-work.md), this new write path does not repeat that pattern."""
    require_hr_admin(current_user)

    assignment = await get_assignment_scoped_to_hr_admin(
        session, assignment_id=assignment_id, hr_admin_id=_parse_user_id(current_user)
    )
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this assignment")

    video_duration = ProgressRepository.get_video_duration(assignment)
    detail = await ProgressService.set_override(
        session,
        assignment=assignment,
        current_user=current_user,
        action=request.action,
        reason=request.reason,
        video_duration=video_duration,
    )
    return _provenance_detail_to_drill_down_response(assignment, detail)


async def delete_assignment_service(
    session: AsyncSession, *, current_user: CurrentUser, assignment_id: uuid.UUID
) -> None:
    """Soft-delete an Assignment (Story 3.7, FR-15). HR_ADMIN-only,
    hard-scoped to assignments the caller created -- identical scoping to
    get_drill_down_service/set_override_service (same uniform 403 for
    not-found/not-owned). Succeeds regardless of the Assignment's Status or
    whether it carries an active HR Override -- no state-based restriction
    (sprint-change-proposal-2026-07-13.md, "no restriction" decision).

    Idempotent (AC7): re-deleting an already-inactive Assignment is a 204
    no-op -- it does not overwrite the original deleted_at/deleted_by with a
    second delete's values. Chosen over a 404/409 since there's no existing
    precedent in this codebase for a stricter "already deleted" error, and a
    no-op is simpler for a caller that double-clicks or retries."""
    require_hr_admin(current_user)

    assignment = await get_assignment_scoped_to_hr_admin(
        session, assignment_id=assignment_id, hr_admin_id=_parse_user_id(current_user)
    )
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this assignment")

    if assignment.active:
        await soft_delete_assignment(session, assignment=assignment, deleted_by=_parse_user_id(current_user))


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

    overrides = await ProgressRepository.get_active_overrides_for_assignments(
        session, [assignment.id for assignment in assignments]
    )
    override_by_assignment_id = {override.assignment_id: override for override in overrides}

    items: list[AssignmentContentItem] = []
    for assignment in assignments:
        content = await match_content_for_skill(session, assignment.skill_id)
        progress = await ProgressService.get_progress(session, assignment.id)
        watch_position = progress.watch_position if progress is not None else 0

        duration_seconds = None
        if content is not None and content.metadata:
            duration_seconds = ProgressRepository.parse_duration_seconds(content.metadata.get("duration"))

        # HR Override (AD-4: a separate, coexisting record) takes precedence
        # over the raw watch signal here too -- mirrors dashboard/service.py's
        # DashboardService (the only other Status consumer), so an HR
        # "mark complete" is reflected on the employee's own dashboard
        # instead of only the HR dashboard.
        override = override_by_assignment_id.get(assignment.id)
        if override is not None:
            derived_status = override.override_status
            status_percentage = None
        else:
            # AD-3: derive via the SAME function the HR dashboard uses
            # (derive_dashboard_status_and_percent), not the older
            # derive_status -- the two had drifted onto different COMPLETED
            # criteria (derive_status required watch_position >= duration
            # exactly; this one rounds the percentage, so e.g. 3603/3606s
            # rounds to 100% and correctly derives COMPLETED there but not
            # under derive_status), which is exactly the contradiction of a
            # card showing "100% watched" while still badged "In Progress".
            status_enum, status_percentage = ProgressService.derive_dashboard_status_and_percent(
                watch_position, duration_seconds
            )
            derived_status = status_enum.value

        if derived_status == "NOT_STARTED":
            group = "TO_START"
        elif derived_status == "COMPLETED":
            group = "COMPLETED"
        else:
            group = "IN_PROGRESS"

        items.append(
            AssignmentContentItem(
                assignment_id=assignment.id,
                skill_id=assignment.skill_id,
                skill_name=assignment.skill.name,
                content=content,
                watch_position=watch_position,
                status=derived_status,
                status_percentage=status_percentage,
                group=group,
            )
        )

    in_progress_count = sum(1 for item in items if item.group == "IN_PROGRESS")
    to_start_count = sum(1 for item in items if item.group == "TO_START")
    completed_count = sum(1 for item in items if item.group == "COMPLETED")

    return MyAssignmentsResponse(
        total=len(items),
        in_progress_count=in_progress_count,
        to_start_count=to_start_count,
        completed_count=completed_count,
        assignments=items,
    )
