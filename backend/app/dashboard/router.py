from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.schemas import DashboardAssignmentRow
from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.core.db import get_db
from app.dashboard.service import get_dashboard_assignments_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/assignments", response_model=list[DashboardAssignmentRow])
async def list_dashboard_assignments_route(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[DashboardAssignmentRow]:
    """HR-only read list of all Assignments for the Readiness Dashboard
    placeholder (Story 3.5) — require_hr_admin enforced in
    assignments/service.py::list_assignment_rows_for_dashboard_service."""
    return await get_dashboard_assignments_service(session, current_user=current_user)
