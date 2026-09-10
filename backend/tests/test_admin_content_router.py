"""Router-level tests for content/admin_content_router.py's POST /attach
endpoint (Story 6.8, FR-18).

Same private-engine/`_login()` pattern as test_skills_router.py -- NOT the
`db_session` fixture, which wipes the shared dev DB on teardown. Deleting the
Skill created for each test also cascade-deletes any content_catalog rows
attached to it (migration 007, ON DELETE CASCADE) -- no separate content
cleanup needed.
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


@pytest.mark.parametrize("source", ["YOUTUBE", "UDEMY", "MANUAL"])
async def test_attach_content_as_hr_admin_returns_201_with_full_response_shape(source):
    name = f"Attach Content Happy Path {source} {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.post(
                "/api/admin/content/attach",
                json={
                    "skill_id": skill_id,
                    "title": "A Great Course",
                    "source": source,
                    "url": "https://example.com/a-course",
                    "duration_hours": 3.5,
                },
            )

            assert response.status_code == 201
            body = response.json()
            assert body["title"] == "A Great Course"
            assert body["source"] == source
            assert body["url"] == "https://example.com/a-course"
            assert body["skill_id"] == skill_id
            assert body["type"] == "VIDEO"
            # No video_id here: this test's URL isn't YouTube-recognizable
            # regardless of source -- see test_attach_content_youtube_url_response_includes_video_id
            # for the YOUTUBE + real youtube.com URL case.
            assert body["metadata"] == {"duration_hours": 3.5, "duration": 12600}
            assert "embedding" not in body
            assert "attached_by" not in body
            assert "origin" not in body
    finally:
        await _delete_skill_by_name(name)


async def test_attach_content_youtube_url_response_includes_video_id():
    name = f"Attach Content Youtube Video Id {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.post(
                "/api/admin/content/attach",
                json={
                    "skill_id": skill_id,
                    "title": "A Great Video",
                    "source": "YOUTUBE",
                    "url": "https://www.youtube.com/watch?v=abc123XYZ_",
                    "duration_hours": 1.0,
                },
            )

            assert response.status_code == 201
            assert response.json()["metadata"] == {
                "duration_hours": 1.0,
                "duration": 3600,
                "video_id": "abc123XYZ_",
            }
    finally:
        await _delete_skill_by_name(name)


async def test_attach_content_duration_hours_omitted_omits_metadata():
    name = f"Attach Content No Duration {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.post(
                "/api/admin/content/attach",
                json={
                    "skill_id": skill_id,
                    "title": "A Great Course",
                    "source": "MANUAL",
                    "url": "https://example.com/a-course",
                },
            )

            assert response.status_code == 201
            assert response.json()["metadata"] is None
    finally:
        await _delete_skill_by_name(name)


async def test_attach_content_as_employee_returns_403():
    name = f"Attach Content Employee {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            await _login(client, email="casey@sails.example.com")
            response = await client.post(
                "/api/admin/content/attach",
                json={
                    "skill_id": skill_id,
                    "title": "A Great Course",
                    "source": "MANUAL",
                    "url": "https://example.com/a-course",
                },
            )

            assert response.status_code == 403
    finally:
        await _delete_skill_by_name(name)


async def test_attach_content_requires_authentication():
    async with _client() as client:
        response = await client.post(
            "/api/admin/content/attach",
            json={
                "skill_id": str(uuid.uuid4()),
                "title": "A Great Course",
                "source": "MANUAL",
                "url": "https://example.com/a-course",
            },
        )
        assert response.status_code == 401


async def test_attach_content_nonexistent_skill_returns_404():
    async with _client() as client:
        await _login(client)
        response = await client.post(
            "/api/admin/content/attach",
            json={
                "skill_id": str(uuid.uuid4()),
                "title": "A Great Course",
                "source": "MANUAL",
                "url": "https://example.com/a-course",
            },
        )
        assert response.status_code == 404


async def test_attach_content_rejects_malformed_url():
    name = f"Attach Content Bad URL {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.post(
                "/api/admin/content/attach",
                json={"skill_id": skill_id, "title": "A Great Course", "source": "MANUAL", "url": "not-a-url"},
            )

            assert response.status_code == 422
    finally:
        await _delete_skill_by_name(name)


async def test_attach_content_rejects_blank_title():
    name = f"Attach Content Blank Title {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.post(
                "/api/admin/content/attach",
                json={
                    "skill_id": skill_id,
                    "title": "   ",
                    "source": "MANUAL",
                    "url": "https://example.com/a-course",
                },
            )

            assert response.status_code == 422
    finally:
        await _delete_skill_by_name(name)


async def test_attach_content_rejects_invalid_source():
    name = f"Attach Content Bad Source {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.post(
                "/api/admin/content/attach",
                json={
                    "skill_id": skill_id,
                    "title": "A Great Course",
                    "source": "VIMEO",
                    "url": "https://example.com/a-course",
                },
            )

            assert response.status_code == 422
    finally:
        await _delete_skill_by_name(name)


async def test_attach_content_rejects_non_positive_duration():
    name = f"Attach Content Bad Duration {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.post(
                "/api/admin/content/attach",
                json={
                    "skill_id": skill_id,
                    "title": "A Great Course",
                    "source": "MANUAL",
                    "url": "https://example.com/a-course",
                    "duration_hours": 0,
                },
            )

            assert response.status_code == 422
    finally:
        await _delete_skill_by_name(name)


async def test_attach_content_rejects_unknown_field():
    name = f"Attach Content Unknown Field {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.post(
                "/api/admin/content/attach",
                json={
                    "skill_id": skill_id,
                    "title": "A Great Course",
                    "source": "MANUAL",
                    "url": "https://example.com/a-course",
                    "type": "VIDEO",
                },
            )

            assert response.status_code == 422
    finally:
        await _delete_skill_by_name(name)
