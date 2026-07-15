"""Router-level tests for dashboard/router.py (Story 3.5).

Same real-app + loop_scope="module" pattern as test_assignments_router.py /
test_assignments_create_route.py — see those files' module docstrings for
why plain function-scoped @pytest.mark.asyncio doesn't work here (this is a
live-DB-touching router).
"""
import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import Assignment, ContentCatalog, SkillProgress
from app.core.config import settings
from app.core.seed_ids import CASEY_ID, RITA_ID
from app.core.seeds import SKILL_DATA_VIZ_ID, SKILL_SALESFORCE_ID
from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="module")

_engine = create_async_engine(settings.DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _login(client: AsyncClient, email: str = "rita@sails.example.com") -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": "demo123"})
    assert response.status_code == 200
    set_cookie_header = response.headers.get("set-cookie", "")
    prefix = f"{settings.SESSION_COOKIE_NAME}="
    token = set_cookie_header.split(";", 1)[0][len(prefix) :]
    client.cookies.clear()
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)
    return token


async def _cleanup_assignment(assignment_id: uuid.UUID) -> None:
    async with _session_factory() as session:
        # skill_progress FKs to assignments — delete it first (this test
        # file is the first to insert SkillProgress rows directly, unlike
        # the sibling test_assignments_*.py files).
        await session.execute(delete(SkillProgress).where(SkillProgress.assignment_id == assignment_id))
        await session.execute(delete(Assignment).where(Assignment.id == assignment_id))
        await session.commit()


async def _cleanup_assignments_for(employee_id: uuid.UUID, skill_id: uuid.UUID) -> None:
    async with _session_factory() as session:
        result = await session.execute(
            select(Assignment.id).where(Assignment.employee_id == employee_id, Assignment.skill_id == skill_id)
        )
        assignment_ids = [row[0] for row in result.all()]
        if assignment_ids:
            await session.execute(delete(SkillProgress).where(SkillProgress.assignment_id.in_(assignment_ids)))
        await session.execute(
            delete(Assignment).where(Assignment.employee_id == employee_id, Assignment.skill_id == skill_id)
        )
        await session.commit()


async def test_dashboard_assignments_includes_created_assignment_with_display_names():
    await _cleanup_assignments_for(CASEY_ID, SKILL_DATA_VIZ_ID)
    created_id = None
    try:
        async with _client() as client:
            await _login(client)
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assert create_response.status_code == 201
            created_id = uuid.UUID(create_response.json()["id"])

            response = await client.get("/api/dashboard")

            assert response.status_code == 200
            body = response.json()
            row = next((r for r in body["assignments"] if r["assignment_id"] == str(created_id)), None)
            assert row is not None, "newly created assignment not found in dashboard list"
            assert row["employee_id"] == str(CASEY_ID)
            assert row["employee_name"] == "Casey the Continuer"
            assert row["skill_id"] == str(SKILL_DATA_VIZ_ID)
            assert row["skill_name"] == "Data Visualization"
            assert row["status"] == "Not Started"
            assert row["status_percentage"] is None
            assert row["provenance"] == "Not Started"
            assert set(row.keys()) == {
                "assignment_id",
                "employee_id",
                "employee_name",
                "employee_group",
                "skill_id",
                "skill_name",
                "status",
                "status_percentage",
                "provenance",
                "last_updated",
                "assignment_created_at",
            }
    finally:
        if created_id is not None:
            await _cleanup_assignment(created_id)


async def test_dashboard_assignments_requires_authentication():
    async with _client() as client:
        response = await client.get("/api/dashboard")
        assert response.status_code == 401


async def test_dashboard_assignments_forbidden_for_employee_role():
    async with _client() as client:
        await _login(client, email="casey@sails.example.com")
        response = await client.get("/api/dashboard")
        assert response.status_code == 403
        assert response.json()["code"] == "FORBIDDEN_NOT_HR_ADMIN"


async def test_dashboard_assignments_reflects_real_watch_progress_status_and_percent():
    """End-to-end: a real skill_progress row (with content whose duration is
    known) must drive the dashboard's Status/progress_percent — not the
    hardcoded placeholder. Exercises all three Status buckets in one pass:
    not-started (no progress row), in-progress (partial watch), completed
    (full watch)."""
    await _cleanup_assignments_for(CASEY_ID, SKILL_DATA_VIZ_ID)
    await _cleanup_assignments_for(RITA_ID, SKILL_DATA_VIZ_ID)
    created_ids: dict[str, uuid.UUID] = {}
    content_id = None
    try:
        async with _session_factory() as session:
            content = ContentCatalog(
                skill_id=SKILL_DATA_VIZ_ID,
                title="Test content for Story 3.5 dashboard progress derivation",
                description="Test content",
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

            # Not-started: created with no progress row at all.
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_DATA_VIZ_ID), "content_id": str(content_id)},
            )
            assert create_response.status_code == 201
            created_ids["not_started"] = uuid.UUID(create_response.json()["id"])

            # In-progress: 150/300 seconds watched.
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(RITA_ID), "skill_id": str(SKILL_DATA_VIZ_ID), "content_id": str(content_id)},
            )
            assert create_response.status_code == 201
            created_ids["in_progress"] = uuid.UUID(create_response.json()["id"])

        async with _session_factory() as session:
            session.add(
                SkillProgress(
                    assignment_id=created_ids["in_progress"],
                    watch_position=150,
                    event_time=datetime.now(timezone.utc),
                    verified=True,
                )
            )
            await session.commit()

        async with _client() as client:
            await _login(client)
            response = await client.get("/api/dashboard")
            assert response.status_code == 200
            body = response.json()

            not_started_row = next(r for r in body["assignments"] if r["assignment_id"] == str(created_ids["not_started"]))
            assert not_started_row["status"] == "Not Started"
            assert not_started_row["status_percentage"] is None
            assert not_started_row["provenance"] == "Not Started"

            in_progress_row = next(r for r in body["assignments"] if r["assignment_id"] == str(created_ids["in_progress"]))
            assert in_progress_row["status"] == "In Progress"
            assert in_progress_row["status_percentage"] == 50
            assert in_progress_row["provenance"] == "Verified"
    finally:
        for cid in created_ids.values():
            await _cleanup_assignment(cid)
        if content_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(ContentCatalog).where(ContentCatalog.id == content_id))
                await session.commit()


async def test_dashboard_assignments_returns_multiple_org_wide_rows_for_hr_admin():
    """HR sessions are unrestricted (not scoped to a single employee) —
    confirm at least two distinct employees' assignments both surface in one
    call, proving this is an org-wide read, not accidentally self-scoped."""
    await _cleanup_assignments_for(CASEY_ID, SKILL_SALESFORCE_ID)
    await _cleanup_assignments_for(RITA_ID, SKILL_SALESFORCE_ID)
    created_ids = []
    try:
        async with _client() as client:
            await _login(client)
            for employee_id in (CASEY_ID, RITA_ID):
                create_response = await client.post(
                    "/api/assignments",
                    json={"employee_id": str(employee_id), "skill_id": str(SKILL_SALESFORCE_ID)},
                )
                assert create_response.status_code == 201
                created_ids.append(uuid.UUID(create_response.json()["id"]))

            response = await client.get("/api/dashboard")

            assert response.status_code == 200
            body = response.json()
            found_ids = {r["assignment_id"] for r in body["assignments"]}
            assert all(str(cid) in found_ids for cid in created_ids)
    finally:
        for cid in created_ids:
            await _cleanup_assignment(cid)
