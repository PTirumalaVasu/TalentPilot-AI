"""Integration tests for DELETE /api/assignments/{assignment_id} (Story 3.7,
FR-15). Real app + ASGITransport + real Postgres, mirroring
test_drill_down_endpoint.py/test_override_endpoint.py's exact scaffolding
(see those files' module docstrings for why loop_scope="module" is needed
here)."""
import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import Assignment, AssignmentOverride, SkillProgress
from app.core.config import settings
from app.core.security import create_access_token
from app.core.seed_ids import CASEY_ID, RITA_ID
from app.core.seeds import SKILL_COMMUNICATION_ID, SKILL_DATA_VIZ_ID, SKILL_SQL_ID
from app.main import app

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
        await session.execute(delete(AssignmentOverride).where(AssignmentOverride.assignment_id == assignment_id))
        await session.execute(delete(SkillProgress).where(SkillProgress.assignment_id == assignment_id))
        await session.execute(delete(Assignment).where(Assignment.id == assignment_id))
        await session.commit()


async def _cleanup_assignments_for(employee_id: uuid.UUID, skill_id: uuid.UUID) -> None:
    async with _session_factory() as session:
        result = await session.execute(
            select(Assignment.id).where(Assignment.employee_id == employee_id, Assignment.skill_id == skill_id)
        )
        ids = [row[0] for row in result.all()]
        if ids:
            await session.execute(delete(AssignmentOverride).where(AssignmentOverride.assignment_id.in_(ids)))
            await session.execute(delete(SkillProgress).where(SkillProgress.assignment_id.in_(ids)))
        await session.execute(
            delete(Assignment).where(Assignment.employee_id == employee_id, Assignment.skill_id == skill_id)
        )
        await session.commit()


async def _create_assignment(client: AsyncClient, skill_id: uuid.UUID = SKILL_DATA_VIZ_ID) -> uuid.UUID:
    response = await client.post(
        "/api/assignments", json={"employee_id": str(CASEY_ID), "skill_id": str(skill_id)}
    )
    assert response.status_code == 201
    return uuid.UUID(response.json()["id"])


async def _fetch_assignment_row(assignment_id: uuid.UUID) -> Assignment:
    async with _session_factory() as session:
        result = await session.execute(select(Assignment).where(Assignment.id == assignment_id))
        return result.scalar_one()


# --- AC4: successful delete sets active/deleted_at/deleted_by, 204, no physical delete ---


async def test_delete_succeeds_returns_204_and_soft_deletes_the_row():
    await _cleanup_assignments_for(CASEY_ID, SKILL_DATA_VIZ_ID)
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            response = await client.delete(f"/api/assignments/{assignment_id}")
            assert response.status_code == 204
            assert response.content == b""

            row = await _fetch_assignment_row(assignment_id)
            assert row.active is False
            assert row.deleted_at is not None
            assert row.deleted_by == RITA_ID
        finally:
            await _cleanup_assignment(assignment_id)


# --- AC5: no restriction by Status or active HR Override ---


async def test_delete_succeeds_on_assignment_with_active_hr_override():
    await _cleanup_assignments_for(CASEY_ID, SKILL_DATA_VIZ_ID)
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            override_response = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "set", "reason": "verified live"}
            )
            assert override_response.status_code == 200

            response = await client.delete(f"/api/assignments/{assignment_id}")
            assert response.status_code == 204

            row = await _fetch_assignment_row(assignment_id)
            assert row.active is False

            # AR-4/AC5: the override record itself is untouched by delete --
            # still active, still readable directly, never modified.
            async with _session_factory() as session:
                result = await session.execute(
                    select(AssignmentOverride).where(AssignmentOverride.assignment_id == assignment_id)
                )
                override = result.scalar_one()
                assert override.active is True
                assert override.reason == "verified live"
        finally:
            await _cleanup_assignment(assignment_id)


async def test_delete_succeeds_on_assignment_with_recorded_watch_progress():
    """Deleting an assignment that already has real skill_progress data
    behaves identically to deleting a Not Started one (AC5) -- the
    progress-aware confirmation *copy* is Story 5.7's frontend concern; the
    backend delete itself has no status-based restriction."""
    await _cleanup_assignments_for(CASEY_ID, SKILL_DATA_VIZ_ID)
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
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

            response = await client.delete(f"/api/assignments/{assignment_id}")
            assert response.status_code == 204

            # skill_progress row is untouched -- never physically deleted,
            # never modified by the delete itself.
            async with _session_factory() as session:
                result = await session.execute(
                    select(SkillProgress).where(SkillProgress.assignment_id == assignment_id)
                )
                progress = result.scalar_one()
                assert progress.watch_position == 150
                assert progress.verified is True
        finally:
            await _cleanup_assignment(assignment_id)


# --- AC6: access control ---


async def test_delete_forbidden_for_employee_role():
    await _cleanup_assignments_for(CASEY_ID, SKILL_DATA_VIZ_ID)
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            async with _client() as employee_client:
                await _login(employee_client, email="casey@sails.example.com")
                response = await employee_client.delete(f"/api/assignments/{assignment_id}")
                assert response.status_code == 403
                assert response.json()["code"] == "FORBIDDEN_NOT_HR_ADMIN"

            # Confirm the forbidden attempt did not soft-delete the row.
            row = await _fetch_assignment_row(assignment_id)
            assert row.active is True
        finally:
            await _cleanup_assignment(assignment_id)


async def test_delete_by_non_owning_hr_admin_gets_403_not_a_leak():
    """A second HR Admin (not the assignment's creator) must be rejected the
    same way as a non-existent assignment_id -- same uniform-403 pattern as
    the drill-down/override endpoints (test_drill_down_endpoint.py's
    test_non_owning_hr_admin_gets_403_not_a_leak)."""
    await _cleanup_assignments_for(CASEY_ID, SKILL_DATA_VIZ_ID)
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            other_hr_token = create_access_token(str(uuid.uuid4()), "HR_ADMIN")
            async with _client() as other_hr_client:
                other_hr_client.cookies.set(settings.SESSION_COOKIE_NAME, other_hr_token)
                response = await other_hr_client.delete(f"/api/assignments/{assignment_id}")
                assert response.status_code == 403

            row = await _fetch_assignment_row(assignment_id)
            assert row.active is True
        finally:
            await _cleanup_assignment(assignment_id)


async def test_delete_nonexistent_assignment_gets_the_same_403_as_not_owned():
    async with _client() as client:
        await _login(client)
        response = await client.delete(f"/api/assignments/{uuid.uuid4()}")
        assert response.status_code == 403


async def test_delete_requires_authentication():
    async with _client() as client:
        response = await client.delete(f"/api/assignments/{uuid.uuid4()}")
        assert response.status_code == 401


# --- AC7: idempotent double-delete ---


async def test_delete_twice_is_idempotent_204_no_op():
    await _cleanup_assignments_for(CASEY_ID, SKILL_DATA_VIZ_ID)
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            first = await client.delete(f"/api/assignments/{assignment_id}")
            assert first.status_code == 204
            row_after_first = await _fetch_assignment_row(assignment_id)
            first_deleted_at = row_after_first.deleted_at

            second = await client.delete(f"/api/assignments/{assignment_id}")
            assert second.status_code == 204

            # No-op: the second delete must not overwrite the first delete's
            # deleted_at with a new timestamp.
            row_after_second = await _fetch_assignment_row(assignment_id)
            assert row_after_second.deleted_at == first_deleted_at
        finally:
            await _cleanup_assignment(assignment_id)


# --- AC8: the four updated read call sites exclude soft-deleted rows ---


async def test_deleted_assignment_disappears_from_hr_dashboard_and_decrements_total_count():
    await _cleanup_assignments_for(CASEY_ID, SKILL_SQL_ID)
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client, skill_id=SKILL_SQL_ID)
        try:
            before = await client.get("/api/dashboard", params={"page_size": 500})
            assert before.status_code == 200
            before_count = before.json()["total_count"]
            assert any(r["assignment_id"] == str(assignment_id) for r in before.json()["assignments"])

            delete_response = await client.delete(f"/api/assignments/{assignment_id}")
            assert delete_response.status_code == 204

            after = await client.get("/api/dashboard", params={"page_size": 500})
            assert after.status_code == 200
            assert after.json()["total_count"] == before_count - 1
            assert not any(r["assignment_id"] == str(assignment_id) for r in after.json()["assignments"])
        finally:
            await _cleanup_assignment(assignment_id)


async def test_deleted_assignment_disappears_from_employee_content_discovery():
    await _cleanup_assignments_for(CASEY_ID, SKILL_SQL_ID)
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client, skill_id=SKILL_SQL_ID)
        try:
            delete_response = await client.delete(f"/api/assignments/{assignment_id}")
            assert delete_response.status_code == 204

            async with _client() as employee_client:
                await _login(employee_client, email="casey@sails.example.com")
                response = await employee_client.get("/api/assignments/employee-assignments")
                assert response.status_code == 200
                body = response.json()
                assert not any(a["assignment_id"] == str(assignment_id) for a in body["assignments"])
        finally:
            await _cleanup_assignment(assignment_id)


async def test_deleted_assignment_rejects_further_watch_progress_capture_and_resume():
    """Code review decision-needed finding 1 (2026-07-14): an Employee's
    already-open video page (SPA, no reload) must not be able to keep
    writing/reading watch progress against an assignment HR just deleted --
    progress/repository.py's _build_assignment_query and
    get_assignment_with_scope now exclude soft-deleted assignments too, so
    POST/GET .../progress correctly 404/403 instead of silently succeeding."""
    await _cleanup_assignments_for(CASEY_ID, SKILL_COMMUNICATION_ID)
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client, skill_id=SKILL_COMMUNICATION_ID)
        try:
            async with _client() as employee_client:
                await _login(employee_client, email="casey@sails.example.com")

                # Before delete: both endpoints work normally. Checking
                # `verified` (not just the 201 status) matters here --
                # record_watch_progress's silent-rejection pattern (Story
                # 4-4) means a 201 alone doesn't prove the write actually
                # landed as a real signal; this establishes a genuinely
                # clean baseline before asserting the post-delete contrast.
                post_before = await employee_client.post(
                    f"/api/assignments/{assignment_id}/progress",
                    json={
                        "watch_position": 30,
                        "event_time": datetime.now(timezone.utc).isoformat(),
                        "video_url": "https://youtube.com/watch?v=test",
                    },
                )
                assert post_before.status_code == 201
                assert post_before.json()["verified"] is True
                get_before = await employee_client.get(f"/api/assignments/{assignment_id}/progress")
                assert get_before.status_code == 200

            delete_response = await client.delete(f"/api/assignments/{assignment_id}")
            assert delete_response.status_code == 204

            async with _client() as employee_client:
                await _login(employee_client, email="casey@sails.example.com")

                post_after = await employee_client.post(
                    f"/api/assignments/{assignment_id}/progress",
                    json={
                        "watch_position": 60,
                        "event_time": datetime.now(timezone.utc).isoformat(),
                        "video_url": "https://youtube.com/watch?v=test",
                    },
                )
                assert post_after.status_code == 404

                get_after = await employee_client.get(f"/api/assignments/{assignment_id}/progress")
                assert get_after.status_code == 403
        finally:
            await _cleanup_assignment(assignment_id)


async def test_deleted_assignment_no_longer_surfaces_as_a_duplicate():
    await _cleanup_assignments_for(CASEY_ID, SKILL_SQL_ID)
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client, skill_id=SKILL_SQL_ID)
        try:
            delete_response = await client.delete(f"/api/assignments/{assignment_id}")
            assert delete_response.status_code == 204

            response = await client.get(
                "/api/assignments/duplicate-check",
                params={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_SQL_ID)},
            )
            assert response.status_code == 200
            assert response.json() == []
        finally:
            await _cleanup_assignment(assignment_id)
