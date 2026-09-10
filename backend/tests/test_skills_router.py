"""Router-level tests for skills/router.py's endpoints (Story 6.2 create,
FR-20; Story 6.3 update/delete, FR-21/22).

Uses the real `app.main.app` via ASGITransport for the HTTP-level assertions
plus a *private* engine/session (create_async_engine(settings.DATABASE_URL))
purely for cleaning up rows this file creates -- NOT the `db_session`
fixture in conftest.py, which calls Base.metadata.drop_all() on teardown and
wipes the shared dev DB. Mirrors test_content_router.py's pattern exactly.
"""
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import AdminApiKey, ContentCatalog, OrgApiCredential
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


async def _lock_skill(skill_id: str) -> None:
    async with _session_factory() as session:
        skill = (await session.execute(select(Skill).where(Skill.id == skill_id))).scalar_one()
        skill.ever_assigned = True
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


# ---------------------------------------------------------------------------
# Story 6.3: PATCH / DELETE /api/admin/skills/{id}
# ---------------------------------------------------------------------------


async def test_update_skill_as_hr_admin_returns_200_with_updated_fields():
    name = f"Router Update Source {uuid.uuid4().hex[:8]}"
    new_name = f"Router Update Target {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name, "description": "before"})
            skill_id = created.json()["id"]

            response = await client.patch(
                f"/api/admin/skills/{skill_id}", json={"name": new_name, "description": "after"}
            )

            assert response.status_code == 200
            body = response.json()
            assert body["id"] == skill_id
            assert body["name"] == new_name
            assert body["description"] == "after"
            assert "embedding" not in body
    finally:
        await _delete_skill_by_name(name)
        await _delete_skill_by_name(new_name)


async def test_update_skill_partial_body_leaves_omitted_field_untouched():
    name = f"Router Partial Update {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name, "description": "keep me"})
            skill_id = created.json()["id"]

            response = await client.patch(f"/api/admin/skills/{skill_id}", json={"description": "changed"})

            assert response.status_code == 200
            body = response.json()
            assert body["name"] == name
            assert body["description"] == "changed"
    finally:
        await _delete_skill_by_name(name)


async def test_update_skill_explicit_null_description_clears_it():
    name = f"Router Null Description {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name, "description": "has a value"})
            skill_id = created.json()["id"]

            response = await client.patch(f"/api/admin/skills/{skill_id}", json={"description": None})

            assert response.status_code == 200
            assert response.json()["description"] is None
    finally:
        await _delete_skill_by_name(name)


async def test_update_skill_rejects_null_name():
    name = f"Router Null Name {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.patch(f"/api/admin/skills/{skill_id}", json={"name": None})

            assert response.status_code == 422
    finally:
        await _delete_skill_by_name(name)


async def test_update_skill_rejects_blank_name():
    name = f"Router Update Blank {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.patch(f"/api/admin/skills/{skill_id}", json={"name": "   "})

            assert response.status_code == 422
    finally:
        await _delete_skill_by_name(name)


async def test_update_skill_rejects_name_over_255_chars():
    name = f"Router Update Too Long {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.patch(f"/api/admin/skills/{skill_id}", json={"name": "x" * 256})

            assert response.status_code == 422
    finally:
        await _delete_skill_by_name(name)


async def test_update_skill_rejects_unknown_field():
    name = f"Router Update Unknown Field {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.patch(f"/api/admin/skills/{skill_id}", json={"ever_assigned": True})

            assert response.status_code == 422
    finally:
        await _delete_skill_by_name(name)


async def test_update_skill_with_duplicate_name_returns_409_excluding_self():
    first_name = f"Router Dup Rename A {uuid.uuid4().hex[:8]}"
    second_name = f"Router Dup Rename B {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            first = await client.post("/api/admin/skills", json={"name": first_name})
            first_id = first.json()["id"]
            second = await client.post("/api/admin/skills", json={"name": second_name})
            second_id = second.json()["id"]

            # Resubmitting its own current name is not a conflict.
            self_resubmit = await client.patch(f"/api/admin/skills/{first_id}", json={"name": first_name})
            assert self_resubmit.status_code == 200

            conflict = await client.patch(f"/api/admin/skills/{second_id}", json={"name": first_name})
            assert conflict.status_code == 409
            body = conflict.json()
            # Unlike create's 409 (Story 6.2), rename's 409 carries no
            # existing_skill redirect payload (AC1, code review 2026-09-09).
            assert "existing_skill" not in body
    finally:
        await _delete_skill_by_name(first_name)
        await _delete_skill_by_name(second_name)


async def test_update_locked_skill_returns_403():
    name = f"Router Locked Update {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]
            await _lock_skill(skill_id)

            response = await client.patch(f"/api/admin/skills/{skill_id}", json={"name": "Should Not Apply"})

            assert response.status_code == 403
            assert "assigned" in response.json()["message"].lower()
    finally:
        await _delete_skill_by_name(name)


async def test_update_nonexistent_skill_returns_404():
    async with _client() as client:
        await _login(client)
        response = await client.patch(f"/api/admin/skills/{uuid.uuid4()}", json={"name": "Whatever"})
        assert response.status_code == 404


async def test_update_skill_as_employee_returns_403():
    name = f"Router Employee Update {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            await _login(client, email="casey@sails.example.com")
            response = await client.patch(f"/api/admin/skills/{skill_id}", json={"name": "New Name"})

            assert response.status_code == 403
    finally:
        await _delete_skill_by_name(name)


async def test_update_skill_requires_authentication():
    async with _client() as client:
        response = await client.patch(f"/api/admin/skills/{uuid.uuid4()}", json={"name": "New Name"})
        assert response.status_code == 401


async def test_delete_skill_as_hr_admin_returns_204_and_hard_deletes():
    name = f"Router Delete {uuid.uuid4().hex[:8]}"
    async with _client() as client:
        await _login(client)
        created = await client.post("/api/admin/skills", json={"name": name})
        skill_id = created.json()["id"]

        response = await client.delete(f"/api/admin/skills/{skill_id}")
        assert response.status_code == 204

        async with _session_factory() as session:
            result = await session.execute(select(Skill).where(Skill.id == skill_id))
            assert result.scalar_one_or_none() is None


async def test_delete_skill_cascades_attached_content_catalog_rows():
    name = f"Router Delete With Content {uuid.uuid4().hex[:8]}"
    async with _client() as client:
        await _login(client)
        created = await client.post("/api/admin/skills", json={"name": name})
        skill_id = created.json()["id"]

        async with _session_factory() as session:
            content = ContentCatalog(
                skill_id=skill_id,
                title="Router Attached Content",
                type="VIDEO",
                url="https://example.com/router-video",
                embedding=[0.2] * 384,
                source="MANUAL",
            )
            session.add(content)
            await session.commit()
            content_id = content.id

        response = await client.delete(f"/api/admin/skills/{skill_id}")
        assert response.status_code == 204

        async with _session_factory() as session:
            skill_result = await session.execute(select(Skill).where(Skill.id == skill_id))
            assert skill_result.scalar_one_or_none() is None
            content_result = await session.execute(select(ContentCatalog).where(ContentCatalog.id == content_id))
            assert content_result.scalar_one_or_none() is None


async def test_delete_locked_skill_returns_403_and_does_not_delete():
    name = f"Router Locked Delete {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]
            await _lock_skill(skill_id)

            response = await client.delete(f"/api/admin/skills/{skill_id}")

            assert response.status_code == 403
            assert "assigned" in response.json()["message"].lower()

        async with _session_factory() as session:
            result = await session.execute(select(Skill).where(Skill.id == skill_id))
            assert result.scalar_one_or_none() is not None
    finally:
        await _delete_skill_by_name(name)


async def test_delete_nonexistent_skill_returns_404():
    async with _client() as client:
        await _login(client)
        response = await client.delete(f"/api/admin/skills/{uuid.uuid4()}")
        assert response.status_code == 404


async def test_delete_skill_as_employee_returns_403():
    name = f"Router Employee Delete {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            await _login(client, email="casey@sails.example.com")
            response = await client.delete(f"/api/admin/skills/{skill_id}")

            assert response.status_code == 403
    finally:
        await _delete_skill_by_name(name)


async def test_delete_skill_requires_authentication():
    async with _client() as client:
        response = await client.delete(f"/api/admin/skills/{uuid.uuid4()}")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Story 6.6: POST /api/admin/skills/{id}/content-lookup
# ---------------------------------------------------------------------------


async def _clear_credentials() -> None:
    async with _session_factory() as session:
        await session.execute(delete(AdminApiKey).where(AdminApiKey.source == "YOUTUBE"))
        await session.execute(delete(OrgApiCredential).where(OrgApiCredential.source == "UDEMY"))
        await session.commit()


def _fake_youtube_search(api_key, query, max_results):
    return [
        {
            "video_id": "router-yt-1",
            "title": "Router YouTube Result",
            "description": "desc",
            "thumbnail_url": "https://img.example.com/router-yt-1.jpg",
        }
    ]


def _fake_youtube_durations(api_key, video_ids):
    return {"router-yt-1": "PT5M0S"}


def _fake_udemy_search(client_id, client_secret, query, max_results):
    return [
        {
            "course_id": 555,
            "title": "Router Udemy Result",
            "url": "/course/router-udemy-result/",
            "thumbnail_url": "https://img.udemy.com/555.jpg",
            "content_info": "2 total hours",
        }
    ]


async def test_content_lookup_as_hr_admin_with_both_sources_configured_returns_both(monkeypatch):
    name = f"Content Lookup Both {uuid.uuid4().hex[:8]}"
    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _fake_youtube_search)
    monkeypatch.setattr("app.content.service.youtube_client.get_video_durations", _fake_youtube_durations)
    monkeypatch.setattr("app.content.service.udemy_client.search_courses", _fake_udemy_search)
    monkeypatch.setattr("app.content.service.settings.UDEMY_ORGANIZATION_SUBDOMAIN", "sails")
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            await client.put("/api/admin/api-keys/youtube", json={"key": "a-real-yt-key"})
            await client.put(
                "/api/admin/api-keys/udemy", json={"client_id": "cid", "client_secret": "csecret"}
            )

            response = await client.post(
                f"/api/admin/skills/{skill_id}/content-lookup", json={"query": "Python"}
            )

            assert response.status_code == 200
            body = response.json()
            assert body["errors"] == []
            sources = {r["source"] for r in body["results"]}
            assert sources == {"YOUTUBE", "UDEMY"}
            youtube_result = next(r for r in body["results"] if r["source"] == "YOUTUBE")
            assert youtube_result["url"] == "https://www.youtube.com/watch?v=router-yt-1"
            udemy_result = next(r for r in body["results"] if r["source"] == "UDEMY")
            assert udemy_result["url"] == "https://sails.udemy.com/course/router-udemy-result/"
    finally:
        await _delete_skill_by_name(name)
        await _clear_credentials()


async def test_content_lookup_with_no_credentials_configured_returns_no_credential_errors():
    name = f"Content Lookup No Creds {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.post(
                f"/api/admin/skills/{skill_id}/content-lookup", json={"query": "Python"}
            )

            assert response.status_code == 200
            body = response.json()
            assert body["results"] == []
            errors_by_source = {e["source"]: e["error"] for e in body["errors"]}
            assert errors_by_source == {"YOUTUBE": "no_credential", "UDEMY": "no_credential"}
    finally:
        await _delete_skill_by_name(name)


async def test_content_lookup_youtube_rate_limited_response_shape(monkeypatch):
    """Code review (2026-09-10): the rate_limited/invalid_credential/
    source_error variants were previously only exercised at the
    service-unit level -- this asserts the real HTTP response shape."""
    from app.content.youtube_client import QuotaExceededError

    name = f"Content Lookup Rate Limited {uuid.uuid4().hex[:8]}"

    def _raise_quota(api_key, query, max_results):
        raise QuotaExceededError("quota exhausted")

    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _raise_quota)
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]
            await client.put("/api/admin/api-keys/youtube", json={"key": "a-key"})

            response = await client.post(
                f"/api/admin/skills/{skill_id}/content-lookup", json={"query": "Python"}
            )

            assert response.status_code == 200
            body = response.json()
            assert body["results"] == []
            errors_by_source = {e["source"]: e["error"] for e in body["errors"]}
            assert errors_by_source["YOUTUBE"] == "rate_limited"
    finally:
        await _delete_skill_by_name(name)
        await _clear_credentials()


async def test_content_lookup_udemy_invalid_credential_response_shape(monkeypatch):
    from app.content.udemy_client import InvalidCredentialError

    name = f"Content Lookup Invalid Cred {uuid.uuid4().hex[:8]}"

    def _raise_invalid(client_id, client_secret, query, max_results):
        raise InvalidCredentialError("bad credential")

    monkeypatch.setattr("app.content.service.udemy_client.search_courses", _raise_invalid)
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]
            await client.put(
                "/api/admin/api-keys/udemy", json={"client_id": "cid", "client_secret": "csecret"}
            )

            response = await client.post(
                f"/api/admin/skills/{skill_id}/content-lookup", json={"query": "Python"}
            )

            assert response.status_code == 200
            body = response.json()
            assert body["results"] == []
            errors_by_source = {e["source"]: e["error"] for e in body["errors"]}
            assert errors_by_source["UDEMY"] == "invalid_credential"
    finally:
        await _delete_skill_by_name(name)
        await _clear_credentials()


async def test_content_lookup_source_error_response_shape(monkeypatch):
    name = f"Content Lookup Source Error {uuid.uuid4().hex[:8]}"

    def _raise_generic(api_key, query, max_results):
        raise Exception("boom")

    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _raise_generic)
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]
            await client.put("/api/admin/api-keys/youtube", json={"key": "a-key"})

            response = await client.post(
                f"/api/admin/skills/{skill_id}/content-lookup", json={"query": "Python"}
            )

            assert response.status_code == 200
            body = response.json()
            assert body["results"] == []
            errors_by_source = {e["source"]: e["error"] for e in body["errors"]}
            assert errors_by_source["YOUTUBE"] == "source_error"
    finally:
        await _delete_skill_by_name(name)
        await _clear_credentials()


async def test_content_lookup_as_employee_returns_403():
    name = f"Content Lookup Employee {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            await _login(client, email="casey@sails.example.com")
            response = await client.post(
                f"/api/admin/skills/{skill_id}/content-lookup", json={"query": "Python"}
            )

            assert response.status_code == 403
    finally:
        await _delete_skill_by_name(name)


async def test_content_lookup_requires_authentication():
    async with _client() as client:
        response = await client.post(
            f"/api/admin/skills/{uuid.uuid4()}/content-lookup", json={"query": "Python"}
        )
        assert response.status_code == 401


async def test_content_lookup_nonexistent_skill_returns_404():
    async with _client() as client:
        await _login(client)
        response = await client.post(
            f"/api/admin/skills/{uuid.uuid4()}/content-lookup", json={"query": "Python"}
        )
        assert response.status_code == 404


async def test_content_lookup_rejects_blank_query():
    name = f"Content Lookup Blank Query {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.post(
                f"/api/admin/skills/{skill_id}/content-lookup", json={"query": "   "}
            )

            assert response.status_code == 422
    finally:
        await _delete_skill_by_name(name)


async def test_content_lookup_rejects_missing_query():
    name = f"Content Lookup Missing Query {uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post("/api/admin/skills", json={"name": name})
            skill_id = created.json()["id"]

            response = await client.post(f"/api/admin/skills/{skill_id}/content-lookup", json={})

            assert response.status_code == 422
    finally:
        await _delete_skill_by_name(name)
