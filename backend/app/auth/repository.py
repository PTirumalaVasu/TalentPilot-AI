"""Repository layer for the auth module. Only this module's own code may query its tables."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Account
from app.core.seed_ids import CASEY_ID, JORDAN_ID, MORGAN_ID, RITA_ID, SAM_ID

# Mock credential store for MVP (PRD Open Question 9) -- hardcoded, not DB-backed.
# user_id values are the same UUIDs as the real seeded Employee rows
# (core/seeds.py), not arbitrary names -- Story 3.1's assignments code treats
# CurrentUser.user_id as a real Employee UUID (uuid.UUID(current_user.user_id)),
# so a login's JWT user_id must actually resolve to a real employee.
_MOCK_ACCOUNTS: dict[str, dict] = {
    "rita@sails.example.com": {"password": "demo123", "role": "HR_ADMIN", "user_id": str(RITA_ID)},
    "casey@sails.example.com": {"password": "demo123", "role": "EMPLOYEE", "user_id": str(CASEY_ID)},
    "morgan@sails.example.com": {"password": "demo123", "role": "EMPLOYEE", "user_id": str(MORGAN_ID)},
    "jordan@sails.example.com": {"password": "demo123", "role": "EMPLOYEE", "user_id": str(JORDAN_ID)},
    "sam@sails.example.com": {"password": "demo123", "role": "EMPLOYEE", "user_id": str(SAM_ID)},
}


def find_account(email: str) -> dict | None:
    return _MOCK_ACCOUNTS.get(email.strip().lower())


async def get_account_by_email_ci(db: AsyncSession, email: str) -> Account | None:
    """Case-insensitive lookup by email. Used by employees/service.py's
    IntegrityError backstop (Story 7.2 code review) to distinguish a
    conflict on the `accounts` side from one on `employees` after a
    rollback -- the two tables' email values aren't guaranteed to always
    match once a future story allows editing an Employee's email without
    also updating its paired Account (FR-26's own `[ASSUMPTION]` flags this
    exact drift as possible)."""
    result = await db.execute(select(Account).where(func.lower(Account.email) == func.lower(email)))
    return result.scalar_one_or_none()


async def get_account_by_email_ci_excluding_id(db: AsyncSession, email: str, exclude_id: UUID) -> Account | None:
    """Same case-insensitive lookup as get_account_by_email_ci, but excludes
    one Account by id -- used by employees/service.py's Story 7.4 edit-time
    IntegrityError backstop so an Employee's own Account never spuriously
    conflicts with itself when its email is unchanged."""
    result = await db.execute(
        select(Account).where(func.lower(Account.email) == func.lower(email), Account.id != exclude_id)
    )
    return result.scalar_one_or_none()


async def update_account_email(db: AsyncSession, *, id: UUID, email: str) -> None:
    """Updates an existing Account's email (Story 7.4, FR-26) -- the sole
    write path for changing accounts.email, following create_account's
    established centralization pattern (Story 7.2 code review) so Account's
    column shape stays known in exactly one place. Called from
    employees/service.py when an Employee's email is edited, to keep
    Employee.email and Account.email from drifting apart (Story 7.2 code
    review flagged this exact future need by name)."""
    account = await db.get(Account, id)
    account.email = email
    await db.flush()


async def get_account_by_id(db: AsyncSession, id: UUID) -> Account | None:
    """Plain PK lookup (Story 7.5, FR-27/AR-25) -- used by
    auth/service.py::get_current_user to check whether the session's
    identity has since been archived or deleted (AC4)."""
    return await db.get(Account, id)


async def update_account_archived_at(db: AsyncSession, *, id: UUID, archived_at: datetime) -> None:
    """Mirrors employees.archived_at onto the paired Account row (Story 7.5,
    AR-25) -- called from employees/service.py's archive path in the same
    transaction as employees.archived_at, so get_current_user can reject an
    archived identity's still-valid session without importing
    app.employees.models.Employee (which would create a circular import,
    since employees/service.py already imports this module).

    Guards for `None` (code review, 2026-09-12) -- mirrors delete_account's
    guard just below; AR-24's 1:1 invariant makes a missing Account
    unreachable in normal operation, but this is the same class of bug
    Story 7.4's review flagged as "deferred but becomes reachable the
    moment this story ships" for update_account_email, and the guard is
    free."""
    account = await db.get(Account, id)
    if account is None:
        return
    account.archived_at = archived_at
    await db.flush()


async def delete_account(db: AsyncSession, *, id: UUID) -> None:
    """Physically removes an Account row (Story 7.5, FR-27 AC1's hard-delete
    path) -- called from employees/service.py before hard-deleting the
    paired Employee row (AR-24: Account.id == Employee.id), since Account
    has a FK to employees.id with no cascade. Guards for `None` (unlike the
    pre-existing gap on update_account_email, deferred in Story 7.4 as
    "currently unreachable" -- this story's hard-delete path makes a missing
    Account newly reachable, so this must not repeat that gap)."""
    account = await db.get(Account, id)
    if account is None:
        return
    await db.delete(account)
    await db.flush()


async def update_account_password_hash(db: AsyncSession, *, id: UUID, password_hash: str) -> None:
    """Updates an existing Account's password_hash (Story 7.6, FR-28) -- the
    sole write path for changing accounts.password_hash after creation,
    following update_account_email's/update_account_archived_at's established
    centralization pattern so Account's column shape stays known in exactly
    one place. Called from employees/service.py's regenerate-password flow.

    Guards for `None` (mirrors update_account_archived_at/delete_account's
    established pattern, Story 7.5 code review) -- AR-24's 1:1 invariant
    makes a missing Account unreachable in normal operation, but the guard is
    free."""
    account = await db.get(Account, id)
    if account is None:
        return
    account.password_hash = password_hash
    await db.flush()


async def create_account(db: AsyncSession, *, id: UUID, email: str, password_hash: str, role: str) -> Account:
    """Create a new Account row. The sole write path into `accounts` from
    another module (Story 7.2 code review, formalizing what
    employees/repository.py::create_employee_with_account previously
    constructed inline) -- centralizing Account's column shape here means a
    future change to its required columns only needs updating in one place,
    not wherever a cross-module caller happens to construct one."""
    account = Account(id=id, email=email, password_hash=password_hash, role=role)
    db.add(account)
    await db.flush()
    return account
