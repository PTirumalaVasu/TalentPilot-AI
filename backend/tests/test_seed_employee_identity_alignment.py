"""Live-DB tests: seeded Employees must align exactly with their paired
Account rows, not just overlap loosely (Story 3.3 AC5).

Regression coverage for the bug Story 3.1's code review found and fixed:
the old mock accounts dict previously issued user_id as plain names
("rita", "casey", ...), disconnected from core/seeds.py's real Employee.id
UUIDs. core/seed_ids.py now aligns them (and, since the auth-wiring fix,
Account.id IS the real Employee.id by construction, AR-24) -- this file
still asserts that alignment explicitly.

Uses a private engine/session-factory, not the shared app.core.db.engine
singleton — see test_assignments_repository.py's module docstring (Story 3.1)
for why: two module-scoped-loop live-DB test files sharing the same pooled
engine corrupt each other's connections.
"""
import uuid
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth import service as auth_service
from app.auth.repository import get_account_by_email_ci
from app.auth.schemas import Role
from app.core.config import settings
from app.employees.models import Employee
from app.core.seed_ids import CASEY_ID, JORDAN_ID, MORGAN_ID, RITA_ID, SAM_ID
from app.core.seeds import run_seeds, seed_employees

pytestmark = pytest.mark.asyncio(loop_scope="module")

_engine = create_async_engine(settings.DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)

# Mirrors core/seeds.py::seed_employees's hardcoded demo roster -- not
# derived from a live dict anymore now that accounts are real DB rows, not
# an importable module-level mapping.
_DEMO_ACCOUNTS = [
    ("rita@sails.example.com", RITA_ID, "HR_ADMIN"),
    ("casey@sails.example.com", CASEY_ID, "EMPLOYEE"),
    ("morgan@sails.example.com", MORGAN_ID, "EMPLOYEE"),
    ("jordan@sails.example.com", JORDAN_ID, "EMPLOYEE"),
    ("sam@sails.example.com", SAM_ID, "EMPLOYEE"),
]
_DEMO_EMPLOYEE_IDS = [employee_id for _, employee_id, _ in _DEMO_ACCOUNTS]


@asynccontextmanager
async def _seeded_session():
    async with _session_factory() as session:
        await run_seeds(session)
        try:
            yield session
        finally:
            await session.rollback()


@pytest.mark.parametrize(("email", "expected_id", "expected_role"), _DEMO_ACCOUNTS)
async def test_seeded_employee_id_matches_account_id(email, expected_id, expected_role):
    async with _seeded_session() as session:
        account = await get_account_by_email_ci(session, email)
        assert account is not None, f"No account for {email}"
        assert account.id == expected_id

        result = await session.execute(select(Employee).where(Employee.id == expected_id))
        employee = result.scalar_one()

        assert employee.email == email
        assert employee.role == expected_role


@pytest.mark.parametrize(("email", "expected_id", "expected_role"), _DEMO_ACCOUNTS)
async def test_account_role_matches_seeded_employee_role(email, expected_id, expected_role):
    async with _seeded_session() as session:
        account = await get_account_by_email_ci(session, email)
        assert account is not None, f"No account for {email}"

        result = await session.execute(select(Employee).where(Employee.id == expected_id))
        employee = result.scalar_one()

        assert account.role == employee.role == expected_role


async def test_login_normalizes_case_and_whitespace_before_lookup():
    """authenticate()'s email lookup strips + lowercases before matching
    (auth/service.py: .strip() + get_account_by_email_ci's case-insensitive
    query) — every other test in this file uses already-lowercase/trimmed
    emails, so this proves the normalization path actually works, not just
    that it's compatible with already-normalized input."""
    async with _seeded_session() as session:
        user_id, role = await auth_service.authenticate(session, "  Rita@Sails.Example.COM  ", "demo123")
        assert uuid.UUID(user_id) == RITA_ID
        assert role == Role.HR_ADMIN

        result = await session.execute(select(Employee).where(Employee.id == RITA_ID))
        employee = result.scalar_one()
        assert employee.email == "rita@sails.example.com"


async def test_exactly_one_hr_admin_and_four_employees_seeded():
    async with _seeded_session() as session:
        result = await session.execute(select(Employee).where(Employee.id.in_(_DEMO_EMPLOYEE_IDS)))
        employees = result.scalars().all()

        hr_admins = [e for e in employees if e.role == "HR_ADMIN"]
        regular_employees = [e for e in employees if e.role == "EMPLOYEE"]

        assert len(employees) == 5
        assert len(hr_admins) == 1
        assert hr_admins[0].id == RITA_ID
        assert len(regular_employees) == 4


async def test_seed_employees_is_idempotent_at_the_function_level():
    """test_database_schema.py::test_seed_script_idempotent already covers this
    via the full run_seeds() pipeline; this isolates seed_employees() itself so
    a future change to seed_skills()/create_default_accounts() can't mask a
    seed_employees() regression.

    Explicitly deletes the 5 demo employee rows within this test's own
    uncommitted transaction first, rather than assuming a fresh DB — other
    tests in this module commit seed data via run_seeds() (seeds.py's
    run_seeds() ends with session.commit()), so without this, seed_employees()
    would already be a no-op on its *first* call here too, and the test would
    never actually observe the insert path it claims to test. The final
    rollback restores whatever state existed before this test ran.

    The delete runs against settings.DATABASE_URL — the same shared dev DB
    every other live-DB test in this suite uses, not an isolated test DB.
    assignments/assignment_overrides/skill_progress all FK-reference
    employees.id with no ondelete=CASCADE (default RESTRICT), so if any
    committed row anywhere ever references one of these 5 IDs, the delete
    raises IntegrityError. Today nothing commits such a row (the assignments
    test files only ever roll back their inserts), but skip cleanly instead
    of crashing confusingly if that ever changes."""
    async with _session_factory() as session:
        try:
            try:
                delete_result = await session.execute(delete(Employee).where(Employee.id.in_(_DEMO_EMPLOYEE_IDS)))
                await session.flush()
            except IntegrityError:
                pytest.skip(
                    "Demo employees are referenced by other committed rows "
                    "(assignments/overrides/progress) — cannot safely delete "
                    "to exercise the insert path of this idempotency check."
                )

            baseline = await session.execute(select(Employee).where(Employee.id.in_(_DEMO_EMPLOYEE_IDS)))
            assert baseline.scalars().all() == []
            # rowcount is 5 when run after other tests in this module (which
            # commit seed data via run_seeds()) and 0 when this test runs in
            # isolation against a DB with no demo employees yet — both are
            # legitimate starting states once the baseline check above
            # confirms empty; anything else means an unexpected partial state.
            assert delete_result.rowcount in (0, 5), (
                f"Expected to delete 0 or 5 pre-existing demo employees, deleted {delete_result.rowcount}"
            )

            await seed_employees(session)
            result1 = await session.execute(select(Employee).where(Employee.id.in_(_DEMO_EMPLOYEE_IDS)))
            count1 = len(result1.scalars().all())
            assert count1 == 5

            await seed_employees(session)  # second call must be a true no-op
            result2 = await session.execute(select(Employee).where(Employee.id.in_(_DEMO_EMPLOYEE_IDS)))
            count2 = len(result2.scalars().all())

            assert count1 == count2 == 5
        finally:
            await session.rollback()
