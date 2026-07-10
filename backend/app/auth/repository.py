"""Repository layer for the auth module. Only this module's own code may query its tables."""
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
