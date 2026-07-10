from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.schemas import (
    AssignmentResponse,
    CreateAssignmentRequest,
    EmployeeResponse,
    SkillResponse,
)
from app.assignments.service import (
    create_assignment_service,
    duplicate_check_service,
    list_employees_service,
    list_skills_service,
)
from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.core.db import get_db

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/employees", response_model=list[EmployeeResponse])
async def list_employees_route(
    search: str | None = None, session: AsyncSession = Depends(get_db)
) -> list[EmployeeResponse]:
    """Read-only employee directory for the assignment modal's Step 1
    (Employee) combobox — not scoped by caller identity (Story 3.4 AC2)."""
    return await list_employees_service(session, search=search)


@router.get("/skills", response_model=list[SkillResponse])
async def list_skills_route(
    search: str | None = None, session: AsyncSession = Depends(get_db)
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


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment_route(
    request: CreateAssignmentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AssignmentResponse:
    """Creates an Assignment (Story 3.4 AC1/AC9) — HR_ADMIN-only via
    create_assignment_service's require_hr_admin gate (Story 3.1 AC4)."""
    return await create_assignment_service(session, current_user=current_user, request=request)
