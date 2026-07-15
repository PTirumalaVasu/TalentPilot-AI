"""Router for the dashboard module."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user, require_hr_admin
from app.core.db import get_db
from app.dashboard.schemas import DashboardResponse
from app.dashboard.service import DashboardService

router = APIRouter(tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: Annotated[CurrentUser, Depends(require_hr_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> DashboardResponse:
    """
    Fetch HR Admin's dashboard with all assignments and their statuses.

    **Access Control (AD-6):**
    - Requires HR_ADMIN role (via require_hr_admin dependency)
    - Returns 403 Forbidden for EMPLOYEE role
    - Returns 401 Unauthorized for unauthenticated requests

    **Pagination:**
    - Default: page=1, page_size=50
    - Returns assignments sorted by assigned_at DESC (newest first)

    **Status & Provenance (AD-3):**
    - Status computed from {watch signal, HR override}
    - Provenance indicates signal type: Verified / Self-reported / Needs Attention / HR Override
    - Single derivation authority per AD-3

    Args:
        current_user: Authenticated HR Admin (from require_hr_admin dependency)
        session: Database session
        page: Page number (1-indexed)
        page_size: Rows per page (max 500)

    Returns:
        DashboardResponse with paginated assignments
    """
    return await DashboardService.get_dashboard_assignments(
        session,
        hr_admin_id=current_user.user_id,
        page=page,
        page_size=page_size,
    )
