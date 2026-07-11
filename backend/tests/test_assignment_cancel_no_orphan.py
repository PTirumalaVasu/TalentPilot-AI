"""Backend-level guarantee for Story 3.6 (Cancel Assignment Flow Leaves No
Orphaned Record), AC5: the specific read-only GET sequence the modal's Steps
1-3 issue while stepping through the flow (employee list, skill list,
duplicate-check with no pre-existing duplicate, content-match) must never
write an Assignment row on their own. Cancel/Close/Escape/backdrop-click
never call POST /api/assignments (verified at the frontend in
AssignmentModal.test.tsx) — this test proves that exact call sequence has no
side effects against the real database, independent of that frontend-mock
guarantee (it does not exhaustively prove every possible input to these
endpoints is side-effect-free, e.g. the duplicate-exists branch or malformed
params — see deferred-work.md).

Same real-app + loop_scope="module" + private-engine pattern as
test_assignments_create_route.py/test_assignments_router.py — see those
files' module docstrings for why plain function-scoped @pytest.mark.asyncio
doesn't work here (this is a live-DB-touching router), and why conftest.py's
db_session/test_engine fixtures must not be used (Base.metadata.drop_all()
DB-wipe bug, tracked in deferred-work.md).
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import Assignment
from app.core.config import settings
from app.core.seed_ids import JORDAN_ID
from app.core.seeds import SKILL_SQL_ID
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


async def _cleanup_assignments_for(employee_id, skill_id) -> None:
    async with _session_factory() as session:
        await session.execute(
            delete(Assignment).where(Assignment.employee_id == employee_id, Assignment.skill_id == skill_id)
        )
        await session.commit()


async def _assignment_count_for(employee_id, skill_id) -> int:
    async with _session_factory() as session:
        result = await session.execute(
            select(Assignment).where(Assignment.employee_id == employee_id, Assignment.skill_id == skill_id)
        )
        return len(result.scalars().all())


async def test_stepping_through_the_modals_read_endpoints_without_posting_creates_no_assignment():
    """Reproduces the exact GET sequence AssignmentModal.tsx's Steps 1-3
    trigger (list employees -> list skills -> duplicate-check -> content
    match) for a known (employee_id, skill_id) pair, then asserts zero
    Assignment rows exist for that pair -- proving this specific no-duplicate
    call sequence has no side effects, not just that the frontend never calls
    the create endpoint (see the module docstring for what this does and does
    not exhaustively cover)."""
    await _cleanup_assignments_for(JORDAN_ID, SKILL_SQL_ID)
    try:
        async with _client() as client:
            await _login(client)

            employees_response = await client.get("/api/assignments/employees")
            assert employees_response.status_code == 200
            assert isinstance(employees_response.json(), list)

            skills_response = await client.get("/api/assignments/skills")
            assert skills_response.status_code == 200
            assert isinstance(skills_response.json(), list)

            duplicate_check_response = await client.get(
                "/api/assignments/duplicate-check",
                params={"employee_id": str(JORDAN_ID), "skill_id": str(SKILL_SQL_ID)},
            )
            assert duplicate_check_response.status_code == 200
            assert duplicate_check_response.json() == []

            content_match_response = await client.get(
                "/api/content/match", params={"skill_id": str(SKILL_SQL_ID)}
            )
            assert content_match_response.status_code == 200

            # The one and only write path (POST /api/assignments) is never
            # called -- this is the literal behavior Cancel/Close/Escape/
            # backdrop-click all reduce to on the frontend.
            assert await _assignment_count_for(JORDAN_ID, SKILL_SQL_ID) == 0
    finally:
        await _cleanup_assignments_for(JORDAN_ID, SKILL_SQL_ID)
