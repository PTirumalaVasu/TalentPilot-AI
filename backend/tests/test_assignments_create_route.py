"""Router-level tests for POST /api/assignments and the duplicate-check
endpoint (Story 3.4 AC1, AC5, AC9, AC12).

Same real-app + loop_scope="module" pattern as test_assignments_router.py —
see that file's module docstring for why plain function-scoped
@pytest.mark.asyncio doesn't work here (this is a live-DB-touching router).
"""
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import Assignment, SkillProgress
from app.core.config import settings
from app.core.seed_ids import CASEY_ID, MORGAN_ID
from app.core.seeds import SKILL_DATA_VIZ_ID, SKILL_PYTHON_ID, SKILL_SQL_ID
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
        await session.execute(delete(Assignment).where(Assignment.id == assignment_id))
        await session.commit()


async def _cleanup_assignments_for(employee_id: uuid.UUID, skill_id: uuid.UUID) -> None:
    async with _session_factory() as session:
        assignment_ids = (
            await session.execute(
                select(Assignment.id).where(
                    Assignment.employee_id == employee_id, Assignment.skill_id == skill_id
                )
            )
        ).scalars().all()
        if assignment_ids:
            await session.execute(delete(SkillProgress).where(SkillProgress.assignment_id.in_(assignment_ids)))
        await session.execute(
            delete(Assignment).where(Assignment.employee_id == employee_id, Assignment.skill_id == skill_id)
        )
        await session.commit()


async def test_create_assignment_succeeds_for_hr_admin_and_returns_201():
    await _cleanup_assignments_for(MORGAN_ID, SKILL_DATA_VIZ_ID)
    created_id = None
    try:
        async with _client() as client:
            await _login(client)
            response = await client.post(
                "/api/assignments",
                json={"employee_id": str(MORGAN_ID), "skill_id": str(SKILL_DATA_VIZ_ID)},
            )

            assert response.status_code == 201
            body = response.json()
            created_id = uuid.UUID(body["id"])
            assert body["employee_id"] == str(MORGAN_ID)
            assert body["skill_id"] == str(SKILL_DATA_VIZ_ID)
            assert body["content_id"] is None
            assert body["status"] == "NOT_STARTED"
            assert body["provenance"] == "Assigned · Awaiting first watch"
    finally:
        if created_id is not None:
            await _cleanup_assignment(created_id)


async def test_create_assignment_forbidden_for_employee_role():
    async with _client() as client:
        await _login(client, email="casey@sails.example.com")
        response = await client.post(
            "/api/assignments",
            json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_PYTHON_ID)},
        )

        assert response.status_code == 403
        assert response.json()["code"] == "FORBIDDEN_NOT_HR_ADMIN"


async def test_create_assignment_requires_authentication():
    async with _client() as client:
        response = await client.post(
            "/api/assignments",
            json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_PYTHON_ID)},
        )
        assert response.status_code == 401


async def test_create_assignment_rejects_missing_fields():
    async with _client() as client:
        await _login(client)
        response = await client.post("/api/assignments", json={"employee_id": str(CASEY_ID)})
        assert response.status_code == 422


async def test_create_assignment_rejects_extra_fields():
    async with _client() as client:
        await _login(client)
        response = await client.post(
            "/api/assignments",
            json={
                "employee_id": str(CASEY_ID),
                "skill_id": str(SKILL_PYTHON_ID),
                "status": "COMPLETED",  # client-supplied status must be rejected, not silently ignored
            },
        )
        assert response.status_code == 422


async def test_duplicate_check_returns_empty_when_no_existing_assignment():
    await _cleanup_assignments_for(CASEY_ID, SKILL_SQL_ID)
    async with _client() as client:
        await _login(client)
        response = await client.get(
            "/api/assignments/duplicate-check",
            params={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_SQL_ID)},
        )

        assert response.status_code == 200
        assert response.json() == []


async def test_duplicate_check_returns_the_existing_assignment():
    await _cleanup_assignments_for(CASEY_ID, SKILL_SQL_ID)
    created_id = None
    try:
        async with _client() as client:
            await _login(client)
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_SQL_ID)},
            )
            assert create_response.status_code == 201
            created_id = uuid.UUID(create_response.json()["id"])

            response = await client.get(
                "/api/assignments/duplicate-check",
                params={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_SQL_ID)},
            )

            assert response.status_code == 200
            body = response.json()
            assert len(body) == 1
            assert body[0]["id"] == str(created_id)
    finally:
        if created_id is not None:
            await _cleanup_assignment(created_id)


async def test_duplicate_check_requires_authentication():
    async with _client() as client:
        response = await client.get(
            "/api/assignments/duplicate-check",
            params={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_SQL_ID)},
        )
        assert response.status_code == 401


async def test_duplicate_check_forbidden_for_employee_role():
    """Code-review fix: only the HR-only assignment modal uses this endpoint,
    and it reveals whether a specific Employee already has a specific Skill
    assigned — an EMPLOYEE session has no legitimate reason to probe that."""
    async with _client() as client:
        await _login(client, email="casey@sails.example.com")
        response = await client.get(
            "/api/assignments/duplicate-check",
            params={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_SQL_ID)},
        )
        assert response.status_code == 403
        assert response.json()["code"] == "FORBIDDEN_NOT_HR_ADMIN"
