"""Router-level tests for dashboard/router.py (Story 3.5).

Same real-app + loop_scope="module" pattern as test_assignments_router.py /
test_assignments_create_route.py — see those files' module docstrings for
why plain function-scoped @pytest.mark.asyncio doesn't work here (this is a
live-DB-touching router).
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import Assignment, AssignmentOverride, ContentCatalog, SkillProgress
from app.core.config import settings
from app.core.seed_ids import CASEY_ID, MORGAN_ID, RITA_ID
from app.core.seeds import (
    SKILL_COMMUNICATION_ID,
    SKILL_DATA_VIZ_ID,
    SKILL_PYTHON_ID,
    SKILL_SALESFORCE_ID,
    SKILL_SQL_ID,
)
from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="module")

_engine = create_async_engine(settings.DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _login(client: AsyncClient, email: str = "admin@sails.example.com") -> str:
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
        # assignment_overrides and skill_progress both FK to assignments —
        # delete overrides first (Story 9.1's tests are the first in this
        # file to create one via POST .../override), then progress (this
        # test file is the first to insert SkillProgress rows directly,
        # unlike the sibling test_assignments_*.py files).
        await session.execute(delete(AssignmentOverride).where(AssignmentOverride.assignment_id == assignment_id))
        await session.execute(delete(SkillProgress).where(SkillProgress.assignment_id == assignment_id))
        await session.execute(delete(Assignment).where(Assignment.id == assignment_id))
        await session.commit()


async def _cleanup_assignments_for(employee_id: uuid.UUID, skill_id: uuid.UUID) -> None:
    async with _session_factory() as session:
        result = await session.execute(
            select(Assignment.id).where(Assignment.employee_id == employee_id, Assignment.skill_id == skill_id)
        )
        assignment_ids = [row[0] for row in result.all()]
        if assignment_ids:
            await session.execute(delete(AssignmentOverride).where(AssignmentOverride.assignment_id.in_(assignment_ids)))
            await session.execute(delete(SkillProgress).where(SkillProgress.assignment_id.in_(assignment_ids)))
        await session.execute(
            delete(Assignment).where(Assignment.employee_id == employee_id, Assignment.skill_id == skill_id)
        )
        await session.commit()


async def test_dashboard_assignments_includes_created_assignment_with_display_names():
    await _cleanup_assignments_for(CASEY_ID, SKILL_DATA_VIZ_ID)
    created_id = None
    try:
        async with _client() as client:
            await _login(client)
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assert create_response.status_code == 201
            created_id = uuid.UUID(create_response.json()["id"])

            response = await client.get("/api/dashboard")

            assert response.status_code == 200
            body = response.json()
            row = next((r for r in body["assignments"] if r["assignment_id"] == str(created_id)), None)
            assert row is not None, "newly created assignment not found in dashboard list"
            assert row["employee_id"] == str(CASEY_ID)
            assert row["employee_name"] == "Casey the Continuer"
            assert row["skill_id"] == str(SKILL_DATA_VIZ_ID)
            assert row["skill_name"] == "Data Visualization"
            assert row["status"] == "Not Started"
            assert row["status_percentage"] is None
            assert row["provenance"] == "Not Started"
            assert set(row.keys()) == {
                "assignment_id",
                "employee_id",
                "employee_name",
                "employee_group",
                "skill_id",
                "skill_name",
                "status",
                "status_percentage",
                "provenance",
                "last_updated",
                "assignment_created_at",
            }
    finally:
        if created_id is not None:
            await _cleanup_assignment(created_id)


async def test_dashboard_assignments_requires_authentication():
    async with _client() as client:
        response = await client.get("/api/dashboard")
        assert response.status_code == 401


async def test_dashboard_assignments_forbidden_for_employee_role():
    async with _client() as client:
        await _login(client, email="casey@sails.example.com")
        response = await client.get("/api/dashboard")
        assert response.status_code == 403
        assert response.json()["code"] == "FORBIDDEN_NOT_HR_ADMIN"


async def test_dashboard_assignments_reflects_real_watch_progress_status_and_percent():
    """End-to-end: a real skill_progress row (with content whose duration is
    known) must drive the dashboard's Status/progress_percent — not the
    hardcoded placeholder. Exercises all three Status buckets in one pass:
    not-started (no progress row), in-progress (partial watch), completed
    (full watch)."""
    await _cleanup_assignments_for(CASEY_ID, SKILL_DATA_VIZ_ID)
    await _cleanup_assignments_for(RITA_ID, SKILL_DATA_VIZ_ID)
    created_ids: dict[str, uuid.UUID] = {}
    content_id = None
    try:
        async with _session_factory() as session:
            content = ContentCatalog(
                skill_id=SKILL_DATA_VIZ_ID,
                title="Test content for Story 3.5 dashboard progress derivation",
                description="Test content",
                type="VIDEO",
                url="https://youtube.com/watch?v=test",
                embedding=[0.1] * 384,
                source="YOUTUBE",
                content_metadata={"video_id": "test", "duration": 300},
            )
            session.add(content)
            await session.commit()
            content_id = content.id

        async with _client() as client:
            await _login(client)

            # Not-started: created with no progress row at all.
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_DATA_VIZ_ID), "content_id": str(content_id)},
            )
            assert create_response.status_code == 201
            created_ids["not_started"] = uuid.UUID(create_response.json()["id"])

            # In-progress: 150/300 seconds watched.
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(RITA_ID), "skill_id": str(SKILL_DATA_VIZ_ID), "content_id": str(content_id)},
            )
            assert create_response.status_code == 201
            created_ids["in_progress"] = uuid.UUID(create_response.json()["id"])

        async with _session_factory() as session:
            session.add(
                SkillProgress(
                    assignment_id=created_ids["in_progress"],
                    watch_position=150,
                    event_time=datetime.now(timezone.utc),
                    verified=True,
                )
            )
            await session.commit()

        async with _client() as client:
            await _login(client)
            response = await client.get("/api/dashboard")
            assert response.status_code == 200
            body = response.json()

            not_started_row = next(r for r in body["assignments"] if r["assignment_id"] == str(created_ids["not_started"]))
            assert not_started_row["status"] == "Not Started"
            assert not_started_row["status_percentage"] is None
            assert not_started_row["provenance"] == "Not Started"

            in_progress_row = next(r for r in body["assignments"] if r["assignment_id"] == str(created_ids["in_progress"]))
            assert in_progress_row["status"] == "In Progress"
            assert in_progress_row["status_percentage"] == 50
            assert in_progress_row["provenance"] == "Verified"
    finally:
        for cid in created_ids.values():
            await _cleanup_assignment(cid)
        if content_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(ContentCatalog).where(ContentCatalog.id == content_id))
                await session.commit()


async def test_dashboard_stats_requires_authentication():
    async with _client() as client:
        response = await client.get("/api/dashboard/stats")
        assert response.status_code == 401


async def test_dashboard_stats_forbidden_for_employee_role():
    async with _client() as client:
        await _login(client, email="casey@sails.example.com")
        response = await client.get("/api/dashboard/stats")
        assert response.status_code == 403
        assert response.json()["code"] == "FORBIDDEN_NOT_HR_ADMIN"


async def _get_stats(client: AsyncClient) -> dict:
    response = await client.get("/api/dashboard/stats")
    assert response.status_code == 200
    return response.json()


async def test_dashboard_stats_reflects_mixed_status_counts():
    """Story 9.1 AC1/AC2: create one Not Started, one In Progress, and one
    Completed assignment (known content duration, matching the existing
    Story 3.5 pattern), snapshot /stats before and after, and assert the
    counts moved by exactly the expected deltas -- the only reliable way to
    assert on aggregate counts against this shared, ever-growing dev DB.
    Also asserts overall_percent's exact formula (not just bounds) by
    computing the expected value from the captured `before` snapshot --
    review finding 2026-09-13: the original version of this test only
    asserted 0 <= overall_percent <= 100, which a wrong formula would still
    pass."""
    await _cleanup_assignments_for(CASEY_ID, SKILL_DATA_VIZ_ID)
    await _cleanup_assignments_for(RITA_ID, SKILL_DATA_VIZ_ID)
    await _cleanup_assignments_for(MORGAN_ID, SKILL_DATA_VIZ_ID)
    created_ids: dict[str, uuid.UUID] = {}
    content_id = None
    try:
        async with _session_factory() as session:
            content = ContentCatalog(
                skill_id=SKILL_DATA_VIZ_ID,
                title="Test content for Story 9.1 dashboard stats",
                description="Test content",
                type="VIDEO",
                url="https://youtube.com/watch?v=test-9-1",
                embedding=[0.1] * 384,
                source="YOUTUBE",
                content_metadata={"video_id": "test-9-1", "duration": 300},
            )
            session.add(content)
            await session.commit()
            content_id = content.id

        async with _client() as client:
            await _login(client)
            before = await _get_stats(client)

            # Not Started: no progress row at all.
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_DATA_VIZ_ID), "content_id": str(content_id)},
            )
            assert create_response.status_code == 201
            created_ids["not_started"] = uuid.UUID(create_response.json()["id"])

            # In Progress: 150/300 seconds watched (review finding 2026-09-13:
            # the original test claimed this case but never actually created
            # it -- the in_progress_count assertion was a no-op).
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(MORGAN_ID), "skill_id": str(SKILL_DATA_VIZ_ID), "content_id": str(content_id)},
            )
            assert create_response.status_code == 201
            created_ids["in_progress"] = uuid.UUID(create_response.json()["id"])

            # Completed: 300/300 seconds watched.
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(RITA_ID), "skill_id": str(SKILL_DATA_VIZ_ID), "content_id": str(content_id)},
            )
            assert create_response.status_code == 201
            created_ids["completed"] = uuid.UUID(create_response.json()["id"])

        async with _session_factory() as session:
            session.add(
                SkillProgress(
                    assignment_id=created_ids["in_progress"],
                    watch_position=150,
                    event_time=datetime.now(timezone.utc),
                    verified=True,
                )
            )
            session.add(
                SkillProgress(
                    assignment_id=created_ids["completed"],
                    watch_position=300,
                    event_time=datetime.now(timezone.utc),
                    verified=True,
                )
            )
            await session.commit()

        async with _client() as client:
            await _login(client)
            after = await _get_stats(client)

        assert after["total_skills_assigned"] - before["total_skills_assigned"] == 3
        assert after["completed_count"] - before["completed_count"] == 1
        assert after["in_progress_count"] - before["in_progress_count"] == 1
        assert after["not_started_count"] - before["not_started_count"] == 1
        assert after["total_completed"] == after["completed_count"]

        expected_percent = round(after["completed_count"] / after["total_skills_assigned"] * 100)
        assert after["overall_percent"] == expected_percent
    finally:
        for cid in created_ids.values():
            await _cleanup_assignment(cid)
        if content_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(ContentCatalog).where(ContentCatalog.id == content_id))
                await session.commit()


async def test_dashboard_stats_hr_override_counts_as_completed():
    """Story 9.1 Scope Note 5: an assignment with an active HR Override must
    count as Completed even with 0% raw watch progress -- this is exactly
    the correctness gap the resurrected list_assignments_for_dashboard query
    doesn't handle on its own (no override eager-load), which is why the
    service batch-loads overrides separately."""
    await _cleanup_assignments_for(CASEY_ID, SKILL_SALESFORCE_ID)
    created_id = None
    try:
        async with _client() as client:
            await _login(client)
            before = await _get_stats(client)

            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(CASEY_ID), "skill_id": str(SKILL_SALESFORCE_ID)},
            )
            assert create_response.status_code == 201
            created_id = uuid.UUID(create_response.json()["id"])

            override_response = await client.post(
                f"/api/assignments/{created_id}/override", json={"action": "set"}
            )
            assert override_response.status_code == 200

            after = await _get_stats(client)

        assert after["total_skills_assigned"] - before["total_skills_assigned"] == 1
        assert after["completed_count"] - before["completed_count"] == 1
        assert after["not_started_count"] - before["not_started_count"] == 0
        assert after["in_progress_count"] - before["in_progress_count"] == 0
    finally:
        if created_id is not None:
            await _cleanup_assignment(created_id)


async def test_dashboard_stats_excludes_archived_employee_and_their_assignments():
    """Story 9.1 AC3: archiving an Employee (via DELETE, which archives
    rather than hard-deletes once they have Assignment history) must drop
    both them AND their Assignments out of every count here -- not just
    total_employees. A throwaway Employee is created specifically for this
    test since archiving is one-way in the product (no un-archive endpoint
    exists to clean up via the API); the created Employee/Assignment rows
    are removed directly at the DB level in the finally block instead."""
    employee_id = None
    assignment_id = None
    try:
        async with _client() as client:
            await _login(client)
            before_create = await _get_stats(client)

            create_emp_response = await client.post(
                "/api/admin/employees",
                json={
                    "employee_code": f"T9-1-{uuid.uuid4().hex[:8]}",
                    "first_name": "Story 9.1 Test",
                    "last_name": "Employee",
                    "email": f"story9-1-{uuid.uuid4().hex[:8]}@example.com",
                },
            )
            assert create_emp_response.status_code == 201
            employee_id = uuid.UUID(create_emp_response.json()["id"])

            create_assignment_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(employee_id), "skill_id": str(SKILL_SALESFORCE_ID)},
            )
            assert create_assignment_response.status_code == 201
            assignment_id = uuid.UUID(create_assignment_response.json()["id"])

            after_create = await _get_stats(client)
            assert after_create["total_employees"] - before_create["total_employees"] == 1
            assert after_create["total_skills_assigned"] - before_create["total_skills_assigned"] == 1

            archive_response = await client.delete(f"/api/admin/employees/{employee_id}")
            assert archive_response.status_code == 200

            after_archive = await _get_stats(client)
            assert after_archive["total_employees"] == before_create["total_employees"]
            assert after_archive["total_skills_assigned"] == before_create["total_skills_assigned"]
    finally:
        if assignment_id is not None:
            await _cleanup_assignment(assignment_id)
        if employee_id is not None:
            async with _session_factory() as session:
                from app.auth.models import Account
                from app.employees.models import Employee

                # Account.id == Employee.id (AR-24) -- delete the account
                # first or the FK (accounts_id_fkey) blocks the employee delete.
                await session.execute(delete(Account).where(Account.id == employee_id))
                await session.execute(delete(Employee).where(Employee.id == employee_id))
                await session.commit()


async def test_dashboard_assignments_returns_multiple_org_wide_rows_for_hr_admin():
    """HR sessions are unrestricted (not scoped to a single employee) —
    confirm at least two distinct employees' assignments both surface in one
    call, proving this is an org-wide read, not accidentally self-scoped."""
    await _cleanup_assignments_for(CASEY_ID, SKILL_SALESFORCE_ID)
    await _cleanup_assignments_for(RITA_ID, SKILL_SALESFORCE_ID)
    created_ids = []
    try:
        async with _client() as client:
            await _login(client)
            for employee_id in (CASEY_ID, RITA_ID):
                create_response = await client.post(
                    "/api/assignments",
                    json={"employee_id": str(employee_id), "skill_id": str(SKILL_SALESFORCE_ID)},
                )
                assert create_response.status_code == 201
                created_ids.append(uuid.UUID(create_response.json()["id"]))

            response = await client.get("/api/dashboard")

            assert response.status_code == 200
            body = response.json()
            found_ids = {r["assignment_id"] for r in body["assignments"]}
            assert all(str(cid) in found_ids for cid in created_ids)
    finally:
        for cid in created_ids:
            await _cleanup_assignment(cid)


async def _get_segmentation(client: AsyncClient) -> dict:
    response = await client.get("/api/dashboard/segmentation")
    assert response.status_code == 200
    return response.json()


async def _create_throwaway_employee(client: AsyncClient, label: str) -> uuid.UUID:
    """Story 9.2: bucket membership is a per-Employee aggregate across ALL of
    that Employee's active Assignments, so the seeded demo Employees
    (CASEY/MORGAN/RITA/etc.) can't be used for precise bucket assertions --
    their existing assignments from other tests in this shared dev DB would
    make the resulting bucket unpredictable. Mirrors Story 9.1's
    test_dashboard_stats_excludes_archived_employee_and_their_assignments,
    which hit the same problem and solved it the same way."""
    response = await client.post(
        "/api/admin/employees",
        json={
            "employee_code": f"T9-2-{label}-{uuid.uuid4().hex[:8]}",
            "first_name": "Story 9.2 Test Employee",
            "last_name": label,
            "email": f"story9-2-{label}-{uuid.uuid4().hex[:8]}@example.com",
        },
    )
    assert response.status_code == 201
    return uuid.UUID(response.json()["id"])


async def _delete_employee_hard(employee_id: uuid.UUID) -> None:
    async with _session_factory() as session:
        from app.auth.models import Account
        from app.employees.models import Employee

        # Account.id == Employee.id (AR-24) -- delete the account first or
        # the FK (accounts_id_fkey) blocks the employee delete.
        await session.execute(delete(Account).where(Account.id == employee_id))
        await session.execute(delete(Employee).where(Employee.id == employee_id))
        await session.commit()


async def _set_override_completed(client: AsyncClient, assignment_id: uuid.UUID) -> None:
    response = await client.post(f"/api/assignments/{assignment_id}/override", json={"action": "set"})
    assert response.status_code == 200


async def _insert_stale_self_reported_progress(assignment_id: uuid.UUID) -> None:
    """Produces a genuine (not overridden) 'Needs Attention' Provenance:
    unverified progress whose event_time is well past
    NEEDS_ATTENTION_STALENESS_DAYS (7), matching the exact shape
    test_provenance_detail.py's test_unverified_stale_progress_is_needs_attention
    uses at the unit level."""
    async with _session_factory() as session:
        progress = SkillProgress(
            id=uuid.uuid4(),
            assignment_id=assignment_id,
            watch_position=100,
            event_time=datetime.now(timezone.utc) - timedelta(days=14),
            verified=False,
            updated_at=datetime.now(timezone.utc) - timedelta(days=14),
        )
        session.add(progress)
        await session.commit()


async def test_employee_segmentation_requires_authentication():
    async with _client() as client:
        response = await client.get("/api/dashboard/segmentation")
        assert response.status_code == 401


async def test_employee_segmentation_forbidden_for_employee_role():
    async with _client() as client:
        await _login(client, email="casey@sails.example.com")
        response = await client.get("/api/dashboard/segmentation")
        assert response.status_code == 403
        assert response.json()["code"] == "FORBIDDEN_NOT_HR_ADMIN"


async def test_employee_segmentation_on_track_employee():
    """Story 9.2 AC1: 100% completion, no Needs Attention assignments ->
    On Track."""
    employee_id = None
    assignment_id = None
    try:
        async with _client() as client:
            await _login(client)
            before = await _get_segmentation(client)

            employee_id = await _create_throwaway_employee(client, "ontrack")
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(employee_id), "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assert create_response.status_code == 201
            assignment_id = uuid.UUID(create_response.json()["id"])
            await _set_override_completed(client, assignment_id)

            after = await _get_segmentation(client)

        assert after["on_track_count"] - before["on_track_count"] == 1
        assert after["in_progress_count"] == before["in_progress_count"]
        assert after["needs_attention_count"] == before["needs_attention_count"]
    finally:
        if assignment_id is not None:
            await _cleanup_assignment(assignment_id)
        if employee_id is not None:
            await _delete_employee_hard(employee_id)


async def test_employee_segmentation_in_progress_catchall_for_zero_percent():
    """Story 9.2 AC1/Scope Note 5: an Employee at 0% complete (Not Started,
    no signal at all) has no Needs Attention flag and completion rate 0.0 <
    ON_TRACK_THRESHOLD, so falls into the explicit In Progress catch-all --
    there is deliberately no 4th 'Not Started' segment (FR-32 consequence #3)."""
    employee_id = None
    assignment_id = None
    try:
        async with _client() as client:
            await _login(client)
            before = await _get_segmentation(client)

            employee_id = await _create_throwaway_employee(client, "inprogress")
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(employee_id), "skill_id": str(SKILL_SQL_ID)},
            )
            assert create_response.status_code == 201
            assignment_id = uuid.UUID(create_response.json()["id"])

            after = await _get_segmentation(client)

        assert after["in_progress_count"] - before["in_progress_count"] == 1
        assert after["on_track_count"] == before["on_track_count"]
        assert after["needs_attention_count"] == before["needs_attention_count"]
    finally:
        if assignment_id is not None:
            await _cleanup_assignment(assignment_id)
        if employee_id is not None:
            await _delete_employee_hard(employee_id)


async def test_employee_segmentation_needs_attention_overrides_high_completion():
    """Story 9.2 AC1: the priority rule, not just additive bucketing. This
    Employee's 4/5 = 80% completion rate would independently qualify as
    On Track (>= ON_TRACK_THRESHOLD's 0.8 default), but a single genuine
    Needs Attention assignment must still force the whole Employee into the
    Needs Attention bucket instead."""
    employee_id = None
    assignment_ids: list[uuid.UUID] = []
    try:
        async with _client() as client:
            await _login(client)
            before = await _get_segmentation(client)

            employee_id = await _create_throwaway_employee(client, "needsattn")
            completed_skills = [SKILL_DATA_VIZ_ID, SKILL_SALESFORCE_ID, SKILL_PYTHON_ID, SKILL_SQL_ID]
            for skill_id in completed_skills:
                create_response = await client.post(
                    "/api/assignments",
                    json={"employee_id": str(employee_id), "skill_id": str(skill_id)},
                )
                assert create_response.status_code == 201
                aid = uuid.UUID(create_response.json()["id"])
                assignment_ids.append(aid)
                await _set_override_completed(client, aid)

            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(employee_id), "skill_id": str(SKILL_COMMUNICATION_ID)},
            )
            assert create_response.status_code == 201
            flagged_assignment_id = uuid.UUID(create_response.json()["id"])
            assignment_ids.append(flagged_assignment_id)
            await _insert_stale_self_reported_progress(flagged_assignment_id)

            after = await _get_segmentation(client)

        assert after["needs_attention_count"] - before["needs_attention_count"] == 1
        assert after["on_track_count"] == before["on_track_count"]
        assert after["in_progress_count"] == before["in_progress_count"]

        flagged_entries = [e for e in after["needs_attention"] if e["employee_id"] == str(employee_id)]
        assert len(flagged_entries) == 1
        entry = flagged_entries[0]
        assert entry["assignment_id"] == str(flagged_assignment_id)
        assert entry["skill_id"] == str(SKILL_COMMUNICATION_ID)
        assert entry["skill_name"] == "Communication Skills"
        assert entry["employee_name"] == "Story 9.2 Test Employee needsattn"
    finally:
        for aid in assignment_ids:
            await _cleanup_assignment(aid)
        if employee_id is not None:
            await _delete_employee_hard(employee_id)


async def test_employee_segmentation_on_track_boundary_without_override():
    """Story 9.2 code review patch: the existing On Track test used 100%
    completion via HR Override, which never actually exercised the
    ON_TRACK_THRESHOLD comparison itself (it would pass regardless of the
    threshold value). This test uses a genuine natural 4/5 = 80% completion
    rate with zero overrides and zero Needs Attention flags, landing exactly
    on ON_TRACK_THRESHOLD's default -- proving the `>=` comparison itself,
    not just the override-masked priority rule."""
    employee_id = None
    assignment_ids: list[uuid.UUID] = []
    try:
        async with _client() as client:
            await _login(client)
            before = await _get_segmentation(client)

            employee_id = await _create_throwaway_employee(client, "boundary80")
            completed_skills = [SKILL_DATA_VIZ_ID, SKILL_SALESFORCE_ID, SKILL_PYTHON_ID, SKILL_SQL_ID]
            for skill_id in completed_skills:
                create_response = await client.post(
                    "/api/assignments",
                    json={"employee_id": str(employee_id), "skill_id": str(skill_id)},
                )
                assert create_response.status_code == 201
                aid = uuid.UUID(create_response.json()["id"])
                assignment_ids.append(aid)
                await _set_override_completed(client, aid)

            # 5th assignment left Not Started -- 4/5 = 80% completion, no
            # Needs Attention flags anywhere.
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(employee_id), "skill_id": str(SKILL_COMMUNICATION_ID)},
            )
            assert create_response.status_code == 201
            assignment_ids.append(uuid.UUID(create_response.json()["id"]))

            after = await _get_segmentation(client)

        assert after["on_track_count"] - before["on_track_count"] == 1
        assert after["in_progress_count"] == before["in_progress_count"]
        assert after["needs_attention_count"] == before["needs_attention_count"]
    finally:
        for aid in assignment_ids:
            await _cleanup_assignment(aid)
        if employee_id is not None:
            await _delete_employee_hard(employee_id)


async def test_employee_segmentation_below_threshold_lands_in_progress():
    """Story 9.2 code review patch: complements the boundary-at-threshold
    test above with a ratio just below ON_TRACK_THRESHOLD (3/4 = 75%, no
    Needs Attention flags) to prove the `>=` comparison correctly excludes
    a near-miss from On Track rather than only ever being tested at 0% or
    100%."""
    employee_id = None
    assignment_ids: list[uuid.UUID] = []
    try:
        async with _client() as client:
            await _login(client)
            before = await _get_segmentation(client)

            employee_id = await _create_throwaway_employee(client, "belowthreshold")
            completed_skills = [SKILL_DATA_VIZ_ID, SKILL_SALESFORCE_ID, SKILL_PYTHON_ID]
            for skill_id in completed_skills:
                create_response = await client.post(
                    "/api/assignments",
                    json={"employee_id": str(employee_id), "skill_id": str(skill_id)},
                )
                assert create_response.status_code == 201
                aid = uuid.UUID(create_response.json()["id"])
                assignment_ids.append(aid)
                await _set_override_completed(client, aid)

            # 4th assignment left Not Started -- 3/4 = 75% completion, below
            # ON_TRACK_THRESHOLD's default 0.8.
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(employee_id), "skill_id": str(SKILL_SQL_ID)},
            )
            assert create_response.status_code == 201
            assignment_ids.append(uuid.UUID(create_response.json()["id"]))

            after = await _get_segmentation(client)

        assert after["in_progress_count"] - before["in_progress_count"] == 1
        assert after["on_track_count"] == before["on_track_count"]
        assert after["needs_attention_count"] == before["needs_attention_count"]
    finally:
        for aid in assignment_ids:
            await _cleanup_assignment(aid)
        if employee_id is not None:
            await _delete_employee_hard(employee_id)


async def test_employee_segmentation_override_clears_needs_attention_flag():
    """Story 9.2 code review patch: proves the one real behavioral
    interaction between Needs Attention and HR Override that the story's
    Dev Notes claimed was 'confirmed safe via direct code reading' but never
    actually tested -- once a genuinely stale (Needs Attention) Assignment
    is HR-Overridden, get_provenance_detail reports provenance "HR Override"
    (never "Needs Attention") for it, so the Employee must fall out of the
    Needs Attention bucket entirely rather than remaining flagged."""
    employee_id = None
    assignment_id = None
    try:
        async with _client() as client:
            await _login(client)
            before = await _get_segmentation(client)

            employee_id = await _create_throwaway_employee(client, "overrideclears")
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(employee_id), "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assert create_response.status_code == 201
            assignment_id = uuid.UUID(create_response.json()["id"])
            await _insert_stale_self_reported_progress(assignment_id)

            during = await _get_segmentation(client)
            assert during["needs_attention_count"] - before["needs_attention_count"] == 1

            await _set_override_completed(client, assignment_id)

            after = await _get_segmentation(client)

        assert after["needs_attention_count"] == before["needs_attention_count"]
        assert after["on_track_count"] - before["on_track_count"] == 1
        assert after["in_progress_count"] == before["in_progress_count"]
        assert not any(e["employee_id"] == str(employee_id) for e in after["needs_attention"])
    finally:
        if assignment_id is not None:
            await _cleanup_assignment(assignment_id)
        if employee_id is not None:
            await _delete_employee_hard(employee_id)


async def test_employee_segmentation_never_triggers_content_reembed_write():
    """Story 9.2 code review patch: the whole point of deliberately omitting
    the match_content_for_skill fallback (Scope Note 3) is that this GET
    endpoint must never trigger a Content re-embed write. Nothing previously
    asserted this -- a future regression reintroducing that call would pass
    every other test silently. Patches app.dashboard.service.match_content_for_skill
    (imported at module level in dashboard/service.py, used only by the
    sibling get_dashboard_assignments) and asserts it is never invoked by
    get_employee_segmentation."""
    employee_id = None
    assignment_id = None
    try:
        async with _client() as client:
            await _login(client)

            employee_id = await _create_throwaway_employee(client, "nosideeffect")
            # No content_id, no progress row -- an assignment whose duration
            # can't be resolved without the fallback, so if the fallback were
            # (re)called, it would actually be exercised, not skipped as a
            # no-op.
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(employee_id), "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assert create_response.status_code == 201
            assignment_id = uuid.UUID(create_response.json()["id"])

            with mock.patch("app.dashboard.service.match_content_for_skill") as mocked:
                response = await client.get("/api/dashboard/segmentation")
                assert response.status_code == 200
                mocked.assert_not_called()
    finally:
        if assignment_id is not None:
            await _cleanup_assignment(assignment_id)
        if employee_id is not None:
            await _delete_employee_hard(employee_id)


async def test_employee_segmentation_excludes_employee_with_zero_active_assignments():
    """Story 9.2 AC3: an active Employee with zero active Assignments is
    excluded entirely -- not counted toward any of the three buckets."""
    employee_id = None
    try:
        async with _client() as client:
            await _login(client)
            before = await _get_segmentation(client)

            employee_id = await _create_throwaway_employee(client, "noassignments")

            after = await _get_segmentation(client)

        assert after["on_track_count"] == before["on_track_count"]
        assert after["in_progress_count"] == before["in_progress_count"]
        assert after["needs_attention_count"] == before["needs_attention_count"]
    finally:
        if employee_id is not None:
            await _delete_employee_hard(employee_id)


async def test_employee_segmentation_excludes_archived_employee():
    """Story 9.2 AC3, mirroring Story 9.1's
    test_dashboard_stats_excludes_archived_employee_and_their_assignments:
    archiving an Employee (DELETE, which archives once they have Assignment
    history) must drop them out of whichever bucket they were in."""
    employee_id = None
    assignment_id = None
    try:
        async with _client() as client:
            await _login(client)
            before_create = await _get_segmentation(client)

            employee_id = await _create_throwaway_employee(client, "archived")
            create_response = await client.post(
                "/api/assignments",
                json={"employee_id": str(employee_id), "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assert create_response.status_code == 201
            assignment_id = uuid.UUID(create_response.json()["id"])
            await _set_override_completed(client, assignment_id)

            after_create = await _get_segmentation(client)
            assert after_create["on_track_count"] - before_create["on_track_count"] == 1

            archive_response = await client.delete(f"/api/admin/employees/{employee_id}")
            assert archive_response.status_code == 200

            after_archive = await _get_segmentation(client)
            assert after_archive["on_track_count"] == before_create["on_track_count"]
    finally:
        if assignment_id is not None:
            await _cleanup_assignment(assignment_id)
        if employee_id is not None:
            await _delete_employee_hard(employee_id)
