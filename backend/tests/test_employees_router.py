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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import Assignment
from app.assignments.repository import list_employees
from app.auth.models import Account
from app.core.config import settings
from app.core.seeds import SKILL_DATA_VIZ_ID
from app.employees.models import Employee
from app.employees.repository import get_employee_for_update
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


# --- Story 7.4: PATCH /api/admin/employees/{employee_id} (edit, FR-26) -------


def _update_payload(**overrides) -> dict:
    payload = {
        "name": "Updated Name",
        "email": "updated@example.com",
        "phone": "555-0199",
        "experience": "10 years",
        "technologies": "Go, Kubernetes",
        "position": "Senior Engineer",
        "project": "Project Atlas",
        "manager_name": "Jordan Manager",
        "location": "Austin",
        "department": "Platform",
    }
    payload.update(overrides)
    return payload


async def test_update_employee_all_editable_fields_returns_200():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Original Name", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

            new_email = f"{code.lower()}-new@example.com"
            response = await client.patch(
                f"/api/admin/employees/{employee_id}",
                json=_update_payload(email=new_email),
            )

            assert response.status_code == 200
            body = response.json()
            assert body["employee_code"] == code  # immutable -- never in the request, unchanged in the response
            assert body["name"] == "Updated Name"
            assert body["email"] == new_email
            assert body["phone"] == "555-0199"
            assert body["experience"] == "10 years"
            assert body["technologies"] == "Go, Kubernetes"
            assert body["position"] == "Senior Engineer"
            assert body["project"] == "Project Atlas"
            assert body["manager_name"] == "Jordan Manager"
            assert body["location"] == "Austin"
            assert body["department"] == "Platform"
    finally:
        await _delete_employee_by_code(code)


async def test_update_employee_succeeds_regardless_of_assignment_history():
    # AC1: no lock, unlike a Skill's identity-lock -- an Employee with real
    # Assignment history is still fully editable.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    employee_id = None
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Has History", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

            assignment_response = await client.post(
                "/api/assignments",
                json={"employee_id": employee_id, "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assert assignment_response.status_code == 201

            response = await client.patch(
                f"/api/admin/employees/{employee_id}",
                json=_update_payload(email=f"{code.lower()}-2@example.com"),
            )
            assert response.status_code == 200
            assert response.json()["name"] == "Updated Name"
    finally:
        if employee_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(Assignment).where(Assignment.employee_id == uuid.UUID(employee_id)))
                await session.commit()
        await _delete_employee_by_code(code)


async def test_update_employee_rejects_employee_code_in_body():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Original", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

            response = await client.patch(
                f"/api/admin/employees/{employee_id}",
                json=_update_payload(employee_code="TST-SHOULD-NOT-BE-ACCEPTED"),
            )
            assert response.status_code == 422
    finally:
        await _delete_employee_by_code(code)


async def test_update_employee_duplicate_email_returns_409():
    code_a = f"TST-{uuid.uuid4().hex[:8]}"
    code_b = f"TST-{uuid.uuid4().hex[:8]}"
    email_a = f"{code_a.lower()}@example.com"
    try:
        async with _client() as client:
            await _login(client)
            await client.post(
                "/api/admin/employees",
                json={"employee_code": code_a, "name": "First", "email": email_a},
            )
            created_b = await client.post(
                "/api/admin/employees",
                json={"employee_code": code_b, "name": "Second", "email": f"{code_b.lower()}@example.com"},
            )
            employee_b_id = created_b.json()["id"]

            response = await client.patch(
                f"/api/admin/employees/{employee_b_id}",
                json=_update_payload(email=email_a.upper()),
            )

            assert response.status_code == 409
            body = response.json()
            assert body["status"] == "error"
            assert body["code"] == "EMPLOYEE_EMAIL_CONFLICT"
    finally:
        await _delete_employee_by_code(code_a)
        await _delete_employee_by_code(code_b)


async def test_update_employee_unchanged_email_does_not_conflict():
    # AC2/self-exclusion: re-saving with the Employee's own current email
    # (the most common real-world save) must never 409 against itself.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    email = f"{code.lower()}@example.com"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Original", "email": email},
            )
            employee_id = created.json()["id"]

            response = await client.patch(
                f"/api/admin/employees/{employee_id}",
                json=_update_payload(email=email, name="Renamed Only"),
            )

            assert response.status_code == 200
            assert response.json()["name"] == "Renamed Only"
            assert response.json()["email"] == email
    finally:
        await _delete_employee_by_code(code)


async def test_update_employee_case_only_email_change_still_syncs_account_email():
    # Code review (Story 7.4): a case-only edit (e.g. "X@example.com" ->
    # "x@example.com") is invisible to the case-insensitive conflict check
    # but must still sync Account.email, or the two tables drift apart --
    # exactly what Scope Note 4 requires this story to prevent.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            original_email = f"{code.upper()}@example.com"
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Original", "email": original_email},
            )
            employee_id = created.json()["id"]

            lowercased_email = original_email.lower()
            response = await client.patch(
                f"/api/admin/employees/{employee_id}",
                json=_update_payload(email=lowercased_email),
            )
            assert response.status_code == 200
            assert response.json()["email"] == lowercased_email

            async with _session_factory() as session:
                account = (
                    await session.execute(select(Account).where(Account.id == uuid.UUID(employee_id)))
                ).scalar_one()
                assert account.email == lowercased_email
    finally:
        await _delete_employee_by_code(code)


async def test_update_employee_account_side_email_conflict_returns_409_not_500():
    # Code review (Story 7.4): deterministically reaches the IntegrityError
    # backstop (same technique as Story 7.2's
    # test_create_employee_account_side_email_conflict_returns_409_not_500)
    # by desyncing Account A's email from Employee A's, then editing Employee
    # B's email to match the stale Account-side value -- the employees-table
    # pre-check passes cleanly (no Employee has that email), but the
    # accounts-table UPDATE collides on accounts.email's unique constraint,
    # raising a genuine IntegrityError. Regression test for a real bug found
    # in review: the backstop read `employee.id` after `db.rollback()`
    # expired it, crashing with MissingGreenlet instead of returning 409.
    code_a = f"TST-{uuid.uuid4().hex[:8]}"
    code_b = f"TST-{uuid.uuid4().hex[:8]}"
    stale_email = f"stale-{uuid.uuid4().hex[:8]}@example.com"
    try:
        async with _client() as client:
            await _login(client)
            created_a = await client.post(
                "/api/admin/employees",
                json={"employee_code": code_a, "name": "Employee A", "email": f"{code_a.lower()}@example.com"},
            )
            employee_a_id = created_a.json()["id"]
            created_b = await client.post(
                "/api/admin/employees",
                json={"employee_code": code_b, "name": "Employee B", "email": f"{code_b.lower()}@example.com"},
            )
            employee_b_id = created_b.json()["id"]

            async with _session_factory() as session:
                account_a = (
                    await session.execute(select(Account).where(Account.id == uuid.UUID(employee_a_id)))
                ).scalar_one()
                account_a.email = stale_email
                await session.commit()

            response = await client.patch(
                f"/api/admin/employees/{employee_b_id}",
                json=_update_payload(email=stale_email),
            )

            assert response.status_code == 409
            assert response.json()["code"] == "EMPLOYEE_EMAIL_CONFLICT"

            # The failed edit must not leave Employee B's fields half-updated
            # -- the rollback must undo the entire transaction, not just the
            # accounts-side write.
            async with _session_factory() as session:
                employee_b = (
                    await session.execute(select(Employee).where(Employee.id == uuid.UUID(employee_b_id)))
                ).scalar_one()
                assert employee_b.email == f"{code_b.lower()}@example.com"
                assert employee_b.name == "Employee B"
    finally:
        await _delete_employee_by_code(code_a)
        await _delete_employee_by_code(code_b)


async def test_update_employee_email_change_syncs_account_email():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Original", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

            new_email = f"{code.lower()}-synced@example.com"
            response = await client.patch(
                f"/api/admin/employees/{employee_id}",
                json=_update_payload(email=new_email),
            )
            assert response.status_code == 200

            async with _session_factory() as session:
                account = (
                    await session.execute(select(Account).where(Account.id == uuid.UUID(employee_id)))
                ).scalar_one()
                assert account.email == new_email
    finally:
        await _delete_employee_by_code(code)


async def test_update_employee_nonexistent_returns_404():
    async with _client() as client:
        await _login(client)
        response = await client.patch(
            f"/api/admin/employees/{uuid.uuid4()}",
            json=_update_payload(),
        )
        assert response.status_code == 404
        assert response.json()["code"] == "EMPLOYEE_NOT_FOUND"


async def test_update_employee_as_employee_returns_403():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Original", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

        async with _client() as client:
            await _login(client, email="casey@sails.example.com")
            response = await client.patch(
                f"/api/admin/employees/{employee_id}",
                json=_update_payload(),
            )
            assert response.status_code == 403
    finally:
        await _delete_employee_by_code(code)


async def test_update_employee_requires_authentication():
    async with _client() as client:
        response = await client.patch(
            f"/api/admin/employees/{uuid.uuid4()}",
            json=_update_payload(),
        )
        assert response.status_code == 401


async def test_update_employee_archived_employee_still_succeeds():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Archived", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

        async with _session_factory() as session:
            employee = (
                await session.execute(select(Employee).where(Employee.id == uuid.UUID(employee_id)))
            ).scalar_one()
            employee.archived_at = datetime.now(timezone.utc)
            await session.commit()

        async with _client() as client:
            await _login(client)
            response = await client.patch(
                f"/api/admin/employees/{employee_id}",
                json=_update_payload(email=f"{code.lower()}-archived@example.com"),
            )
            assert response.status_code == 200
            assert response.json()["archived_at"] is not None
    finally:
        await _delete_employee_by_code(code)


async def test_update_employee_concurrent_edits_last_write_wins():
    # AC4: no optimistic lock -- two sequential edits (simulating two HR
    # Admins) never conflict; the second write's values are what persist.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Original", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

            first = await client.patch(
                f"/api/admin/employees/{employee_id}",
                json=_update_payload(email=f"{code.lower()}-a@example.com", department="First Write"),
            )
            assert first.status_code == 200

            second = await client.patch(
                f"/api/admin/employees/{employee_id}",
                json=_update_payload(email=f"{code.lower()}-b@example.com", department="Second Write"),
            )
            assert second.status_code == 200
            assert second.json()["department"] == "Second Write"

            final = await client.get("/api/admin/employees")
            entry = next(e for e in final.json() if e["employee_code"] == code)
            assert entry["department"] == "Second Write"
    finally:
        await _delete_employee_by_code(code)


# --- Story 7.5: DELETE /api/admin/employees/{employee_id} (delete/archive, FR-27) ---


async def test_get_employee_for_update_locks_the_row():
    # AC1's atomicity requirement relies on a real `FOR UPDATE` row lock
    # (repository.get_employee_for_update's docstring explains why) --
    # rather than a flaky forced-concurrency test, assert the function's
    # own source actually issues one.
    import inspect

    source = inspect.getsource(get_employee_for_update)
    assert "with_for_update()" in source


async def test_delete_employee_with_no_assignment_history_hard_deletes():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "No History", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

            response = await client.delete(f"/api/admin/employees/{employee_id}")

            assert response.status_code == 200
            assert response.json() == {"action": "deleted"}

            async with _session_factory() as session:
                employee_result = await session.execute(
                    select(Employee).where(Employee.id == uuid.UUID(employee_id))
                )
                assert employee_result.scalar_one_or_none() is None
                account_result = await session.execute(
                    select(Account).where(Account.id == uuid.UUID(employee_id))
                )
                assert account_result.scalar_one_or_none() is None
    finally:
        await _delete_employee_by_code(code)


async def test_delete_employee_with_assignment_history_archives_instead():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    employee_id = None
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Has History", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

            assignment_response = await client.post(
                "/api/assignments",
                json={"employee_id": employee_id, "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assert assignment_response.status_code == 201
            assignment_id = assignment_response.json()["id"]

            response = await client.delete(f"/api/admin/employees/{employee_id}")

            assert response.status_code == 200
            assert response.json() == {"action": "archived"}

            async with _session_factory() as session:
                employee = (
                    await session.execute(select(Employee).where(Employee.id == uuid.UUID(employee_id)))
                ).scalar_one()
                assert employee.archived_at is not None

                account = (
                    await session.execute(select(Account).where(Account.id == uuid.UUID(employee_id)))
                ).scalar_one()
                assert account.archived_at is not None

                assignment = (
                    await session.execute(select(Assignment).where(Assignment.id == uuid.UUID(assignment_id)))
                ).scalar_one()
                assert assignment.active is True  # untouched -- history preserved
    finally:
        if employee_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(Assignment).where(Assignment.employee_id == uuid.UUID(employee_id)))
                await session.commit()
        await _delete_employee_by_code(code)


async def test_delete_employee_with_only_soft_deleted_assignment_still_archives():
    # AC1's "active or soft-deleted, per FR-15" wording -- a soft-deleted
    # Assignment still counts as history that must be preserved.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    employee_id = None
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Soft Deleted History", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

            assignment_response = await client.post(
                "/api/assignments",
                json={"employee_id": employee_id, "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assignment_id = assignment_response.json()["id"]

        async with _session_factory() as session:
            assignment = (
                await session.execute(select(Assignment).where(Assignment.id == uuid.UUID(assignment_id)))
            ).scalar_one()
            assignment.active = False
            assignment.deleted_at = datetime.now(timezone.utc)
            await session.commit()

        async with _client() as client:
            await _login(client)
            response = await client.delete(f"/api/admin/employees/{employee_id}")

            assert response.status_code == 200
            assert response.json() == {"action": "archived"}
    finally:
        if employee_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(Assignment).where(Assignment.employee_id == uuid.UUID(employee_id)))
                await session.commit()
        await _delete_employee_by_code(code)


async def test_delete_employee_archived_excluded_from_assignment_picker_not_hr_roster():
    # AC2's "every Employee picker" -- confirmed to be
    # GET /api/assignments/employees, NOT the HR roster's own
    # GET /api/admin/employees (which keeps showing archived rows for
    # Story 7.3's archived-toggle).
    code = f"TST-{uuid.uuid4().hex[:8]}"
    employee_id = None
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Picker Test", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

            assignment_response = await client.post(
                "/api/assignments",
                json={"employee_id": employee_id, "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assert assignment_response.status_code == 201

            delete_response = await client.delete(f"/api/admin/employees/{employee_id}")
            assert delete_response.json() == {"action": "archived"}

            picker_response = await client.get("/api/assignments/employees")
            assert not any(e["id"] == employee_id for e in picker_response.json())

            roster_response = await client.get("/api/admin/employees")
            assert any(e["id"] == employee_id for e in roster_response.json())
    finally:
        if employee_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(Assignment).where(Assignment.employee_id == uuid.UUID(employee_id)))
                await session.commit()
        await _delete_employee_by_code(code)


async def test_list_employees_has_assignment_history_reflects_reality():
    code_no_history = f"TST-{uuid.uuid4().hex[:8]}"
    code_has_history = f"TST-{uuid.uuid4().hex[:8]}"
    employee_with_history_id = None
    try:
        async with _client() as client:
            await _login(client)
            created_no_history = await client.post(
                "/api/admin/employees",
                json={
                    "employee_code": code_no_history,
                    "name": "No History",
                    "email": f"{code_no_history.lower()}@example.com",
                },
            )
            assert created_no_history.json()["has_assignment_history"] is False

            created_has_history = await client.post(
                "/api/admin/employees",
                json={
                    "employee_code": code_has_history,
                    "name": "Has History",
                    "email": f"{code_has_history.lower()}@example.com",
                },
            )
            employee_with_history_id = created_has_history.json()["id"]
            await client.post(
                "/api/assignments",
                json={"employee_id": employee_with_history_id, "skill_id": str(SKILL_DATA_VIZ_ID)},
            )

            roster = await client.get("/api/admin/employees")
            entries = {e["employee_code"]: e for e in roster.json()}
            assert entries[code_no_history]["has_assignment_history"] is False
            assert entries[code_has_history]["has_assignment_history"] is True
    finally:
        if employee_with_history_id is not None:
            async with _session_factory() as session:
                await session.execute(
                    delete(Assignment).where(Assignment.employee_id == uuid.UUID(employee_with_history_id))
                )
                await session.commit()
        await _delete_employee_by_code(code_no_history)
        await _delete_employee_by_code(code_has_history)


async def test_delete_employee_nonexistent_returns_404():
    async with _client() as client:
        await _login(client)
        response = await client.delete(f"/api/admin/employees/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.json()["code"] == "EMPLOYEE_NOT_FOUND"


async def test_delete_employee_as_employee_returns_403():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Original", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

        async with _client() as client:
            await _login(client, email="casey@sails.example.com")
            response = await client.delete(f"/api/admin/employees/{employee_id}")
            assert response.status_code == 403
    finally:
        await _delete_employee_by_code(code)


async def test_delete_employee_requires_authentication():
    async with _client() as client:
        response = await client.delete(f"/api/admin/employees/{uuid.uuid4()}")
        assert response.status_code == 401


async def test_hard_deleted_employee_session_not_specifically_rejected_by_ac4():
    # Deliberate scope boundary (see auth/service.py::get_current_user's
    # comment): AC4's text is scoped to ARCHIVED Employees, not hard-deleted
    # ones. get_current_user only rejects when a real Account row exists
    # AND is archived -- a *missing* Account (hard-delete) passes through
    # unchanged, since a large pre-existing slice of this codebase's test
    # suite mints tokens for fabricated/non-existent user_ids with no
    # backing Account row (PR #80's non-owning-HR-admin tests,
    # test_current_user.py, etc.) purely to exercise role/identity logic --
    # rejecting on "no such account" would break that established
    # convention app-wide. The hard-delete case still degrades gracefully
    # at the one route that actually reads the Employee row: /api/auth/me
    # 404s (its own pre-existing "Employee record not found" branch), not
    # a generic 401.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    email = f"{code.lower()}@example.com"
    employee_id = None
    try:
        async with _client() as hr_client:
            await _login(hr_client)
            created = await hr_client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Soon Hard Deleted", "email": email},
            )
            employee_id = created.json()["id"]

        from app.core.security import create_access_token

        token = create_access_token(user_id=employee_id, role="EMPLOYEE")

        async with _client() as employee_client:
            employee_client.cookies.set(settings.SESSION_COOKIE_NAME, token)
            pre_delete = await employee_client.get("/api/auth/me")
            assert pre_delete.status_code == 200

        async with _client() as hr_client:
            await _login(hr_client)
            delete_response = await hr_client.delete(f"/api/admin/employees/{employee_id}")
            assert delete_response.json() == {"action": "deleted"}  # zero history -> hard-deleted

        async with _client() as employee_client:
            employee_client.cookies.set(settings.SESSION_COOKIE_NAME, token)
            post_delete = await employee_client.get("/api/auth/me")
            assert post_delete.status_code == 404  # not 401 -- see comment above
    finally:
        if employee_id is not None:
            await _delete_employee_by_code(code)


async def test_archived_employee_with_history_session_rejected_on_next_request():
    # Same as above, but via the archive path (not hard-delete) -- confirms
    # Account.archived_at (not just a missing Account row) is what
    # get_current_user checks.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    email = f"{code.lower()}@example.com"
    employee_id = None
    try:
        async with _client() as hr_client:
            await _login(hr_client)
            created = await hr_client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Soon Archived With History", "email": email},
            )
            employee_id = created.json()["id"]
            await hr_client.post(
                "/api/assignments",
                json={"employee_id": employee_id, "skill_id": str(SKILL_DATA_VIZ_ID)},
            )

        from app.core.security import create_access_token

        token = create_access_token(user_id=employee_id, role="EMPLOYEE")

        async with _client() as hr_client:
            await _login(hr_client)
            delete_response = await hr_client.delete(f"/api/admin/employees/{employee_id}")
            assert delete_response.json() == {"action": "archived"}

        async with _client() as employee_client:
            employee_client.cookies.set(settings.SESSION_COOKIE_NAME, token)
            response = await employee_client.get("/api/auth/me")
            assert response.status_code == 401
    finally:
        if employee_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(Assignment).where(Assignment.employee_id == uuid.UUID(employee_id)))
                await session.commit()
            await _delete_employee_by_code(code)


async def test_create_assignment_against_freshly_archived_employee_returns_409():
    # AC5: the Assignment-creation service itself must reject a stale
    # picker's submission against an Employee archived since the picker
    # loaded, at confirm time -- not only at picker-load time.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    employee_id = None
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Stale Picker Target", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

            # Give them history first so the delete call archives (not
            # hard-deletes) -- AC5 is about an archived-but-still-existing
            # employee_id being submitted against.
            first_assignment = await client.post(
                "/api/assignments",
                json={"employee_id": employee_id, "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assert first_assignment.status_code == 201

            delete_response = await client.delete(f"/api/admin/employees/{employee_id}")
            assert delete_response.json() == {"action": "archived"}

            stale_submission = await client.post(
                "/api/assignments",
                json={"employee_id": employee_id, "skill_id": str(SKILL_DATA_VIZ_ID)},
            )

            assert stale_submission.status_code == 409
            assert stale_submission.json()["code"] == "EMPLOYEE_ARCHIVED"

            async with _session_factory() as session:
                count_result = await session.execute(
                    select(Assignment).where(Assignment.employee_id == uuid.UUID(employee_id))
                )
                # Only the first (pre-archive) assignment exists -- the
                # rejected stale submission created no partial row.
                assert len(count_result.scalars().all()) == 1
    finally:
        if employee_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(Assignment).where(Assignment.employee_id == uuid.UUID(employee_id)))
                await session.commit()
        await _delete_employee_by_code(code)


async def test_delete_employee_rejects_self_deletion():
    # Code review, 2026-09-12: Rita deleting her own row would archive her
    # (she has real assignment history) and 401 her own very next request
    # (AC4) with no un-archive path to recover -- rejected outright instead.
    async with _client() as client:
        rita_token = await _login(client)
        import jwt as pyjwt

        from app.core.config import settings as app_settings

        payload = pyjwt.decode(rita_token, app_settings.JWT_SECRET, algorithms=["HS256"])
        rita_id = payload["user_id"]

        response = await client.delete(f"/api/admin/employees/{rita_id}")

        assert response.status_code == 409
        assert response.json()["code"] == "CANNOT_DELETE_SELF"


async def test_delete_employee_already_archived_is_a_no_op_that_preserves_the_original_timestamp():
    # Code review, 2026-09-12: clicking Delete/Archive again on an
    # already-archived row must not silently bump archived_at, destroying
    # the original audit timestamp.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    employee_id = None
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Already Archived", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]
            await client.post(
                "/api/assignments",
                json={"employee_id": employee_id, "skill_id": str(SKILL_DATA_VIZ_ID)},
            )

            first = await client.delete(f"/api/admin/employees/{employee_id}")
            assert first.json() == {"action": "archived"}

            async with _session_factory() as session:
                original_archived_at = (
                    await session.execute(select(Employee).where(Employee.id == uuid.UUID(employee_id)))
                ).scalar_one().archived_at

            second = await client.delete(f"/api/admin/employees/{employee_id}")
            assert second.status_code == 200
            assert second.json() == {"action": "archived"}

            async with _session_factory() as session:
                employee = (
                    await session.execute(select(Employee).where(Employee.id == uuid.UUID(employee_id)))
                ).scalar_one()
                assert employee.archived_at == original_archived_at
    finally:
        if employee_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(Assignment).where(Assignment.employee_id == uuid.UUID(employee_id)))
                await session.commit()
        await _delete_employee_by_code(code)


async def test_delete_employee_has_assignment_history_covers_assigner_not_just_target():
    # Code review, 2026-09-12: an employee who has never been an Assignment
    # *target* but HAS acted as assigned_by for another employee must still
    # be archived, not hard-deleted -- and the roster's has_assignment_history
    # field must predict that correctly too (the whole point of this fix).
    admin_code = f"TST-{uuid.uuid4().hex[:8]}"
    target_code = f"TST-{uuid.uuid4().hex[:8]}"
    admin_id = None
    target_id = None
    try:
        async with _client() as client:
            await _login(client)
            created_admin = await client.post(
                "/api/admin/employees",
                json={"employee_code": admin_code, "name": "Acting Admin", "email": f"{admin_code.lower()}@example.com"},
            )
            admin_id = created_admin.json()["id"]
            created_target = await client.post(
                "/api/admin/employees",
                json={"employee_code": target_code, "name": "Assignment Target", "email": f"{target_code.lower()}@example.com"},
            )
            target_id = created_target.json()["id"]

        # Promote the new employee to HR_ADMIN directly (no signup flow for
        # this) and mint a real session for them so they can act as assigner.
        from app.core.security import create_access_token

        async with _session_factory() as session:
            account = (
                await session.execute(select(Account).where(Account.id == uuid.UUID(admin_id)))
            ).scalar_one()
            account.role = "HR_ADMIN"
            employee = (
                await session.execute(select(Employee).where(Employee.id == uuid.UUID(admin_id)))
            ).scalar_one()
            employee.role = "HR_ADMIN"
            await session.commit()

        admin_token = create_access_token(user_id=admin_id, role="HR_ADMIN")
        async with _client() as acting_admin_client:
            acting_admin_client.cookies.set(settings.SESSION_COOKIE_NAME, admin_token)
            assign_response = await acting_admin_client.post(
                "/api/assignments",
                json={"employee_id": target_id, "skill_id": str(SKILL_DATA_VIZ_ID)},
            )
            assert assign_response.status_code == 201

        async with _client() as client:
            await _login(client)
            roster = await client.get("/api/admin/employees")
            entry = next(e for e in roster.json() if e["id"] == admin_id)
            assert entry["has_assignment_history"] is True  # never a target, but IS an assigner

            response = await client.delete(f"/api/admin/employees/{admin_id}")
            assert response.status_code == 200
            assert response.json() == {"action": "archived"}  # not "deleted" -- assigned_by blocks hard-delete
    finally:
        if target_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(Assignment).where(Assignment.employee_id == uuid.UUID(target_id)))
                await session.commit()
            await _delete_employee_by_code(target_code)
        if admin_id is not None:
            await _delete_employee_by_code(admin_code)


async def test_delete_employee_integrity_error_with_fk_violation_falls_back_to_archive(monkeypatch):
    # Code review, 2026-09-12: the IntegrityError fallback is now a
    # defensive-only backstop (the pre-check covers all known FKs), so
    # reaching it for a real, currently-unknown FK requires simulating one.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    employee_id = None
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Fake FK Violation", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

        from app.employees import repository as employees_repository

        class _FakeOrig(Exception):
            sqlstate = "23503"  # foreign_key_violation

        async def _raise_fk_violation(db, employee):
            raise IntegrityError("DELETE FROM employees", {}, _FakeOrig())

        monkeypatch.setattr(employees_repository, "hard_delete_employee", _raise_fk_violation)

        async with _client() as client:
            await _login(client)
            response = await client.delete(f"/api/admin/employees/{employee_id}")

            assert response.status_code == 200
            assert response.json() == {"action": "archived"}

        async with _session_factory() as session:
            employee = (
                await session.execute(select(Employee).where(Employee.id == uuid.UUID(employee_id)))
            ).scalar_one()
            assert employee.archived_at is not None
    finally:
        if employee_id is not None:
            await _delete_employee_by_code(code)


async def test_delete_employee_integrity_error_without_fk_violation_reraises(monkeypatch):
    # Code review, 2026-09-12: an unrelated integrity violation must not be
    # silently reported as a successful archive.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    employee_id = None
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Fake Other Error", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

        from app.employees import repository as employees_repository

        class _FakeOrig(Exception):
            sqlstate = "23505"  # unique_violation -- not a FK violation

        async def _raise_other_error(db, employee):
            raise IntegrityError("DELETE FROM employees", {}, _FakeOrig())

        monkeypatch.setattr(employees_repository, "hard_delete_employee", _raise_other_error)

        async with _client() as client:
            await _login(client)
            # httpx's ASGITransport re-raises an unhandled exception to the
            # caller rather than converting it to a response (the framework
            # would return 500 for a real deployed server) -- asserting the
            # exception itself is what proves this ISN'T silently swallowed
            # and reported as a successful archive.
            with pytest.raises(IntegrityError):
                await client.delete(f"/api/admin/employees/{employee_id}")
    finally:
        if employee_id is not None:
            await _delete_employee_by_code(code)


# --- Story 7.6: POST /{employee_id}/regenerate-password (FR-28) ---------


async def test_regenerate_password_active_employee_returns_new_password():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Regen Target", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]
            old_password = created.json()["generated_password"]

            response = await client.post(f"/api/admin/employees/{employee_id}/regenerate-password")

            assert response.status_code == 200
            body = response.json()
            assert body["id"] == employee_id
            assert body["employee_code"] == code
            assert "generated_password" in body
            new_password = body["generated_password"]
            assert len(new_password) == 12
            assert new_password != old_password
            assert body["has_assignment_history"] is False

            async with _session_factory() as session:
                account_result = await session.execute(select(Account).where(Account.id == employee_id))
                account = account_result.scalar_one()
                # AC1: the previous password must stop working, not just "a
                # new one exists" -- confirms real invalidation, not a no-op.
                assert verify_password(old_password, account.password_hash) is False
                assert verify_password(new_password, account.password_hash) is True
    finally:
        await _delete_employee_by_code(code)


async def test_regenerate_password_reflects_true_has_assignment_history():
    # Code review, 2026-09-12: the other AC1 test only covers a
    # freshly-created employee (always False by construction) -- this
    # exercises the True branch, mirroring
    # test_list_employees_has_assignment_history_reflects_reality's pattern.
    code = f"TST-{uuid.uuid4().hex[:8]}"
    employee_id = None
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Has History Regen", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]
            assert created.json()["has_assignment_history"] is False

            await client.post(
                "/api/assignments",
                json={"employee_id": employee_id, "skill_id": str(SKILL_DATA_VIZ_ID)},
            )

            response = await client.post(f"/api/admin/employees/{employee_id}/regenerate-password")

            assert response.status_code == 200
            assert response.json()["has_assignment_history"] is True
    finally:
        if employee_id is not None:
            async with _session_factory() as session:
                await session.execute(delete(Assignment).where(Assignment.employee_id == uuid.UUID(employee_id)))
                await session.commit()
        await _delete_employee_by_code(code)


async def test_regenerate_password_never_leaks_plaintext_via_list_endpoint():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "No Leak", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

            await client.post(f"/api/admin/employees/{employee_id}/regenerate-password")

            list_response = await client.get("/api/admin/employees")
            assert list_response.status_code == 200
            entry = next(e for e in list_response.json() if e["id"] == employee_id)
            assert "generated_password" not in entry
            assert "password" not in entry
            assert "password_hash" not in entry
    finally:
        await _delete_employee_by_code(code)


async def test_regenerate_password_archived_employee_returns_409_and_leaves_hash_unchanged():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Archived Regen", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

        async with _session_factory() as session:
            result = await session.execute(select(Employee).where(Employee.id == employee_id))
            employee = result.scalar_one()
            employee.archived_at = datetime.now(timezone.utc)
            await session.commit()

        async with _session_factory() as session:
            account_result = await session.execute(select(Account).where(Account.id == employee_id))
            hash_before = account_result.scalar_one().password_hash

        async with _client() as client:
            await _login(client)
            response = await client.post(f"/api/admin/employees/{employee_id}/regenerate-password")

            assert response.status_code == 409
            assert response.json()["code"] == "EMPLOYEE_ARCHIVED"

        async with _session_factory() as session:
            account_result = await session.execute(select(Account).where(Account.id == employee_id))
            assert account_result.scalar_one().password_hash == hash_before
    finally:
        await _delete_employee_by_code(code)


async def test_regenerate_password_does_not_touch_profile_fields():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={
                    "employee_code": code,
                    "name": "Profile Untouched",
                    "email": f"{code.lower()}@example.com",
                    "department": "Engineering",
                },
            )
            employee_id = created.json()["id"]

            response = await client.post(f"/api/admin/employees/{employee_id}/regenerate-password")

            assert response.status_code == 200
            body = response.json()
            # AC3: this is a credential operation, not a profile edit --
            # every non-credential field is unchanged.
            assert body["employee_code"] == code
            assert body["name"] == "Profile Untouched"
            assert body["department"] == "Engineering"
    finally:
        await _delete_employee_by_code(code)


async def test_regenerate_password_nonexistent_employee_returns_404():
    async with _client() as client:
        await _login(client)
        response = await client.post(f"/api/admin/employees/{uuid.uuid4()}/regenerate-password")
        assert response.status_code == 404
        assert response.json()["code"] == "EMPLOYEE_NOT_FOUND"


async def test_regenerate_password_employee_session_returns_403():
    code = f"TST-{uuid.uuid4().hex[:8]}"
    try:
        async with _client() as client:
            await _login(client)
            created = await client.post(
                "/api/admin/employees",
                json={"employee_code": code, "name": "Role Gate", "email": f"{code.lower()}@example.com"},
            )
            employee_id = created.json()["id"]

        async with _client() as client:
            await _login(client, email="casey@sails.example.com")
            response = await client.post(f"/api/admin/employees/{employee_id}/regenerate-password")
            assert response.status_code == 403
    finally:
        await _delete_employee_by_code(code)


async def test_regenerate_password_unauthenticated_returns_401():
    async with _client() as client:
        response = await client.post(f"/api/admin/employees/{uuid.uuid4()}/regenerate-password")
        assert response.status_code == 401
