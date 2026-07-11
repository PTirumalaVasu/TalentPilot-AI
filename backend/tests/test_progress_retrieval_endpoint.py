"""
Integration tests for Story 4-5: Resume Position Retrieval & Exact-Point Playback

Tests the GET /api/assignments/{assignment_id}/progress endpoint:
- AC1: Endpoint returns position (AC1)
- AC4: Hard-scoping at router/service layer
- AC10: Backward compatibility with existing tests
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from httpx import AsyncClient

from app.assignments.models import Employee, Assignment, Skill, ContentCatalog, SkillProgress
from app.core.security import create_access_token
from app.core.seeds import _DEMO_EMPLOYEE_IDS, _DEMO_ACCOUNTS
from sqlalchemy import select


@pytest.fixture
async def employee(db_session):
    """Fixture: get test employee (Casey)."""
    emp = await db_session.get(Employee, _DEMO_EMPLOYEE_IDS[1])  # Casey
    return emp


@pytest.fixture
async def other_employee(db_session):
    """Fixture: get another test employee (Morgan)."""
    emp = await db_session.get(Employee, _DEMO_EMPLOYEE_IDS[2])  # Morgan
    return emp


@pytest.fixture
async def skill(db_session):
    """Fixture: get test skill."""
    result = await db_session.execute(select(Skill).limit(1))
    return result.scalar_one()


@pytest.fixture
async def video_content(db_session, skill):
    """Fixture: create test video content."""
    content = ContentCatalog(
        id=uuid4(),
        skill_id=skill.id,
        title="Test Video",
        description="Test video",
        type="VIDEO",
        url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        source="YOUTUBE",
        content_metadata={"duration": 600, "video_id": "dQw4w9WgXcQ"},
    )
    db_session.add(content)
    await db_session.flush()
    return content


@pytest.fixture
async def assignment_for_employee(db_session, employee, skill, video_content):
    """Fixture: create assignment for test employee."""
    assignment = Assignment(
        id=uuid4(),
        employee_id=employee.id,
        skill_id=skill.id,
        content_id=video_content.id,
        assigned_by=employee.id,
    )
    db_session.add(assignment)
    await db_session.flush()
    return assignment


@pytest.fixture
async def assignment_for_other_employee(db_session, other_employee, skill, video_content):
    """Fixture: create assignment for another employee."""
    assignment = Assignment(
        id=uuid4(),
        employee_id=other_employee.id,
        skill_id=skill.id,
        content_id=video_content.id,
        assigned_by=other_employee.id,
    )
    db_session.add(assignment)
    await db_session.flush()
    return assignment


@pytest.fixture
async def client_authenticated(client: AsyncClient, employee):
    """Fixture: authenticated client for employee."""
    token = create_access_token(employee.id, "EMPLOYEE", employee.email)
    client.cookies["session"] = token
    return client


@pytest.fixture
async def client_other_employee(client: AsyncClient, other_employee):
    """Fixture: authenticated client for other employee."""
    token = create_access_token(other_employee.id, "EMPLOYEE", other_employee.email)
    client.cookies["session"] = token
    return client


@pytest.fixture
async def client_hr_admin(client: AsyncClient):
    """Fixture: authenticated client for HR Admin."""
    hr_email = _DEMO_ACCOUNTS[0][0]  # Rita
    token = create_access_token(uuid4(), "HR_ADMIN", hr_email)
    client.cookies["session"] = token
    return client


class TestGetResumePositionEndpoint:
    """Integration tests for GET /api/assignments/{assignment_id}/progress"""

    @pytest.mark.asyncio
    async def test_get_resume_position_first_view_200(
        self, client_authenticated, assignment_for_employee
    ):
        """AC1: First view returns 200 with position 0."""
        response = await client_authenticated.get(
            f"/api/assignments/{assignment_for_employee.id}/progress"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["watch_position"] == 0
        assert data["event_time"] is None
        assert data["verified"] is False

    @pytest.mark.asyncio
    async def test_get_resume_position_stored_position_200(
        self, db_session, client_authenticated, assignment_for_employee
    ):
        """AC1: Returns stored position with 200 status."""
        # Create stored progress
        progress = SkillProgress(
            id=uuid4(),
            assignment_id=assignment_for_employee.id,
            watch_position=872,
            event_time=datetime.now(timezone.utc),
            verified=True,
        )
        db_session.add(progress)
        await db_session.flush()

        response = await client_authenticated.get(
            f"/api/assignments/{assignment_for_employee.id}/progress"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["watch_position"] == 872
        assert data["verified"] is True

    @pytest.mark.asyncio
    async def test_get_resume_position_no_auth_401(self, client, assignment_for_employee):
        """AC1: Returns 401 Unauthorized when not authenticated."""
        response = await client.get(
            f"/api/assignments/{assignment_for_employee.id}/progress"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_resume_position_wrong_employee_403(
        self, client_other_employee, assignment_for_employee
    ):
        """AC4: Returns 403 Forbidden when hard-scoping fails (identity mismatch)."""
        response = await client_other_employee.get(
            f"/api/assignments/{assignment_for_employee.id}/progress"
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_resume_position_missing_assignment_403(
        self, client_authenticated
    ):
        """AC4: Returns 403 when assignment doesn't exist (hard-scoping)."""
        fake_id = uuid4()
        response = await client_authenticated.get(
            f"/api/assignments/{fake_id}/progress"
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_resume_position_hr_admin_forbidden(
        self, client_hr_admin, assignment_for_employee
    ):
        """AC10: HR Admin cannot call employee-only endpoint (returns 403)."""
        response = await client_hr_admin.get(
            f"/api/assignments/{assignment_for_employee.id}/progress"
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_resume_position_idempotent_repeated_calls(
        self, db_session, client_authenticated, assignment_for_employee
    ):
        """AC6: Repeated calls return identical results."""
        # Create stored progress
        progress = SkillProgress(
            id=uuid4(),
            assignment_id=assignment_for_employee.id,
            watch_position=300,
            event_time=datetime.now(timezone.utc),
            verified=True,
        )
        db_session.add(progress)
        await db_session.flush()

        # Call three times
        response1 = await client_authenticated.get(
            f"/api/assignments/{assignment_for_employee.id}/progress"
        )
        response2 = await client_authenticated.get(
            f"/api/assignments/{assignment_for_employee.id}/progress"
        )
        response3 = await client_authenticated.get(
            f"/api/assignments/{assignment_for_employee.id}/progress"
        )

        assert response1.status_code == response2.status_code == response3.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        data3 = response3.json()
        assert data1 == data2 == data3
        assert data1["watch_position"] == 300


@pytest.fixture
async def client(app):
    """Fixture: AsyncClient for FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
