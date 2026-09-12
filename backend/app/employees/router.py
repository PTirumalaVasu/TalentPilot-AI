"""FastAPI router for the employees module.

Story 7.2 mounts this router for the first time (Story 7.1 left it as a
documented, unmounted stub). Mounted in app/main.py under
/api/admin/employees, mirroring skills/router.py's /api/admin/skills prefix
(both are HR-Admin-only mutation modules, same convention). Stories 7.3-7.6
add GET/PATCH/DELETE and the regenerate-password endpoint.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.core.db import get_db
from app.employees.schemas import (
    CreateEmployeeRequest,
    EmployeeCreatedResponse,
    EmployeeResponse,
    UpdateEmployeeRequest,
)
from app.employees.service import create_employee_service, list_employees_service, update_employee_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[EmployeeResponse])
async def list_employees_route(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[EmployeeResponse]:
    """Employees roster (Story 7.3 AC1/AC3/AC4, FR-25) -- HR_ADMIN-only via
    list_employees_service's require_hr_admin gate. Returns the full roster
    (active and archived); search/filter/pagination/"show archived" are all
    client-side (Story 7.3 Scope Note 2)."""
    return await list_employees_service(session, current_user=current_user)


@router.post("", response_model=EmployeeCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_employee_route(
    request: CreateEmployeeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> EmployeeCreatedResponse:
    """Creates an Employee with a generated login (Story 7.2 AC1) --
    HR_ADMIN-only via create_employee_service's require_hr_admin gate."""
    return await create_employee_service(session, current_user=current_user, request=request)


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee_route(
    employee_id: UUID,
    request: UpdateEmployeeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> EmployeeResponse:
    """Edits an existing Employee's profile fields (Story 7.4 AC1, FR-26) --
    Employee ID/Code is immutable (not part of the request body). 404 if the
    Employee doesn't exist, 409 on a case-insensitive email conflict with a
    different Employee -- HR_ADMIN-only via update_employee_service's
    require_hr_admin gate."""
    return await update_employee_service(
        session, current_user=current_user, employee_id=employee_id, request=request
    )
