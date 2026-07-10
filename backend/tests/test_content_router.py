"""Router-level tests for content/router.py's match-for-skill endpoint (Story 3.4).

Uses the real `app.main.app` via ASGITransport for the HTTP-level assertions
(same loop_scope="module" pattern and rationale as test_assignments_router.py),
plus a *private* engine/session (create_async_engine(settings.DATABASE_URL),
matching test_assignments_repository.py's Story 3.1 pattern) purely for
inserting/cleaning up ContentCatalog test rows directly — NOT the `db_session`
fixture in conftest.py, which calls Base.metadata.drop_all() on teardown and
wipes the shared dev DB (the exact reason test_content_repository.py/
test_content_service.py are excluded from full-suite runs; see deferred-work.md).

content_catalog is empty in this environment (Story 2.3's batch ingestion is
still backlog) — every test here explicitly creates and cleans up its own
rows rather than relying on any pre-existing seeded content.
"""
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import ContentCatalog
from app.core.config import settings
from app.core.seeds import SKILL_DATA_VIZ_ID, SKILL_PYTHON_ID
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


async def _create_content(*, skill_id, title: str) -> uuid.UUID:
    async with _session_factory() as session:
        content = ContentCatalog(
            skill_id=skill_id,
            title=title,
            description="Test content for Story 3.4 content-match endpoint",
            type="VIDEO",
            url="https://youtube.com/watch?v=test",
            embedding=[0.1] * 384,
            source="YOUTUBE",
            content_metadata={"video_id": "test", "duration": 300},
        )
        session.add(content)
        await session.commit()
        return content.id


async def _delete_content(content_id: uuid.UUID) -> None:
    async with _session_factory() as session:
        await session.execute(delete(ContentCatalog).where(ContentCatalog.id == content_id))
        await session.commit()


async def test_content_match_returns_the_content_when_one_exists_for_the_skill():
    content_id = await _create_content(skill_id=SKILL_DATA_VIZ_ID, title="Intro to Charts")
    try:
        async with _client() as client:
            await _login(client)
            response = await client.get("/api/content/match", params={"skill_id": str(SKILL_DATA_VIZ_ID)})

            assert response.status_code == 200
            body = response.json()
            assert body is not None
            assert body["id"] == str(content_id)
            assert body["title"] == "Intro to Charts"
            assert body["skill_id"] == str(SKILL_DATA_VIZ_ID)
            assert "embedding" not in body
    finally:
        await _delete_content(content_id)


async def test_content_match_returns_null_when_no_content_matches_the_skill():
    """The common case in this environment today — content_catalog is empty
    for most skills since Story 2.3's ingestion job is still backlog."""
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/content/match", params={"skill_id": str(SKILL_PYTHON_ID)})

        assert response.status_code == 200
        assert response.json() is None


async def test_content_match_requires_authentication():
    async with _client() as client:
        response = await client.get("/api/content/match", params={"skill_id": str(SKILL_DATA_VIZ_ID)})
        assert response.status_code == 401


async def test_content_match_is_deterministic_across_multiple_matching_rows():
    """Code review round 2: the first-match placeholder (TODO(Story 2.4)) must
    return the same row every time given multiple candidates, not whatever
    order Postgres happens to return without an ORDER BY."""
    older_id = await _create_content(skill_id=SKILL_DATA_VIZ_ID, title="Older Video")
    newer_id = await _create_content(skill_id=SKILL_DATA_VIZ_ID, title="Newer Video")
    try:
        async with _client() as client:
            await _login(client)
            first = await client.get("/api/content/match", params={"skill_id": str(SKILL_DATA_VIZ_ID)})
            second = await client.get("/api/content/match", params={"skill_id": str(SKILL_DATA_VIZ_ID)})

            assert first.status_code == 200
            assert second.status_code == 200
            assert first.json()["id"] == second.json()["id"]
            # Deterministic by (ingested_at, id) — the earlier-inserted row wins.
            assert first.json()["id"] == str(older_id)
    finally:
        await _delete_content(older_id)
        await _delete_content(newer_id)


async def test_content_match_rejects_malformed_skill_id():
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/content/match", params={"skill_id": "not-a-uuid"})
        assert response.status_code == 422
