"""Integration tests for POST /api/assignments/{assignment_id}/override
(Story 5.5, FR-12). Real app + ASGITransport + real Postgres, mirroring
test_drill_down_endpoint.py's exact scaffolding (see that file's module
docstring for why loop_scope="module" is needed here)."""
import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import Assignment, AssignmentOverride, SkillProgress
from app.core.config import settings
from app.core.security import create_access_token
from app.core.seed_ids import CASEY_ID
from app.core.seeds import SKILL_DATA_VIZ_ID
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


async def _create_assignment(client: AsyncClient) -> uuid.UUID:
    response = await client.post(
        "/api/assignments", json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_DATA_VIZ_ID)}
    )
    assert response.status_code == 201
    return uuid.UUID(response.json()["id"])


async def test_hr_admin_marks_ready_returns_hr_override_state():
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            response = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "set", "reason": "Verified in call"}
            )
            assert response.status_code == 200
            body = response.json()
            assert body["provenance"] == "HR Override"
            assert body["status"] == "COMPLETED"
            assert body["override_reason"] == "Verified in call"
            assert body["override_set_by_name"] is not None
            # A brand-new no-progress assignment's underlying signal is Not Started.
            assert body["underlying_provenance"] == "Not Started"
            assert body["underlying_status"] == "NOT_STARTED"
        finally:
            await _cleanup_assignment(assignment_id)


async def test_post_response_and_subsequent_drill_down_get_agree():
    """AR-3 cross-surface invariant: the POST response and a following GET
    drill-down must be identical for the same state."""
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            post_response = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "set"}
            )
            assert post_response.status_code == 200

            get_response = await client.get(f"/api/assignments/{assignment_id}/progress/drill-down")
            assert get_response.status_code == 200

            post_body = post_response.json()
            get_body = get_response.json()
            assert post_body["status"] == get_body["status"]
            assert post_body["provenance"] == get_body["provenance"]
            assert post_body["override_set_by_name"] == get_body["override_set_by_name"]
        finally:
            await _cleanup_assignment(assignment_id)


async def test_dashboard_grid_reflects_override_immediately():
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            response = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "set"}
            )
            assert response.status_code == 200

            dashboard_response = await client.get("/api/dashboard", params={"page_size": 500})
            assert dashboard_response.status_code == 200
            row = next(
                r for r in dashboard_response.json()["assignments"] if r["assignment_id"] == str(assignment_id)
            )
            assert row["status"] == "Completed"
            assert row["provenance"] == "HR Override"
        finally:
            await _cleanup_assignment(assignment_id)


async def test_employee_role_gets_403_for_set_and_unset():
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            async with _client() as employee_client:
                await _login(employee_client, email="casey@sails.example.com")

                set_response = await employee_client.post(
                    f"/api/assignments/{assignment_id}/override", json={"action": "set"}
                )
                assert set_response.status_code == 403
                assert set_response.json()["code"] == "FORBIDDEN_NOT_HR_ADMIN"

                unset_response = await employee_client.post(
                    f"/api/assignments/{assignment_id}/override", json={"action": "unset"}
                )
                assert unset_response.status_code == 403
                assert unset_response.json()["code"] == "FORBIDDEN_NOT_HR_ADMIN"
        finally:
            await _cleanup_assignment(assignment_id)


async def test_non_owning_hr_admin_gets_403_not_a_leak():
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            other_hr_token = create_access_token(str(uuid.uuid4()), "HR_ADMIN")
            async with _client() as other_hr_client:
                other_hr_client.cookies.set(settings.SESSION_COOKIE_NAME, other_hr_token)
                response = await other_hr_client.post(
                    f"/api/assignments/{assignment_id}/override", json={"action": "set"}
                )
                assert response.status_code == 403
        finally:
            await _cleanup_assignment(assignment_id)


async def test_unset_with_no_active_override_returns_404():
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            response = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "unset"}
            )
            assert response.status_code == 404
            assert response.json()["code"] == "NO_ACTIVE_OVERRIDE"
        finally:
            await _cleanup_assignment(assignment_id)


async def test_re_marking_ready_leaves_exactly_one_active_override_row():
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            first = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "set", "reason": "First mark"}
            )
            assert first.status_code == 200

            second = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "set", "reason": "Second mark"}
            )
            assert second.status_code == 200

            async with _session_factory() as session:
                result = await session.execute(
                    select(AssignmentOverride).where(AssignmentOverride.assignment_id == assignment_id)
                )
                rows = list(result.scalars().all())

            assert len(rows) == 2
            active_rows = [r for r in rows if r.active]
            inactive_rows = [r for r in rows if not r.active]
            assert len(active_rows) == 1
            assert len(inactive_rows) == 1
            assert active_rows[0].reason == "Second mark"
            assert inactive_rows[0].reason == "First mark"
            assert inactive_rows[0].reversed_at is not None
            assert inactive_rows[0].reversed_by is not None
        finally:
            await _cleanup_assignment(assignment_id)


async def test_set_then_unset_deactivates_and_reverts_to_underlying_signal():
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            set_response = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "set"}
            )
            assert set_response.status_code == 200
            assert set_response.json()["provenance"] == "HR Override"

            unset_response = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "unset"}
            )
            assert unset_response.status_code == 200
            body = unset_response.json()
            assert body["provenance"] == "Not Started"
            assert body["underlying_provenance"] is None

            # A second unset with nothing active must 404, not silently succeed.
            second_unset = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "unset"}
            )
            assert second_unset.status_code == 404
        finally:
            await _cleanup_assignment(assignment_id)


async def test_reason_is_trimmed_and_whitespace_only_becomes_none():
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            response = await client.post(
                f"/api/assignments/{assignment_id}/override",
                json={"action": "set", "reason": "   Verified in call   "},
            )
            assert response.status_code == 200
            assert response.json()["override_reason"] == "Verified in call"
        finally:
            await _cleanup_assignment(assignment_id)


async def test_whitespace_only_reason_stored_as_none():
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            response = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "set", "reason": "   "}
            )
            assert response.status_code == 200
            assert response.json()["override_reason"] is None
        finally:
            await _cleanup_assignment(assignment_id)


async def test_fresh_watch_progress_after_override_shows_both_signals():
    """AC5: a fresh watch-position update arriving after an override must not
    replace it -- both must remain visible in a following drill-down GET."""
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            set_response = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "set"}
            )
            assert set_response.status_code == 200

            async with _session_factory() as session:
                session.add(
                    SkillProgress(
                        assignment_id=assignment_id,
                        watch_position=120,
                        event_time=datetime.now(timezone.utc),
                        verified=True,
                    )
                )
                await session.commit()

            get_response = await client.get(f"/api/assignments/{assignment_id}/progress/drill-down")
            assert get_response.status_code == 200
            body = get_response.json()
            assert body["provenance"] == "HR Override"
            assert body["underlying_provenance"] == "Verified"
        finally:
            await _cleanup_assignment(assignment_id)


async def test_unauthenticated_gets_401():
    async with _client() as client:
        response = await client.post(
            f"/api/assignments/{uuid.uuid4()}/override", json={"action": "set"}
        )
        assert response.status_code == 401


async def test_nonexistent_assignment_gets_403_not_a_leak():
    """Code review finding, Story 5.5: only "owned by someone else" was
    tested for the anti-enumeration 403 -- a wholly nonexistent assignment_id
    must behave identically (same status, no existence leak)."""
    async with _client() as client:
        await _login(client)
        response = await client.post(
            f"/api/assignments/{uuid.uuid4()}/override", json={"action": "set"}
        )
        assert response.status_code == 403


async def test_unknown_request_field_rejected_with_422():
    """Code review finding, Story 5.5: SetOverrideRequest's extra="forbid"
    (no client-supplied override_status/set_by/active) was asserted in prose
    but never tested."""
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            response = await client.post(
                f"/api/assignments/{assignment_id}/override",
                json={"action": "set", "status": "IN_PROGRESS"},
            )
            assert response.status_code == 422
        finally:
            await _cleanup_assignment(assignment_id)


async def test_reason_with_unset_action_rejected_with_422():
    """Code review finding, Story 5.5: a reversal has no column to persist a
    reason against -- reject rather than silently drop a caller-supplied one."""
    async with _client() as client:
        await _login(client)
        assignment_id = await _create_assignment(client)
        try:
            set_response = await client.post(
                f"/api/assignments/{assignment_id}/override", json={"action": "set"}
            )
            assert set_response.status_code == 200

            response = await client.post(
                f"/api/assignments/{assignment_id}/override",
                json={"action": "unset", "reason": "Should not be accepted"},
            )
            assert response.status_code == 422
        finally:
            await _cleanup_assignment(assignment_id)


async def test_concurrent_set_calls_leave_exactly_one_active_override_row():
    """Code review finding, Story 5.5: the read-active -> deactivate -> create
    sequence had no DB-level guard, so two concurrent 'set' calls starting
    from zero active overrides could both insert, violating AC9. Fixed via a
    Postgres advisory lock (ProgressRepository.acquire_override_lock) that
    serializes concurrent calls for the same assignment_id -- this test
    fires two real concurrent requests (not sequential) to prove the guard
    actually closes the race, not just that re-marking works in order."""
    async with _client() as client_a, _client() as client_b:
        await _login(client_a)
        await _login(client_b)
        assignment_id = await _create_assignment(client_a)
        try:
            responses = await asyncio.gather(
                client_a.post(
                    f"/api/assignments/{assignment_id}/override",
                    json={"action": "set", "reason": "From A"},
                ),
                client_b.post(
                    f"/api/assignments/{assignment_id}/override",
                    json={"action": "set", "reason": "From B"},
                ),
            )
            assert all(r.status_code == 200 for r in responses)

            async with _session_factory() as session:
                result = await session.execute(
                    select(AssignmentOverride).where(AssignmentOverride.assignment_id == assignment_id)
                )
                rows = list(result.scalars().all())

            active_rows = [r for r in rows if r.active]
            assert len(active_rows) == 1, (
                f"expected exactly one active override after concurrent 'set' calls, "
                f"got {len(active_rows)}"
            )
        finally:
            await _cleanup_assignment(assignment_id)
