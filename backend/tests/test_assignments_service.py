"""Live-DB tests for assignments/service.py (Story 3.1 AC4, AC6).

Uses a private engine/session-factory rather than the shared `app.core.db.engine`
singleton — see test_assignments_repository.py's module docstring for why
(cross-module-loop connection-pool corruption when two module-scoped-loop test
files share the same pooled engine)."""
from contextlib import asynccontextmanager

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.repository import list_assignments_for_employee
from app.assignments.schemas import AssignmentStatus, CreateAssignmentRequest
from app.assignments.service import create_assignment_service
from app.auth.repository import find_account
from app.auth.schemas import CurrentUser, Role
from app.core.config import settings
from app.core.errors import AppException
from app.core.seeds import CASEY_ID, RITA_ID, SKILL_DATA_VIZ_ID, run_seeds

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
