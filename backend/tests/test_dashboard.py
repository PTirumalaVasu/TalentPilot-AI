"""Tests for the dashboard module (Story 5-1)."""
import pytest
from uuid import UUID

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.service import DashboardService
from app.core.security import create_access_token
from app.core.config import settings
from app.auth.schemas import Role
from app.main import app


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_dashboard_service_returns_response(db_session: AsyncSession):
    """Test: Dashboard service returns proper response structure."""
    # Use Rita (HR_ADMIN from seeded data)
    rita_id = UUID("550e8400-e29b-41d4-a716-446655440001")

    response = await DashboardService.get_dashboard_assignments(
        db_session, hr_admin_id=rita_id, page=1, page_size=50
    )

    # Verify response structure
    assert hasattr(response, "assignments")
    assert hasattr(response, "total_count")
    assert hasattr(response, "page")
    assert hasattr(response, "page_size")
    assert isinstance(response.assignments, list)
    assert response.page == 1
    assert response.page_size == 50


@pytest.mark.asyncio
async def test_dashboard_service_pagination(db_session: AsyncSession):
    """Test: Pagination parameters are respected."""
    mock_hr_admin_id = UUID("550e8400-e29b-41d4-a716-446655440001")

    # Test page 2
    response = await DashboardService.get_dashboard_assignments(
        db_session, hr_admin_id=mock_hr_admin_id, page=2, page_size=25
    )

    assert response.page == 2
    assert response.page_size == 25


@pytest.mark.asyncio
async def test_dashboard_response_schema(db_session: AsyncSession):
    """Test: Response matches DashboardResponse schema."""
    mock_hr_admin_id = UUID("550e8400-e29b-41d4-a716-446655440001")

    response = await DashboardService.get_dashboard_assignments(
        db_session, hr_admin_id=mock_hr_admin_id, page=1, page_size=50
    )

    # Verify response has required fields
    assert hasattr(response, "assignments")
    assert hasattr(response, "total_count")
    assert hasattr(response, "page")
    assert hasattr(response, "page_size")

    # Verify types
    assert isinstance(response.assignments, list)
    assert isinstance(response.total_count, int)
    assert isinstance(response.page, int)
    assert isinstance(response.page_size, int)


@pytest.mark.asyncio
async def test_dashboard_stats_service_returns_response_structure(db_session: AsyncSession):
    """Test: DashboardService.get_dashboard_stats (Story 9.1) returns the
    right shape. No absolute-value assertions -- this runs against the live
    seeded/shared dev DB (same convention as the tests above), so only
    structural/invariant checks are reliable here. Precise value assertions
    (mixed statuses, HR Override, archived-Employee exclusion) live in
    test_dashboard_router.py, which creates and cleans up its own rows."""
    response = await DashboardService.get_dashboard_stats(db_session)

    assert isinstance(response.total_employees, int)
    assert isinstance(response.total_skills_assigned, int)
    assert isinstance(response.total_completed, int)
    assert response.total_employees >= 0
    assert response.total_skills_assigned >= 0
    assert response.total_completed == response.completed_count
    assert response.completed_count + response.in_progress_count + response.not_started_count == response.total_skills_assigned
    assert 0 <= response.overall_percent <= 100


@pytest.mark.asyncio
async def test_dashboard_requires_hr_admin_role():
    """Test: GET /api/dashboard returns 403 Forbidden for EMPLOYEE role (AC10)."""
    # Create EMPLOYEE JWT. The app only reads the session from the
    # SESSION_COOKIE_NAME cookie (see get_current_token_payload), not an
    # Authorization header, so the token must be delivered as a cookie.
    employee_id = UUID("550e8400-e29b-41d4-a716-446655440010")
    employee_token = create_access_token(
        user_id=str(employee_id), role=Role.EMPLOYEE
    )

    async with _client() as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, employee_token)
        response = await client.get("/api/dashboard")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_unauthenticated_returns_401():
    """Test: GET /api/dashboard returns 401 Unauthorized for no JWT (AC10)."""
    async with _client() as client:
        response = await client.get("/api/dashboard")

    assert response.status_code == 401
