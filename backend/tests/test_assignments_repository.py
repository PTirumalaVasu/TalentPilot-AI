"""Live-DB tests for assignments/repository.py (Story 3.1 AC1, AC2, AC5).

Uses a **private** engine/session-factory (same settings.DATABASE_URL as
`app.core.db`, but its own connection pool) rather than importing the shared
`app.core.db.engine` singleton `test_database_schema.py` uses. Two prior
approaches were tried and rejected, both empirically:
  1. A `pytest-asyncio` async-generator fixture — conflicts with
     `loop_scope="module"` (`AssertionError` at fixture setup), autouse or not.
  2. Reusing the shared `app.core.db.engine` directly — its pooled connections
     stay bound to whichever module-scoped loop touched them first, and get
     corrupted the moment a *second* module-scoped-loop test file (this one)
     touches the same pool, breaking `test_database_schema.py` too when run in
     the same session (a wider version of the single-file loop-binding bug
     Story 1.7 already fixed once). A private pool sidesteps this: nothing
     else references it, so there's no cross-file loop to corrupt.
A plain async context-manager helper (not a fixture) opens/rolls back each
test's session, since this module-scoped loop still can't host a
pytest-asyncio async fixture.
"""
from contextlib import asynccontextmanager

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import ContentCatalog
from app.assignments.repository import (
    create_assignment,
    find_existing_assignment,
    list_assignments_for_employee,
)
from app.auth.schemas import CurrentUser, Role
from app.core.config import settings
from app.core.seeds import (
    CASEY_ID,
    MORGAN_ID,
    RITA_ID,
    SKILL_DATA_VIZ_ID,
    SKILL_PYTHON_ID,
    run_seeds,
)

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


async def test_create_assignment_inserts_and_returns_row():
    async with _seeded_session() as session:
        assignment = await create_assignment(
            session,
            employee_id=CASEY_ID,
            skill_id=SKILL_DATA_VIZ_ID,
            content_id=None,
            assigned_by=RITA_ID,
        )

        assert assignment.id is not None
        assert assignment.employee_id == CASEY_ID
        assert assignment.skill_id == SKILL_DATA_VIZ_ID
        assert assignment.content_id is None
        assert assignment.assigned_by == RITA_ID
        assert assignment.assigned_at is not None


async def test_create_assignment_stores_a_real_content_id():
    """AC1's content_id is a nullable FK to content_catalog — this covers the
    populated path (every other test in this file passes content_id=None)."""
    async with _seeded_session() as session:
        content = ContentCatalog(
            skill_id=SKILL_DATA_VIZ_ID,
            title="Intro to Data Visualization",
            type="VIDEO",
            url="https://example.com/video",
            embedding=[0.0] * 384,
            source="MANUAL",
        )
        session.add(content)
        await session.flush()

        assignment = await create_assignment(
            session,
            employee_id=CASEY_ID,
            skill_id=SKILL_DATA_VIZ_ID,
            content_id=content.id,
            assigned_by=RITA_ID,
        )

        assert assignment.content_id == content.id


async def test_create_assignment_allows_repeat_employee_skill_pair():
    """AC2: (employee_id, skill_id) may repeat — each row is a distinct Assignment."""
    async with _seeded_session() as session:
        first = await create_assignment(
            session, employee_id=CASEY_ID, skill_id=SKILL_PYTHON_ID, content_id=None, assigned_by=RITA_ID
        )
        second = await create_assignment(
            session, employee_id=CASEY_ID, skill_id=SKILL_PYTHON_ID, content_id=None, assigned_by=RITA_ID
        )

        assert first.id != second.id


async def test_find_existing_assignment_returns_matching_rows():
    async with _seeded_session() as session:
        created = await create_assignment(
            session, employee_id=MORGAN_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )

        found = await find_existing_assignment(session, employee_id=MORGAN_ID, skill_id=SKILL_DATA_VIZ_ID)

        assert any(a.id == created.id for a in found)


async def test_find_existing_assignment_returns_empty_when_no_match():
    async with _seeded_session() as session:
        found = await find_existing_assignment(session, employee_id=MORGAN_ID, skill_id=SKILL_PYTHON_ID)

        assert found == []


async def test_employee_scoped_list_ignores_spoofed_employee_id():
    """AC5: an EMPLOYEE session must never see another employee's rows, even if
    it passes a different employee_id — the override is silently ignored."""
    async with _seeded_session() as session:
        await create_assignment(
            session, employee_id=CASEY_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )
        await create_assignment(
            session, employee_id=MORGAN_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )

        casey_user = CurrentUser(role=Role.EMPLOYEE, user_id=str(CASEY_ID))

        # Casey spoofs Morgan's employee_id — must still only get Casey's own rows.
        results = await list_assignments_for_employee(
            session, current_user=casey_user, requested_employee_id=MORGAN_ID
        )

        assert any(a.employee_id == CASEY_ID for a in results)
        assert not any(a.employee_id == MORGAN_ID for a in results)


async def test_hr_admin_scoped_list_returns_all_employees_rows():
    async with _seeded_session() as session:
        await create_assignment(
            session, employee_id=CASEY_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )
        await create_assignment(
            session, employee_id=MORGAN_ID, skill_id=SKILL_PYTHON_ID, content_id=None, assigned_by=RITA_ID
        )

        hr_user = CurrentUser(role=Role.HR_ADMIN, user_id=str(RITA_ID))

        results = await list_assignments_for_employee(session, current_user=hr_user, requested_employee_id=None)

        employee_ids = {a.employee_id for a in results}
        assert CASEY_ID in employee_ids
        assert MORGAN_ID in employee_ids


async def test_hr_admin_scoped_list_can_filter_by_requested_employee_id():
    """Unlike EMPLOYEE sessions, HR_ADMIN's own employee_id filter is honored,
    not ignored — it's a real filter, not a spoof-defense."""
    async with _seeded_session() as session:
        await create_assignment(
            session, employee_id=CASEY_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )
        await create_assignment(
            session, employee_id=MORGAN_ID, skill_id=SKILL_PYTHON_ID, content_id=None, assigned_by=RITA_ID
        )

        hr_user = CurrentUser(role=Role.HR_ADMIN, user_id=str(RITA_ID))

        results = await list_assignments_for_employee(session, current_user=hr_user, requested_employee_id=CASEY_ID)

        # any(...) first: all() over an empty list is vacuously True and
        # wouldn't catch a filter that incorrectly returns zero rows.
        assert any(a.employee_id == CASEY_ID for a in results)
        assert all(a.employee_id == CASEY_ID for a in results)


async def test_employee_scoped_list_returns_own_rows_with_no_requested_employee_id():
    """Default-usage case (no spoofing attempt): requested_employee_id isn't
    even passed. Distinct from test_employee_scoped_list_ignores_spoofed_employee_id,
    which only covers the override-supplied path."""
    async with _seeded_session() as session:
        await create_assignment(
            session, employee_id=CASEY_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )
        await create_assignment(
            session, employee_id=MORGAN_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )

        casey_user = CurrentUser(role=Role.EMPLOYEE, user_id=str(CASEY_ID))

        results = await list_assignments_for_employee(session, current_user=casey_user)

        assert any(a.employee_id == CASEY_ID for a in results)
        assert not any(a.employee_id == MORGAN_ID for a in results)
