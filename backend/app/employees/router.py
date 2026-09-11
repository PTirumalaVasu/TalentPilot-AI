"""FastAPI router for the employees module.

Story 7.2 mounts this router for the first time (Story 7.1 left it as a
documented, unmounted stub). Mounted in app/main.py under
/api/admin/employees, mirroring skills/router.py's /api/admin/skills prefix
(both are HR-Admin-only mutation modules, same convention). Stories 7.3-7.6
add GET/PATCH/DELETE and the regenerate-password endpoint.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.core.db import get_db
from app.employees.schemas import CreateEmployeeRequest, EmployeeCreatedResponse
from app.employees.service import create_employee_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("", response_model=EmployeeCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_employee_route(
    request: CreateEmployeeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> EmployeeCreatedResponse:
    """Creates an Employee with a generated login (Story 7.2 AC1) --
    HR_ADMIN-only via create_employee_service's require_hr_admin gate."""
    return await create_employee_service(session, current_user=current_user, request=request)
