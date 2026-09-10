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

from app.assignments.models import Assignment, ContentCatalog
from app.core.config import settings
from app.core.seed_ids import CASEY_ID, RITA_ID
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


async def test_reject_content_happy_path_returns_204():
    name = f"Reject Content Happy Path {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]
            attached = await client.post(
                "/api/admin/content/attach",
                json={
                    "skill_id": skill_id,
                    "title": "A Course To Reject",
                    "source": "MANUAL",
                    "url": "https://example.com/a-course",
                },
            )
            content_id = attached.json()["id"]

            response = await client.delete(f"/api/admin/content/{content_id}/reject")

            assert response.status_code == 204
            assert response.content == b""

            # Confirm the row is actually gone, not just a 204 lie.
            reattempt = await client.delete(f"/api/admin/content/{content_id}/reject")
            assert reattempt.status_code == 404
    finally:
        await _delete_skill_by_name(name)


async def test_reject_content_as_employee_returns_403():
    name = f"Reject Content Employee {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]
            attached = await client.post(
                "/api/admin/content/attach",
                json={
                    "skill_id": skill_id,
                    "title": "A Course",
                    "source": "MANUAL",
                    "url": "https://example.com/a-course",
                },
            )
            content_id = attached.json()["id"]

            await _login(client, email="casey@sails.example.com")
            response = await client.delete(f"/api/admin/content/{content_id}/reject")

            assert response.status_code == 403
    finally:
        await _delete_skill_by_name(name)


async def test_reject_content_requires_authentication():
    async with _client() as client:
        response = await client.delete(f"/api/admin/content/{uuid.uuid4()}/reject")
        assert response.status_code == 401


async def test_reject_content_nonexistent_id_returns_404():
    async with _client() as client:
        await _login(client)
        response = await client.delete(f"/api/admin/content/{uuid.uuid4()}/reject")
        assert response.status_code == 404


async def test_reject_content_batch_sourced_row_returns_404():
    """A row that isn't admin-sourced (origin != "ADMIN_LOOKUP") must 404,
    same as a genuinely nonexistent content_id (Scope Note 2) -- seeded
    directly via ORM since /attach always writes origin="ADMIN_LOOKUP"."""
    name = f"Reject Content Batch Sourced {uuid.uuid4().hex[:8]}"
    try:
        async with _session_factory() as session:
            skill = Skill(name=name, description="Test skill", embedding=[0.1] * 384)
            session.add(skill)
            await session.flush()
            content = ContentCatalog(
                skill_id=skill.id,
                title="Batch Video",
                description=None,
                type="VIDEO",
                url="https://youtube.com/watch?v=batch1",
                embedding=[0.2] * 384,
                source="YOUTUBE",
                content_metadata={"video_id": "batch1"},
                origin="BATCH",
            )
            session.add(content)
            await session.commit()
            content_id = content.id

        async with _client() as client:
            await _login(client)
            response = await client.delete(f"/api/admin/content/{content_id}/reject")
            assert response.status_code == 404
    finally:
        await _delete_skill_by_name(name)


async def test_reject_content_succeeds_when_referenced_by_an_assignment_and_nulls_content_id():
    """AC6/Scope Note 3: an Assignment.content_id pointing at the row being
    rejected must not 500 -- migration 010's ON DELETE SET NULL nulls it out
    instead."""
    name = f"Reject Content Referenced By Assignment {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]
            attached = await client.post(
                "/api/admin/content/attach",
                json={
                    "skill_id": skill_id,
                    "title": "A Course",
                    "source": "MANUAL",
                    "url": "https://example.com/a-course",
                },
            )
            content_id = attached.json()["id"]

            async with _session_factory() as session:
                assignment = Assignment(
                    employee_id=CASEY_ID,
                    skill_id=uuid.UUID(skill_id),
                    content_id=uuid.UUID(content_id),
                    assigned_by=RITA_ID,
                )
                session.add(assignment)
                await session.commit()
                assignment_id = assignment.id

            try:
                response = await client.delete(f"/api/admin/content/{content_id}/reject")
                assert response.status_code == 204

                async with _session_factory() as session:
                    refreshed = await session.get(Assignment, assignment_id)
                    assert refreshed.content_id is None
            finally:
                # Unconditional, independent of the asserts above -- if an
                # assertion fails, the Assignment row must still be removed
                # here so the outer finally's _delete_skill_by_name (below)
                # doesn't hit assignments_skill_id_fkey (no cascade) and
                # mask the real failure behind an unrelated IntegrityError
                # (review patch, 2026-09-10).
                async with _session_factory() as session:
                    leftover = await session.get(Assignment, assignment_id)
                    if leftover is not None:
                        await session.delete(leftover)
                        await session.commit()
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
