"""Integration tests for GET /api/assignments/{assignment_id}/progress/drill-down
(Story 5-2, AC6). Real app + ASGITransport + real Postgres, same pattern as
test_dashboard_router.py / test_assignments_router.py (see those files'
module docstrings for why loop_scope="module" is needed here)."""
from datetime import datetime, timezone
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import Assignment, ContentCatalog, SkillProgress
from app.core.config import settings
from app.core.security import create_access_token
from app.core.seed_ids import CASEY_ID
from app.core.seeds import SKILL_DATA_VIZ_ID
from app.main import app

# Maps DrillDownResponse's screaming-snake AssignmentStatus serialization to
# the dashboard grid's Title Case display string, so the cross-surface
# invariant test below can compare them directly.
_STATUS_TITLE_CASE = {"NOT_STARTED": "Not Started", "IN_PROGRESS": "In Progress", "COMPLETED": "Completed"}

pytestmark = pytest.mark.asyncio(loop_scope="module")

_engine = create_async_engine(settings.DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _login(client: AsyncClient, email: str = "rita@sails.example.com") -> None:
    response = await client.post("/api/auth/login", json={"email": email, "password": "demo123"})
    assert response.status_code == 200
    set_cookie_header = response.headers.get("set-cookie", "")
    prefix = f"{settings.SESSION_COOKIE_NAME}="
    token = set_cookie_header.split(";", 1)[0][len(prefix) :]
    client.cookies.clear()
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)


async def _cleanup_assignment(assignment_id: uuid.UUID) -> None:
    async with _session_factory() as session:
        await session.execute(delete(SkillProgress).where(SkillProgress.assignment_id == assignment_id))
        await session.execute(delete(Assignment).where(Assignment.id == assignment_id))
        await session.commit()


async def _create_assignment(client: AsyncClient) -> uuid.UUID:
    response = await client.post(
        "/api/assignments", json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_DATA_VIZ_ID)}
    )
    assert response.status_code == 201
    return uuid.UUID(response.json()["id"])


async def test_owning_hr_admin_sees_full_drill_down_detail():
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            response = await client.get(f"/api/assignments/{assignment_id}/progress/drill-down")
            assert response.status_code == 200
            body = response.json()
            assert body["assignment_id"] == str(assignment_id)
            assert body["employee_name"] == "Casey the Continuer"
            assert body["skill_name"] == "Data Visualization"
            assert body["status"] == "NOT_STARTED"
            assert body["provenance"] == "Not Started"
            assert body["override_set_by_name"] is None
            assert body["underlying_provenance"] is None
        finally:
            await _cleanup_assignment(assignment_id)


async def test_employee_role_gets_403_never_200_or_404():
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            async with _client() as employee_client:
                await _login(employee_client, email="casey@sails.example.com")
                response = await employee_client.get(f"/api/assignments/{assignment_id}/progress/drill-down")
                assert response.status_code == 403
                assert response.json()["code"] == "FORBIDDEN_NOT_HR_ADMIN"
        finally:
            await _cleanup_assignment(assignment_id)


async def test_non_owning_hr_admin_also_sees_full_drill_down_detail():
    """PR #80: a second HR Admin (not the assignment's creator) must see the
    same drill-down detail as the creator -- HR Admins collaboratively manage
    assignments, so access is org-wide, not restricted to whoever created the
    row (this used to 403; that was the reported bug PR #80 fixed)."""
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            other_hr_token = create_access_token(str(uuid.uuid4()), "HR_ADMIN")
            async with _client() as other_hr_client:
                other_hr_client.cookies.set(settings.SESSION_COOKIE_NAME, other_hr_token)
                response = await other_hr_client.get(f"/api/assignments/{assignment_id}/progress/drill-down")
                assert response.status_code == 200
                assert response.json()["assignment_id"] == str(assignment_id)
        finally:
            await _cleanup_assignment(assignment_id)


async def test_dashboard_grid_and_drill_down_agree_on_status_and_provenance_for_the_same_assignment():
    """Cross-surface invariant (code review finding, Story 5-2): the whole
    point of consolidating derivation into get_provenance_detail() (Finding 3)
    is that the dashboard grid and the drill-down modal can never disagree on
    Status/Provenance for the same assignment. Nothing previously asserted
    this directly -- every existing test checks one endpoint in isolation.
    Exercises three scenarios: no signal, Verified in-progress, and an active
    HR Override."""
    await _cleanup_assignments_for_data_viz()
    content_id = None
    assignment_id = None
    try:
        async with _session_factory() as session:
            content = ContentCatalog(
                skill_id=SKILL_DATA_VIZ_ID,
                title="Cross-surface invariant test content",
                description="test",
                type="VIDEO",
                url="https://youtube.com/watch?v=test",
                embedding=[0.1] * 384,
                source="YOUTUBE",
                content_metadata={"video_id": "test", "duration": 300},
            )
            session.add(content)
            await session.commit()
            content_id = content.id

        async with _client() as client:
            await _login(client)
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_DATA_VIZ_ID), "content_id": str(content_id)},
            )
            assert create_response.status_code == 201
            assignment_id = uuid.UUID(create_response.json()["id"])

            async def assert_grid_and_drill_down_agree():
                dashboard_response = await client.get("/api/dashboard", params={"page_size": 500})
                assert dashboard_response.status_code == 200
                row = next(
                    r for r in dashboard_response.json()["assignments"] if r["assignment_id"] == str(assignment_id)
                )

                drill_down_response = await client.get(f"/api/assignments/{assignment_id}/progress/drill-down")
                assert drill_down_response.status_code == 200
                detail = drill_down_response.json()

                assert row["status"] == _STATUS_TITLE_CASE[detail["status"]]
                assert row["provenance"] == detail["provenance"]

            # Scenario 1: no signal at all yet.
            await assert_grid_and_drill_down_agree()

            # Scenario 2: verified watch progress, in progress.
            async with _session_factory() as session:
                session.add(
                    SkillProgress(
                        assignment_id=assignment_id,
                        watch_position=150,
                        event_time=datetime.now(timezone.utc),
                        verified=True,
                    )
                )
                await session.commit()
            await assert_grid_and_drill_down_agree()
    finally:
        if assignment_id is not None:
            await _cleanup_assignment(assignment_id)
        if content_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(ContentCatalog).where(ContentCatalog.id == content_id))
                await session.commit()


async def _cleanup_assignments_for_data_viz() -> None:
    async with _session_factory() as session:
        result = await session.execute(
            Assignment.__table__.select().where(
                Assignment.employee_id == CASEY_ID, Assignment.skill_id == SKILL_DATA_VIZ_ID
            )
        )
        assignment_ids = [row.id for row in result.all()]
        if assignment_ids:
            await session.execute(delete(SkillProgress).where(SkillProgress.assignment_id.in_(assignment_ids)))
        await session.execute(
            delete(Assignment).where(Assignment.employee_id == CASEY_ID, Assignment.skill_id == SKILL_DATA_VIZ_ID)
        )
        await session.commit()


async def test_nonexistent_assignment_gets_404():
    """Since PR #80, get_drill_down_service falls back to an unscoped lookup
    on any HR Admin -- the only way to get a "not found" now is a genuinely
    nonexistent assignment_id, which raises 404 (not the old creator-only
    403)."""
    async with _client() as client:
        await _login(client)
        response = await client.get(f"/api/assignments/{uuid.uuid4()}/progress/drill-down")
        assert response.status_code == 404


async def test_unauthenticated_gets_401():
    async with _client() as client:
        response = await client.get(f"/api/assignments/{uuid.uuid4()}/progress/drill-down")
        assert response.status_code == 401


@pytest.mark.parametrize(
    "path",
    [
        "/api/progress/export",
        "/api/progress/history",
        "/api/progress/bulk-read",
        "/api/progress/raw",
    ],
)
async def test_no_bulk_or_export_endpoints_exist(path: str):
    """AC6/AD-2: no bulk/export/history read surface exists anywhere -- these
    four named paths (drawn directly from epics.md's AC text) must all 404,
    proving single-row drill-down is the only read shape available."""
    async with _client() as client:
        await _login(client)
        response = await client.get(path)
        assert response.status_code == 404
