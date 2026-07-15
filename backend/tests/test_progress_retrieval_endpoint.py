"""
Integration tests for Story 4-5: Resume Position Retrieval & Exact-Point Playback

Tests the GET /api/assignments/{assignment_id}/progress endpoint:
- AC1: Endpoint returns position (AC1)
- AC4: Hard-scoping at router/service layer
- AC10: Backward compatibility with existing tests

Real app + ASGITransport + real Postgres, same pattern as
test_drill_down_endpoint.py / test_override_endpoint.py (see those files'
module docstrings for why loop_scope="module" is needed here, and why rows
are created/cleaned up via a private engine + explicit try/finally in each
test body rather than fixture teardown or conftest.py's db_session -- a
row merely flush()'d on db_session is invisible to these HTTP requests,
which go through the app's own get_db() session on a different connection).
"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import Assignment, ContentCatalog, SkillProgress
from app.core.config import settings
from app.core.security import create_access_token
from app.core.seed_ids import CASEY_ID, MORGAN_ID, RITA_ID
from app.core.seeds import SKILL_DATA_VIZ_ID
from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="module")

_engine = create_async_engine(settings.DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _authenticated_client(user_id: uuid.UUID, role: str) -> AsyncClient:
    client = _client()
    token = create_access_token(str(user_id), role)
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)
    return client


async def _create_video_content() -> uuid.UUID:
    content_id = uuid.uuid4()
    async with _session_factory() as session:
        session.add(
            ContentCatalog(
                id=content_id,
                skill_id=SKILL_DATA_VIZ_ID,
                title="Test Video",
                description="Test video",
                type="VIDEO",
                url="https://www.youtube.com/embed/dQw4w9WgXcQ",
                embedding=[0.1] * 384,
                source="YOUTUBE",
                content_metadata={"duration": 600, "video_id": "dQw4w9WgXcQ"},
            )
        )
        await session.commit()
    return content_id


async def _create_assignment(employee_id: uuid.UUID, content_id: uuid.UUID) -> uuid.UUID:
    assignment_id = uuid.uuid4()
    async with _session_factory() as session:
        session.add(
            Assignment(
                id=assignment_id,
                employee_id=employee_id,
                skill_id=SKILL_DATA_VIZ_ID,
                content_id=content_id,
                assigned_by=employee_id,
            )
        )
        await session.commit()
    return assignment_id


async def _add_progress(assignment_id: uuid.UUID, watch_position: int, *, verified: bool) -> None:
    async with _session_factory() as session:
        session.add(
            SkillProgress(
                id=uuid.uuid4(),
                assignment_id=assignment_id,
                watch_position=watch_position,
                event_time=datetime.now(timezone.utc),
                verified=verified,
            )
        )
        await session.commit()


async def _cleanup(assignment_id: uuid.UUID, content_id: uuid.UUID) -> None:
    async with _session_factory() as session:
        await session.execute(delete(SkillProgress).where(SkillProgress.assignment_id == assignment_id))
        await session.execute(delete(Assignment).where(Assignment.id == assignment_id))
        await session.execute(delete(ContentCatalog).where(ContentCatalog.id == content_id))
        await session.commit()


class TestGetResumePositionEndpoint:
    """Integration tests for GET /api/assignments/{assignment_id}/progress"""

    async def test_get_resume_position_first_view_200(self):
        """AC1: First view returns 200 with position 0."""
        content_id = await _create_video_content()
        assignment_id = await _create_assignment(CASEY_ID, content_id)
        try:
            async with _authenticated_client(CASEY_ID, "EMPLOYEE") as client:
                response = await client.get(f"/api/assignments/{assignment_id}/progress")
            assert response.status_code == 200
            data = response.json()
            assert data["watch_position"] == 0
            assert data["event_time"] is None
            assert data["verified"] is False
        finally:
            await _cleanup(assignment_id, content_id)

    async def test_get_resume_position_stored_position_200(self):
        """AC1: Returns stored position with 200 status."""
        content_id = await _create_video_content()
        assignment_id = await _create_assignment(CASEY_ID, content_id)
        try:
            # Within the fixture video's 600-second duration -- an out-of-bounds
            # position is legitimately zeroed by the service (see the sibling
            # out-of-bounds-fallback test), so this needs to actually fit.
            await _add_progress(assignment_id, 400, verified=True)

            async with _authenticated_client(CASEY_ID, "EMPLOYEE") as client:
                response = await client.get(f"/api/assignments/{assignment_id}/progress")
            assert response.status_code == 200
            data = response.json()
            assert data["watch_position"] == 400
            assert data["verified"] is True
        finally:
            await _cleanup(assignment_id, content_id)

    async def test_get_resume_position_no_auth_401(self):
        """AC1: Returns 401 Unauthorized when not authenticated."""
        content_id = await _create_video_content()
        assignment_id = await _create_assignment(CASEY_ID, content_id)
        try:
            async with _client() as client:
                response = await client.get(f"/api/assignments/{assignment_id}/progress")
            assert response.status_code == 401
        finally:
            await _cleanup(assignment_id, content_id)

    async def test_get_resume_position_wrong_employee_403(self):
        """AC4: Returns 403 Forbidden when hard-scoping fails (identity mismatch)."""
        content_id = await _create_video_content()
        assignment_id = await _create_assignment(CASEY_ID, content_id)
        try:
            async with _authenticated_client(MORGAN_ID, "EMPLOYEE") as client:
                response = await client.get(f"/api/assignments/{assignment_id}/progress")
            assert response.status_code == 403
        finally:
            await _cleanup(assignment_id, content_id)

    async def test_get_resume_position_missing_assignment_403(self):
        """AC4: Returns 403 when assignment doesn't exist (hard-scoping)."""
        fake_id = uuid.uuid4()
        async with _authenticated_client(CASEY_ID, "EMPLOYEE") as client:
            response = await client.get(f"/api/assignments/{fake_id}/progress")
        assert response.status_code == 403

    async def test_get_resume_position_hr_admin_forbidden(self):
        """AC10: HR Admin cannot call employee-only endpoint (returns 403)."""
        content_id = await _create_video_content()
        assignment_id = await _create_assignment(CASEY_ID, content_id)
        try:
            async with _authenticated_client(RITA_ID, "HR_ADMIN") as client:
                response = await client.get(f"/api/assignments/{assignment_id}/progress")
            assert response.status_code == 403
        finally:
            await _cleanup(assignment_id, content_id)

    async def test_get_resume_position_idempotent_repeated_calls(self):
        """AC6: Repeated calls return identical results."""
        content_id = await _create_video_content()
        assignment_id = await _create_assignment(CASEY_ID, content_id)
        try:
            await _add_progress(assignment_id, 300, verified=True)

            async with _authenticated_client(CASEY_ID, "EMPLOYEE") as client:
                response1 = await client.get(f"/api/assignments/{assignment_id}/progress")
                response2 = await client.get(f"/api/assignments/{assignment_id}/progress")
                response3 = await client.get(f"/api/assignments/{assignment_id}/progress")

            assert response1.status_code == response2.status_code == response3.status_code == 200
            data1 = response1.json()
            data2 = response2.json()
            data3 = response3.json()
            assert data1 == data2 == data3
            assert data1["watch_position"] == 300
        finally:
            await _cleanup(assignment_id, content_id)
