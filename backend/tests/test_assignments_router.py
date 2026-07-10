"""Router-level tests for assignments/router.py (Story 3.4).

Uses the real `app.main.app` via ASGITransport. Unlike test_login.py/
test_logout.py (which never touch the DB — authenticate() reads the mock
_MOCK_ACCOUNTS dict, not a real query), this file is the first to exercise
get_db()'s real per-request session against the shared app.core.db.engine
repeatedly across multiple test functions. Plain function-scoped
@pytest.mark.asyncio (pytest's default) reproduces the known cross-event-loop
asyncpg pool corruption ("cannot perform operation: another operation is in
progress") the moment a second DB-touching test runs — each test function
gets its own event loop, but the shared engine's pooled connections don't
get released cleanly across that boundary. loop_scope="module" (this file's
own established fix, per Story 1.7/3.1/3.3's precedent) gives every test in
this file one shared loop instead, avoiding the cross-loop reuse. This can
in turn collide with *other* module-scoped-loop files sharing the same
engine (test_database_schema.py) — see deferred-work.md's running thread on
this bug class; excluded via -k if that recurs during the full suite run.

Per Story 1.7's own hard-won lesson: do NOT add individual
@pytest.mark.asyncio decorators to the test functions below — they silently
override this module-level loop_scope. The bare `pytestmark` line is enough.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.seed_ids import CASEY_ID, RITA_ID
from app.core.seeds import SKILL_DATA_VIZ_ID, SKILL_PYTHON_ID
from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="module")


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _login(client: AsyncClient, email: str = "rita@sails.example.com") -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": "demo123"})
    assert response.status_code == 200
    set_cookie_header = response.headers.get("set-cookie", "")
    prefix = f"{settings.SESSION_COOKIE_NAME}="
    assert set_cookie_header.startswith(prefix)
    token = set_cookie_header.split(";", 1)[0][len(prefix) :]
    client.cookies.clear()
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)
    return token


async def test_list_employees_returns_all_demo_employees_for_authenticated_caller():
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/assignments/employees")

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) >= 5
        emails = {e["email"] for e in body}
        assert "rita@sails.example.com" in emails
        assert "casey@sails.example.com" in emails
        # Response shape: id, name, email, role — no extra/internal fields.
        sample = next(e for e in body if e["email"] == "casey@sails.example.com")
        assert set(sample.keys()) == {"id", "name", "email", "role"}
        assert sample["id"] == str(CASEY_ID)
        assert sample["role"] == "EMPLOYEE"


async def test_list_employees_requires_authentication():
    async with _client() as client:
        response = await client.get("/api/assignments/employees")
        assert response.status_code == 401


async def test_list_employees_accessible_to_employee_role_too():
    """Reading the employee roster is not HR_ADMIN-gated — any authenticated
    session can see it (this is a read-only directory listing, not an
    assignment-scoped read)."""
    async with _client() as client:
        await _login(client, email="casey@sails.example.com")
        response = await client.get("/api/assignments/employees")
        assert response.status_code == 200


async def test_list_employees_search_filters_by_name():
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/assignments/employees", params={"search": "casey"})

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["email"] == "casey@sails.example.com"


async def test_list_employees_search_filters_by_email():
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/assignments/employees", params={"search": "rita@sails"})

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == str(RITA_ID)


async def test_list_employees_search_is_case_insensitive():
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/assignments/employees", params={"search": "CASEY"})

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["email"] == "casey@sails.example.com"


async def test_list_employees_search_no_match_returns_empty_list():
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/assignments/employees", params={"search": "nonexistent-xyz"})

        assert response.status_code == 200
        assert response.json() == []


async def test_list_skills_returns_all_seeded_skills_for_authenticated_caller():
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/assignments/skills")

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) >= 5
        names = {s["name"] for s in body}
        assert "Data Visualization" in names
        assert "Python Programming" in names
        # Response shape: id, name, description — no `embedding` (never
        # serialize the 384-dim vector to a list response).
        sample = next(s for s in body if s["name"] == "Data Visualization")
        assert set(sample.keys()) == {"id", "name", "description"}
        assert sample["id"] == str(SKILL_DATA_VIZ_ID)


async def test_list_skills_requires_authentication():
    async with _client() as client:
        response = await client.get("/api/assignments/skills")
        assert response.status_code == 401


async def test_list_skills_search_filters_by_name():
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/assignments/skills", params={"search": "Python"})

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == str(SKILL_PYTHON_ID)


async def test_list_skills_search_filters_by_description():
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/assignments/skills", params={"search": "charts"})

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == str(SKILL_DATA_VIZ_ID)


async def test_list_skills_search_no_match_returns_empty_list():
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/assignments/skills", params={"search": "nonexistent-xyz"})

        assert response.status_code == 200
        assert response.json() == []
