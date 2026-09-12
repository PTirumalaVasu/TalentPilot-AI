"""Repository layer for the employees module. Only this module's own code
may query the `employees` table directly (AD-1).

Story 7.2 (create, FR-24) adds the first real queries here.
`create_employee_with_account` is a deliberate, AR-24-sanctioned exception
to strict module ownership: it also triggers a write to `accounts` (owned by
`auth/`) -- this is the one designed cross-module write this epic's
architecture creates, not a precedent to casually extend. As of the Story
7.2 code review, the actual `Account` row construction is delegated to
`auth.repository.create_account` rather than inlined here, so `auth/`
remains the single place that knows `Account`'s required column shape.
"""
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import repository as auth_repository
from app.employees.models import Employee


async def list_all_employees(db: AsyncSession) -> list[Employee]:
    """Full roster read (Story 7.3, FR-25) -- every Employee, active and
    archived alike. No `archived_at` filter: the frontend's "show archived"
    toggle decides what to display, not this query (mirrors
    skills/repository.py::list_all_skills's shape -- AD-1, `employees/` is
    the sole owner of `employees` table reads). Ordered by `employee_code`
    for deterministic client-side pagination -- unlike list_all_skills
    (unordered, backs a grid), this backs a paginated table."""
    result = await db.execute(select(Employee).order_by(Employee.employee_code))
    return list(result.scalars().all())


async def get_employee_by_code(db: AsyncSession, employee_code: str) -> Employee | None:
    """Exact-match lookup by employee_code (Story 7.2 AC2's duplicate check).

    No `archived_at` filter -- an archived Employee's employee_code still
    collides (per FR-24/AC2: "active or archived"). Case-sensitive, matching
    the plain DB UNIQUE constraint (`uq_employees_employee_code`, migration
    011) -- unlike email, the AC does not ask for case-insensitive
    employee_code matching (Story 7.2 Scope Note 5)."""
    result = await db.execute(select(Employee).where(Employee.employee_code == employee_code))
    return result.scalar_one_or_none()


async def get_employee_by_email_ci(db: AsyncSession, email: str) -> Employee | None:
    """Case-insensitive lookup by email (Story 7.2 AC2's duplicate check,
    "matching FR-20's Skill-name dedup pattern"). Mirrors
    skills/repository.py::get_skill_by_name_ci's exact shape. No
    `archived_at` filter -- an archived Employee's email still collides."""
    result = await db.execute(select(Employee).where(func.lower(Employee.email) == func.lower(email)))
    return result.scalar_one_or_none()


async def get_employee_by_code_or_email_ci(
    db: AsyncSession, employee_code: str, email: str
) -> tuple[Employee | None, Employee | None]:
    """Combined pre-check for Story 7.2 AC2: one query instead of two
    sequential round-trips (Story 7.2 code review). Returns
    `(matched_by_code, matched_by_email)` -- either may be `None`, and both
    may point at the same row if a single existing Employee happens to
    collide on both fields at once. No `archived_at` filter, same reasoning
    as the two single-column lookups above."""
    result = await db.execute(
        select(Employee).where(
            or_(Employee.employee_code == employee_code, func.lower(Employee.email) == func.lower(email))
        )
    )
    rows = result.scalars().all()
    matched_by_code = next((row for row in rows if row.employee_code == employee_code), None)
    matched_by_email = next((row for row in rows if row.email.lower() == email.lower()), None)
    return matched_by_code, matched_by_email


async def get_employee_by_id(db: AsyncSession, employee_id: UUID) -> Employee | None:
    """Plain PK lookup for Story 7.4 (edit, FR-26). No `archived_at` filter --
    an archived Employee can still be edited (nothing in the AC restricts
    editing to active-only, unlike Story 7.6's regenerate-password).

    `assignments/repository.py::get_employee_by_id` already exists with the
    identical signature/behavior (used by `/api/auth/me`) -- this is a
    deliberate, AD-1-consistent duplication (each module owns its own reads
    of `employees`), not an oversight."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    return result.scalar_one_or_none()


async def get_employee_by_email_ci_excluding_id(
    db: AsyncSession, email: str, exclude_id: UUID
) -> Employee | None:
    """Same case-insensitive lookup as get_employee_by_email_ci, but excludes
    one Employee by id (Story 7.4 AC2) -- so re-saving an edit with the
    Employee's own unchanged email never spuriously conflicts with itself."""
    result = await db.execute(
        select(Employee).where(func.lower(Employee.email) == func.lower(email), Employee.id != exclude_id)
    )
    return result.scalar_one_or_none()


async def update_employee(db: AsyncSession, employee: Employee, data: dict) -> Employee:
    """Applies an in-place field update to an existing Employee (Story 7.4,
    FR-26). `updated_at` bumps automatically via the model's existing
    `onupdate=func.now()` (Story 7.1) -- no explicit set needed here."""
    for field, value in data.items():
        setattr(employee, field, value)
    await db.flush()
    await db.refresh(employee)
    return employee


async def create_employee_with_account(
    db: AsyncSession, employee_data: dict, password_hash: str
) -> Employee:
    """Create a new Employee and its corresponding Account row in one
    transaction (Story 7.2 AC1, AR-24). `Account.id` is set equal to the new
    Employee's generated `id` -- the identity link `accounts_id_fkey`
    (migration 011) enforces at the DB level. Both writes happen in this one
    function so no caller can flush/commit between them and leave either
    row orphaned.

    This is a deliberate exception to AD-1 (employees/ triggering a write to
    auth/'s owned `accounts` table): Story 7.1 established that Account.id
    must always equal the corresponding Employee.id, and employees/ is the
    only module that knows when a new Employee -- and therefore a new
    required Account -- is being created. Routing this through
    auth/service.py instead would be backwards, since auth/ doesn't own the
    Employee-creation workflow or its validation rules. The actual Account
    row construction itself is delegated to auth_repository.create_account
    (Story 7.2 code review) rather than inlined here, keeping Account's
    column shape known in exactly one place.
    """
    employee = Employee(**employee_data)
    db.add(employee)
    await db.flush()
    await db.refresh(employee)

    await auth_repository.create_account(
        db, id=employee.id, email=employee.email, password_hash=password_hash, role="EMPLOYEE"
    )

    return employee
