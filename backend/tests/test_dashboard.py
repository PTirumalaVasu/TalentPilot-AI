"""Tests for the dashboard module (Story 5-1)."""
import pytest
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.service import DashboardService
from app.core.security import create_access_token
from app.auth.models import Role


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


def test_dashboard_requires_hr_admin_role(client: TestClient):
    """Test: GET /api/dashboard returns 403 Forbidden for EMPLOYEE role (AC10)."""
    # Create EMPLOYEE JWT
    employee_id = UUID("550e8400-e29b-41d4-a716-446655440010")
    employee_token = create_access_token(
        user_id=str(employee_id), role=Role.EMPLOYEE
    )

    response = client.get(
        "/api/dashboard",
        headers={"Authorization": f"Bearer {employee_token}"},
    )

    assert response.status_code == 403


def test_dashboard_unauthenticated_returns_401(client: TestClient):
    """Test: GET /api/dashboard returns 401 Unauthorized for no JWT (AC10)."""
    response = client.get("/api/dashboard")

    assert response.status_code == 401
