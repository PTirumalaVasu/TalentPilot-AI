"""Repository layer for the auth module. Only this module's own code may query its tables."""
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
