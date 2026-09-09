"""Router-level tests for skills/router.py's create endpoint (Story 6.2, FR-20).

Uses the real `app.main.app` via ASGITransport for the HTTP-level assertions
plus a *private* engine/session (create_async_engine(settings.DATABASE_URL))
purely for cleaning up rows this file creates -- NOT the `db_session`
fixture in conftest.py, which calls Base.metadata.drop_all() on teardown and
wipes the shared dev DB. Mirrors test_content_router.py's pattern exactly.
"""
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.main import app
from app.skills.models import Skill

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


async def _delete_skill_by_name(name: str) -> None:
    async with _session_factory() as session:
        await session.execute(delete(Skill).where(Skill.name == name))
        await session.commit()


async def test_create_skill_as_hr_admin_returns_201_with_full_response_shape():
    name = f"Router Create Test {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            response = await client.post("/api/admin/skills", json={"name": name, "description": "A new skill"})

            assert response.status_code == 201
            body = response.json()
            assert body["name"] == name
            assert body["description"] == "A new skill"
            assert body["ever_assigned"] is False
            assert "id" in body
            assert "embedding" not in body
    finally:
        await _delete_skill_by_name(name)


async def test_create_skill_with_same_name_different_case_returns_409_with_existing_skill():
    name = f"Conflict Test {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            first = await client.post("/api/admin/skills", json={"name": name})
            assert first.status_code == 201
            existing_id = first.json()["id"]

            second = await client.post("/api/admin/skills", json={"name": name.upper()})

            assert second.status_code == 409
            body = second.json()
            # Standard error envelope (core/errors.py::_error_body) must survive
            # alongside the extra existing_skill payload, not be clobbered by it.
            assert body["status"] == "error"
            assert body["code"] == "SKILL_NAME_CONFLICT"
            assert "message" in body
            assert "timestamp" in body
            assert body["existing_skill"]["id"] == existing_id
            assert body["existing_skill"]["name"] == name
    finally:
        await _delete_skill_by_name(name)


async def test_create_skill_with_exact_same_name_twice_returns_409():
    name = f"Exact Duplicate Test {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            first = await client.post("/api/admin/skills", json={"name": name})
            assert first.status_code == 201
            existing_id = first.json()["id"]

            second = await client.post("/api/admin/skills", json={"name": name})

            assert second.status_code == 409
            body = second.json()
            assert body["existing_skill"]["id"] == existing_id
            assert body["existing_skill"]["name"] == name
    finally:
        await _delete_skill_by_name(name)


async def test_create_skill_as_employee_returns_403():
    name = f"Employee Forbidden Test {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client, email="casey@sails.example.com")
            response = await client.post("/api/admin/skills", json={"name": name})

            assert response.status_code == 403
    finally:
        await _delete_skill_by_name(name)


async def test_create_skill_requires_authentication():
    async with _client() as client:
        response = await client.post("/api/admin/skills", json={"name": "Unauthenticated Attempt"})
        assert response.status_code == 401


async def test_create_skill_rejects_blank_name():
    async with _client() as client:
        await _login(client)
        response = await client.post("/api/admin/skills", json={"name": "   "})
        assert response.status_code == 422


async def test_create_skill_rejects_missing_name():
    async with _client() as client:
        await _login(client)
        response = await client.post("/api/admin/skills", json={"description": "no name given"})
        assert response.status_code == 422


async def test_create_skill_rejects_name_over_255_chars():
    async with _client() as client:
        await _login(client)
        response = await client.post("/api/admin/skills", json={"name": "x" * 256})
        assert response.status_code == 422
