"""Service layer for the dashboard module. Cross-module callers must go through here (AD-1)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.schemas import DashboardAssignmentRow
from app.assignments.service import list_assignment_rows_for_dashboard_service
from app.auth.schemas import CurrentUser


async def get_dashboard_assignments_service(
    session: AsyncSession, *, current_user: CurrentUser
) -> list[DashboardAssignmentRow]:
    """Thin orchestration seam (Story 3.5): today this only calls into
    assignments/ for the placeholder row list. Story 5.1/5.2 will extend
    this function to also compose real Status/Provenance from progress/ —
    keep it thin, and do not move the HR-only gate or the Assignment query
    itself out of assignments/service.py/repository.py when that happens
    (AD-1: only assignments/ queries the Assignment table)."""
    return await list_assignment_rows_for_dashboard_service(session, current_user=current_user)
