from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.schemas import (
    AssignmentResponse,
    CreateAssignmentRequest,
    DrillDownResponse,
    EmployeeResponse,
    MyAssignmentsResponse,
    SetOverrideRequest,
    SkillResponse,
)
from app.assignments.service import (
    create_assignment_service,
    delete_assignment_service,
    duplicate_check_service,
    get_drill_down_service,
    list_employees_service,
    list_my_assignments,
    list_skills_service,
    set_override_service,
)
from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.core.db import get_db

router = APIRouter(tags=["assignments"])


@router.get("/employees", response_model=list[EmployeeResponse])
async def list_employees_route(
    search: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> list[EmployeeResponse]:
    """Read-only employee directory for the assignment modal's Step 1
    (Employee) combobox — not scoped by caller identity (Story 3.4 AC2)."""
    return await list_employees_service(session, search=search)


@router.get("/skills", response_model=list[SkillResponse])
async def list_skills_route(
    search: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> list[SkillResponse]:
    """Read-only skill directory for the assignment modal's Step 2 (Skill)
    combobox (Story 3.4 AC3)."""
    return await list_skills_service(session, search=search)


@router.get("/duplicate-check", response_model=list[AssignmentResponse])
async def duplicate_check_route(
    employee_id: UUID,
    skill_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[AssignmentResponse]:
    """Existing Assignment(s) for (employee_id, skill_id), used by the modal
    before Step 3 renders (Story 3.4 AC5). HR_ADMIN-only via
    duplicate_check_service's require_hr_admin gate (code-review fix)."""
    return await duplicate_check_service(session, current_user=current_user, employee_id=employee_id, skill_id=skill_id)


@router.get("/employee-assignments")
async def list_employee_assignments_route(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MyAssignmentsResponse:
    """Fetch current EMPLOYEE's assignments with progress counts (Story 2.5).
    EMPLOYEE-only — returns 403 for HR_ADMIN role."""
    return await list_my_assignments(session, current_user=current_user)


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment_route(
    request: CreateAssignmentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AssignmentResponse:
    """Creates an Assignment (Story 3.4 AC1/AC9) — HR_ADMIN-only via
    create_assignment_service's require_hr_admin gate (Story 3.1 AC4)."""
    return await create_assignment_service(session, current_user=current_user, request=request)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment_route(
    assignment_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Soft-deletes an Assignment (Story 3.7, FR-15) -- HR_ADMIN-only via
    delete_assignment_service's require_hr_admin gate, hard-scoped to
    assignments the caller created. Row is never physically removed; see
    delete_assignment_service's docstring for the soft-delete/idempotency
    contract."""
    await delete_assignment_service(session, current_user=current_user, assignment_id=assignment_id)


@router.get("/{assignment_id}/progress/drill-down", response_model=DrillDownResponse)
async def get_drill_down_route(
    assignment_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DrillDownResponse:
    """Provenance Drill-Down modal data (Story 5.2, FR-9) — HR_ADMIN-only via
    get_drill_down_service's require_hr_admin gate, hard-scoped to
    assignments the caller created. Deliberately registered on this router
    (mounted at /api/assignments with only relative-path routes) rather than
    progress/router.py, which double-prefixes its own absolute-path routes
    with main.py's /api/progress mount — see this story's Dev Notes Finding 2
    for the live bug that causes."""
    return await get_drill_down_service(session, current_user=current_user, assignment_id=assignment_id)


@router.post("/{assignment_id}/override", response_model=DrillDownResponse)
async def set_override_route(
    assignment_id: UUID,
    request: SetOverrideRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DrillDownResponse:
    """Create or reverse an HR Override (Story 5.5/5.5b, FR-12) -- HR_ADMIN-only
    via set_override_service's require_hr_admin gate, hard-scoped to
    assignments the caller created. Registered here (not progress/router.py)
    for the same double-prefix-avoidance reason as the drill-down route
    above -- even though assignment_overrides is owned by progress/ (AD-1),
    the mutation itself is delegated to ProgressService.set_override; this
    route/service pairing is purely about avoiding the routing bug."""
    return await set_override_service(session, current_user=current_user, assignment_id=assignment_id, request=request)
