"""Live-DB tests for assignments/service.py (Story 3.1 AC4, AC6).

Uses a private engine/session-factory rather than the shared `app.core.db.engine`
singleton — see test_assignments_repository.py's module docstring for why
(cross-module-loop connection-pool corruption when two module-scoped-loop test
files share the same pooled engine)."""
import uuid
from contextlib import asynccontextmanager
from unittest import mock

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments import service as assignments_service
from app.assignments.repository import find_existing_assignment, list_assignments_for_employee
from app.assignments.schemas import AssignmentStatus, CreateAssignmentRequest
from app.assignments.service import create_assignment_service
from app.auth.repository import find_account
from app.auth.schemas import CurrentUser, Role
from app.core.config import settings
from app.core.errors import AppException
from app.core.seeds import CASEY_ID, RITA_ID, SKILL_DATA_VIZ_ID, run_seeds
from app.skills.models import Skill
from app.skills.repository import get_skill_by_id

pytestmark = pytest.mark.asyncio(loop_scope="module")

_engine = create_async_engine(settings.DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


@asynccontextmanager
async def _seeded_session():
    async with _session_factory() as session:
        await run_seeds(session)
        try:
            yield session
        finally:
            await session.rollback()


async def test_hr_admin_creates_assignment_with_trivial_status_and_provenance():
    async with _seeded_session() as session:
        hr_user = CurrentUser(role=Role.HR_ADMIN, user_id=str(RITA_ID))
        request = CreateAssignmentRequest(employee_id=CASEY_ID, skill_id=SKILL_DATA_VIZ_ID)

        response = await create_assignment_service(session, current_user=hr_user, request=request)

        assert response.employee_id == CASEY_ID
        assert response.skill_id == SKILL_DATA_VIZ_ID
        assert response.status == AssignmentStatus.NOT_STARTED
        assert response.provenance == "Assigned · Awaiting first watch"
        assert response.assigned_by == RITA_ID


async def test_employee_is_rejected_before_any_repository_call():
    async with _seeded_session() as session:
        employee_user = CurrentUser(role=Role.EMPLOYEE, user_id=str(CASEY_ID))
        request = CreateAssignmentRequest(employee_id=CASEY_ID, skill_id=SKILL_DATA_VIZ_ID)

        before = await list_assignments_for_employee(session, current_user=employee_user)

        with pytest.raises(AppException) as exc_info:
            await create_assignment_service(session, current_user=employee_user, request=request)

        assert exc_info.value.status_code == 403
        assert exc_info.value.error_code == "FORBIDDEN_NOT_HR_ADMIN"

        # No assignment row was created as a side effect of the rejected call.
        after = await list_assignments_for_employee(session, current_user=employee_user)
        assert after == before


async def test_real_mock_login_user_id_works_end_to_end_as_assigned_by():
    """Regression test (code review, 2026-07-10): create_assignment_service does
    `uuid.UUID(current_user.user_id)`, which previously crashed for every real
    login, because auth/repository.py's mock accounts issued user_id as plain
    names ("rita", "casey", ...) instead of UUIDs. Fixed by aligning the mock
    accounts' user_id with the real seeded Employee UUIDs (core/seed_ids.py) —
    this test goes through find_account (the actual login-flow lookup), not a
    hand-constructed CurrentUser, to prove the real path works end-to-end."""
    async with _seeded_session() as session:
        account = find_account("rita@sails.example.com")
        hr_user = CurrentUser(role=Role.HR_ADMIN, user_id=account["user_id"])
        request = CreateAssignmentRequest(employee_id=CASEY_ID, skill_id=SKILL_DATA_VIZ_ID)

        response = await create_assignment_service(session, current_user=hr_user, request=request)

        assert response.assigned_by == RITA_ID


async def _make_test_skill(session, *, ever_assigned: bool = False) -> Skill:
    """A skill this test file fully controls the `ever_assigned` starting
    value of -- the fixed seeded skill IDs (SKILL_DATA_VIZ_ID etc.) live in
    the real shared dev DB and may already carry real Assignment history
    from actual usage, so their current ever_assigned value isn't a safe
    assumption for these tests."""
    skill = Skill(
        name=f"Assignment Wiring Test Skill {uuid.uuid4().hex[:8]}",
        description="Story 6.4 test skill",
        embedding=[0.1] * 384,
        ever_assigned=ever_assigned,
    )
    session.add(skill)
    await session.flush()
    return skill


async def test_creating_assignment_marks_target_skill_ever_assigned():
    """Story 6.4 AC1 -- create_assignment_service calls
    skills.service.mark_ever_assigned after the Assignment insert."""
    async with _seeded_session() as session:
        skill = await _make_test_skill(session)
        hr_user = CurrentUser(role=Role.HR_ADMIN, user_id=str(RITA_ID))
        request = CreateAssignmentRequest(employee_id=CASEY_ID, skill_id=skill.id)

        await create_assignment_service(session, current_user=hr_user, request=request)

        updated_skill = await get_skill_by_id(session, skill.id)
        assert updated_skill.ever_assigned is True


async def test_creating_second_assignment_for_already_assigned_skill_is_idempotent():
    """Story 6.4 AC2 -- a second (intentional, FR-1) Assignment against an
    already-locked Skill succeeds normally; the flag-set call is a no-op,
    not an error."""
    async with _seeded_session() as session:
        skill = await _make_test_skill(session, ever_assigned=True)
        hr_user = CurrentUser(role=Role.HR_ADMIN, user_id=str(RITA_ID))
        request = CreateAssignmentRequest(employee_id=CASEY_ID, skill_id=skill.id)

        response = await create_assignment_service(session, current_user=hr_user, request=request)

        assert response.skill_id == skill.id
        updated_skill = await get_skill_by_id(session, skill.id)
        assert updated_skill.ever_assigned is True


async def test_mark_ever_assigned_failure_does_not_lose_the_assignment(monkeypatch):
    """Story 6.4 AC1 (Scope Note 5) -- if the flag-set call raises, the
    Assignment must still be created and returned; the failure must not
    roll back the outer transaction."""
    async def _boom(session, skill_id):
        raise RuntimeError("simulated flag-set failure")

    monkeypatch.setattr(assignments_service, "mark_ever_assigned", _boom)

    async with _seeded_session() as session:
        skill = await _make_test_skill(session)
        hr_user = CurrentUser(role=Role.HR_ADMIN, user_id=str(RITA_ID))
        request = CreateAssignmentRequest(employee_id=CASEY_ID, skill_id=skill.id)

        response = await create_assignment_service(session, current_user=hr_user, request=request)

        assert response.employee_id == CASEY_ID
        assert response.skill_id == skill.id

        existing = await find_existing_assignment(session, employee_id=CASEY_ID, skill_id=skill.id)
        assert any(a.id == response.id for a in existing)

        # The flag itself was never set, since the simulated failure
        # prevented it -- confirms the isolation didn't silently succeed.
        updated_skill = await get_skill_by_id(session, skill.id)
        assert updated_skill.ever_assigned is False


async def test_real_db_error_inside_savepoint_does_not_lose_the_assignment():
    """Story 6.4 code review patch -- the synthetic-RuntimeError test above
    only proves the try/except wiring exists; this proves the actual
    SAVEPOINT-rollback-on-DB-error path works against a genuine DB
    constraint violation (skills.name is NOT NULL), not just a Python
    exception raised before any statement executes. Confirms
    session.is_active stays True afterward and the outer transaction
    (the Assignment) is still intact and committable."""
    async def _real_db_failure(session, skill_id):
        await session.execute(update(Skill).where(Skill.id == skill_id).values(name=None))

    async with _seeded_session() as session:
        skill = await _make_test_skill(session)
        hr_user = CurrentUser(role=Role.HR_ADMIN, user_id=str(RITA_ID))
        request = CreateAssignmentRequest(employee_id=CASEY_ID, skill_id=skill.id)

        with mock.patch.object(assignments_service, "mark_ever_assigned", _real_db_failure):
            response = await create_assignment_service(session, current_user=hr_user, request=request)

        assert response.employee_id == CASEY_ID
        assert response.skill_id == skill.id
        assert session.is_active

        existing = await find_existing_assignment(session, employee_id=CASEY_ID, skill_id=skill.id)
        assert any(a.id == response.id for a in existing)
