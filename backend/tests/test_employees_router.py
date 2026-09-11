"""Router-level tests for employees/router.py's POST /api/admin/employees
(Story 7.2, FR-24).

Mirrors test_skills_router.py's pattern exactly: real app.main.app via
ASGITransport, plus a private engine/session purely for cleaning up rows
this file creates (NOT the shared db_session fixture, which wipes the whole
dev DB on teardown).
"""
import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.repository import list_employees
from app.auth.models import Account
from app.core.config import settings
from app.employees.models import Employee
from app.employees.service import verify_password
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


async def _delete_employee_by_code(employee_code: str) -> None:
    async with _session_factory() as session:
        result = await session.execute(select(Employee).where(Employee.employee_code == employee_code))
        employee = result.scalar_one_or_none()
        if employee is not None:
            await session.execute(delete(Account).where(Account.id == employee.id))
            await session.execute(delete(Employee).where(Employee.id == employee.id))
            await session.commit()


async def test_create_employee_with_only_required_fields_returns_201():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    email = f"{code.lower()}@example.com"
    try:
        async with _client() as client:
            await _login(client)
            response = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "New Hire", "email": email},
            )

            assert response.status_code == 201
            body = response.json()
            assert body["employee_code"] == code
            assert body["name"] == "New Hire"
            assert body["email"] == email
            assert body["role"] == "EMPLOYEE"
            assert "generated_password" in body
            assert len(body["generated_password"]) == 12

            async with _session_factory() as session:
                account_result = await session.execute(select(Account).where(Account.id == body["id"]))
                account = account_result.scalar_one()
                assert account.email == email
                assert account.role == "EMPLOYEE"
                assert verify_password(body["generated_password"], account.password_hash) is True
    finally:
        await _delete_employee_by_code(code)


async def test_create_employee_omitted_optional_fields_are_null():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    email = f"{code.lower()}@example.com"
    try:
        async with _client() as client:
            await _login(client)
            response = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Minimal Fields", "email": email},
            )

            assert response.status_code == 201
            body = response.json()
            for field in (
                "phone", "experience", "technologies", "position",
                "project", "manager_name", "location", "department",
            ):
                assert body[field] is None
            assert body["archived_at"] is None
    finally:
        await _delete_employee_by_code(code)


async def test_create_employee_is_immediately_visible_in_the_assignment_picker():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    email = f"{code.lower()}@example.com"
    try:
        async with _client() as client:
            await _login(client)
            response = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Pickable Hire", "email": email},
            )
            employee_id = response.json()["id"]

        async with _session_factory() as session:
            employees = await list_employees(session)
            assert any(str(e.id) == employee_id for e in employees)
    finally:
        await _delete_employee_by_code(code)


async def test_create_employee_duplicate_employee_code_returns_409():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            first = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "First", "email": f"{code.lower()}-a@example.com"},
            )
            assert first.status_code == 201

            second = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Second", "email": f"{code.lower()}-b@example.com"},
            )

            assert second.status_code == 409
            body = second.json()
            assert body["status"] == "error"
            assert body["code"] == "EMPLOYEE_CODE_CONFLICT"
            assert code in body["message"]
    finally:
        await _delete_employee_by_code(code)


async def test_create_employee_duplicate_email_different_case_returns_409():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    email = f"{code.lower()}@example.com"
    try:
        async with _client() as client:
            await _login(client)
            first = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "First", "email": email},
            )
            assert first.status_code == 201

            second_code = f"TST-{uuid.uuid4().hex[:8]}"
            second = await client.post(
                "/api/admin/employees",
                json={"employee_code": second_code, "name": "Second", "email": email.upper()},
            )

            assert second.status_code == 409
            body = second.json()
            assert body["code"] == "EMPLOYEE_EMAIL_CONFLICT"
    finally:
        await _delete_employee_by_code(code)


async def test_create_employee_account_side_email_conflict_returns_409_not_500():
    # Regression test for a Story 7.2 code review finding: the
    # IntegrityError backstop only re-checked `employees`, so a failure on
    # the *Account* insert (e.g. a stale accounts.email left over from some
    # future Employee-edit story letting the two tables' emails drift apart,
    # FR-26's own [ASSUMPTION]) fell through to a raw, unattributed 500
    # instead of a clean 409.
    code_a = f"TST-{uuid.uuid4().hex[:8]}"
    email_a = f"{code_a.lower()}@example.com"
    stale_email = f"stale-{uuid.uuid4().hex[:8]}@example.com"
    code_b = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created_a = await client.post(
                "/api/admin/employees",
                json={"employee_code": code_a, "name": "Employee A", "email": email_a},
            )
            assert created_a.status_code == 201
            employee_a_id = created_a.json()["id"]

            # Simulate the desync directly -- no story yet lets this happen
            # through the API itself.
            async with _session_factory() as session:
                account_a = (
                    await session.execute(select(Account).where(Account.id == employee_a_id))
                ).scalar_one()
                account_a.email = stale_email
                await session.commit()

            response = await client.post(
                "/api/admin/employees",
                json={"employee_code": code_b, "name": "Employee B", "email": stale_email},
            )

            assert response.status_code == 409
            assert response.json()["code"] == "EMPLOYEE_EMAIL_CONFLICT"

            # The failed create must not leave an orphaned Employee row behind.
            async with _session_factory() as session:
                result = await session.execute(select(Employee).where(Employee.employee_code == code_b))
                assert result.scalar_one_or_none() is None
    finally:
        await _delete_employee_by_code(code_a)
        await _delete_employee_by_code(code_b)


async def test_create_employee_as_employee_returns_403():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client, email="casey@sails.example.com")
            response = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Forbidden", "email": f"{code.lower()}@example.com"},
            )
            assert response.status_code == 403
    finally:
        await _delete_employee_by_code(code)


async def test_create_employee_requires_authentication():
    async with _client() as client:
        response = await client.post(
            "/api/admin/employees",
            json={"employee_code": "TST-NOAUTH", "name": "No Auth", "email": "noauth@example.com"},
        )
        assert response.status_code == 401


async def test_create_employee_rejects_missing_required_field():
    async with _client() as client:
        await _login(client)
        response = await client.post(
            "/api/admin/employees",
            json={"name": "Missing Code And Email"},
        )
        assert response.status_code == 422


async def test_create_employee_rejects_blank_name():
    async with _client() as client:
        await _login(client)
        response = await client.post(
            "/api/admin/employees",
            json={"employee_code": f"TST-{uuid.uuid4().hex[:8]}", "name": "   ", "email": "blank@example.com"},
        )
        assert response.status_code == 422


async def test_create_employee_rejects_invalid_email():
    async with _client() as client:
        await _login(client)
        response = await client.post(
            "/api/admin/employees",
            json={"employee_code": f"TST-{uuid.uuid4().hex[:8]}", "name": "Bad Email", "email": "not-an-email"},
        )
        assert response.status_code == 422


async def test_create_employee_rejects_unknown_field():
    async with _client() as client:
        await _login(client)
        response = await client.post(
            "/api/admin/employees",
            json={
                "employee_code": f"TST-{uuid.uuid4().hex[:8]}",
                "name": "Unknown Field",
                "email": "unknown@example.com",
                "salary": 100000,
            },
        )
        assert response.status_code == 422


# --- Story 7.3: GET /api/admin/employees (roster, FR-25) ---------------------


async def test_list_employees_returns_full_roster_with_all_fields():
    # Code review (Story 7.3): the original version of this test only
    # checked field *presence*, not that values actually round-trip -- a
    # mapping bug (e.g. two columns swapped in EmployeeResponse) would have
    # passed undetected. Populate every optional field on employee A and
    # assert each one explicitly.
    code_a = f"TST-{uuid.uuid4().hex[:8]}"
    code_b = f"TST-{uuid.uuid4().hex[:8]}"
    email_a = f"{code_a.lower()}@example.com"
    try:
        async with _client() as client:
            await _login(client)
            await client.post(
                "/api/admin/employees",
                json={
                    "employee_code": code_a,
                    "name": "Roster A",
                    "email": email_a,
                    "phone": "555-0100",
                    "experience": "5 years",
                    "technologies": "Python, React",
                    "position": "Engineer",
                    "project": "Project Phoenix",
                    "manager_name": "Alex Manager",
                    "location": "Remote",
                    "department": "Engineering",
                },
            )
            await client.post(
                "/api/admin/employees",
                json={"employee_code": code_b, "name": "Roster B", "email": f"{code_b.lower()}@example.com"},
            )

            response = await client.get("/api/admin/employees")

            assert response.status_code == 200
            body = response.json()
            codes = [e["employee_code"] for e in body]
            assert code_a in codes
            assert code_b in codes

            entry = next(e for e in body if e["employee_code"] == code_a)
            assert entry["employee_code"] == code_a
            assert entry["name"] == "Roster A"
            assert entry["email"] == email_a
            assert entry["role"] == "EMPLOYEE"
            assert entry["phone"] == "555-0100"
            assert entry["experience"] == "5 years"
            assert entry["technologies"] == "Python, React"
            assert entry["position"] == "Engineer"
            assert entry["project"] == "Project Phoenix"
            assert entry["manager_name"] == "Alex Manager"
            assert entry["location"] == "Remote"
            assert entry["department"] == "Engineering"
            assert entry["archived_at"] is None
            for field in ("id", "created_at", "updated_at"):
                assert field in entry
            assert "generated_password" not in entry
            assert "password" not in entry
            assert "password_hash" not in entry
    finally:
        await _delete_employee_by_code(code_a)
        await _delete_employee_by_code(code_b)


async def test_list_employees_includes_archived_rows_unfiltered():
    # Story 7.5 (archive) doesn't exist yet -- set archived_at directly to
    # prove the endpoint itself applies no archived_at filter (Scope Note 2 /
    # Task 1: filtering is the frontend's job).
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Archived Row", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

        async with _session_factory() as session:
            result = await session.execute(select(Employee).where(Employee.id == employee_id))
            employee = result.scalar_one()
            employee.archived_at = datetime.now(timezone.utc)
            await session.commit()

        async with _client() as client:
            await _login(client)
            response = await client.get("/api/admin/employees")
            assert response.status_code == 200
            entry = next(e for e in response.json() if e["employee_code"] == code)
            assert entry["archived_at"] is not None
    finally:
        await _delete_employee_by_code(code)


async def test_list_employees_ordered_by_employee_code_ascending():
    prefix = uuid.uuid4().hex[:8]
    code_z = f"TST-{prefix}-Z"
    code_a = f"TST-{prefix}-A"
    try:
        async with _client() as client:
            await _login(client)
            # Create in descending order to prove the response isn't just
            # insertion/created_at order.
            await client.post(
                "/api/admin/employees",
                json={"employee_code": code_z, "name": "Z Employee", "email": f"{prefix.lower()}-z@example.com"},
            )
            await client.post(
                "/api/admin/employees",
                json={"employee_code": code_a, "name": "A Employee", "email": f"{prefix.lower()}-a@example.com"},
            )

            response = await client.get("/api/admin/employees")
            codes = [e["employee_code"] for e in response.json() if e["employee_code"] in (code_z, code_a)]
            assert codes == [code_a, code_z]
    finally:
        await _delete_employee_by_code(code_a)
        await _delete_employee_by_code(code_z)


async def test_list_employees_as_employee_returns_403():
    async with _client() as client:
        await _login(client, email="casey@sails.example.com")
        response = await client.get("/api/admin/employees")
        assert response.status_code == 403


async def test_list_employees_requires_authentication():
    async with _client() as client:
        response = await client.get("/api/admin/employees")
        assert response.status_code == 401
