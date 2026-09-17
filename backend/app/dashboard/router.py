"""Router for the dashboard module."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user, require_hr_admin
from app.core.db import get_db
from app.dashboard.schemas import (
    DashboardResponse,
    DashboardStatsResponse,
    EmployeeSegmentationResponse,
    ExperienceDistributionResponse,
)
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


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: Annotated[CurrentUser, Depends(require_hr_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardStatsResponse:
    """
    Org-wide stats and Assignment Progress breakdown for the Skill Assignment
    Dashboard landing page (Story 9.1, FR-31/FR-32).

    **Access Control (AD-6):** identical to `GET /api/dashboard` -- requires
    HR_ADMIN (403 for EMPLOYEE, 401 for unauthenticated).

    Not paginated -- this is a single computed aggregate object, not a list.

    Returns:
        DashboardStatsResponse with org-wide counts and progress breakdown
    """
    return await DashboardService.get_dashboard_stats(session)


@router.get("/segmentation", response_model=EmployeeSegmentationResponse)
async def get_employee_segmentation(
    current_user: Annotated[CurrentUser, Depends(require_hr_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> EmployeeSegmentationResponse:
    """
    Per-Employee On Track / In Progress / Needs Attention classification for
    the Skill Assignment Dashboard's pie chart (Story 9.2, FR-32).

    **Access Control (AD-6):** identical to `GET /api/dashboard` -- requires
    HR_ADMIN (403 for EMPLOYEE, 401 for unauthenticated).

    Not paginated -- this is a single computed aggregate object, not a list.

    Returns:
        EmployeeSegmentationResponse with bucket counts and the Needs
        Attention detail list (Story 9.4's popover needs this without a
        second round-trip).
    """
    return await DashboardService.get_employee_segmentation(session)


@router.get("/experience-distribution", response_model=ExperienceDistributionResponse)
async def get_experience_distribution(
    current_user: Annotated[CurrentUser, Depends(require_hr_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ExperienceDistributionResponse:
    """
    Headcount broken down by years of experience for the Employees page's
    Experience Distribution panel (Story 10.4, FR-36) -- 7 fixed,
    contiguous buckets, active roster only, distinct from FR-32's Employee
    Segmentation chart above.

    **Access Control (AD-6):** identical to `GET /api/dashboard` -- requires
    HR_ADMIN (403 for EMPLOYEE, 401 for unauthenticated).

    Not paginated -- this is a single computed aggregate object, not a list.

    Returns:
        ExperienceDistributionResponse with per-bucket counts
    """
    return await DashboardService.get_experience_distribution(session)
