"""Service layer for the assignments module. Cross-module callers must go through here (AD-1)."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.repository import (
    _parse_user_id,
    create_assignment,
    find_existing_assignment,
    list_assignments_for_dashboard,
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
from app.auth.service import require_hr_admin
from app.progress.repository import ProgressRepository
from app.progress.service import ProgressService


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
