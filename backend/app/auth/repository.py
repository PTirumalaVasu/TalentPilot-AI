"""Repository layer for the auth module. Only this module's own code may query its tables."""

# Mock credential store for MVP (PRD Open Question 9) -- hardcoded, not DB-backed.
# The real `accounts` table (Story 1.7) and `employees` seed (Story 3.3) don't
# exist yet, and this story's own AC calls for a hardcoded mock store anyway.
_MOCK_ACCOUNTS: dict[str, dict] = {
    "rita@sails.example.com": {"password": "demo123", "role": "HR_ADMIN", "user_id": "rita"},
    "casey@sails.example.com": {"password": "demo123", "role": "EMPLOYEE", "user_id": "casey"},
    "morgan@sails.example.com": {"password": "demo123", "role": "EMPLOYEE", "user_id": "morgan"},
    "jordan@sails.example.com": {"password": "demo123", "role": "EMPLOYEE", "user_id": "jordan"},
    "sam@sails.example.com": {"password": "demo123", "role": "EMPLOYEE", "user_id": "sam"},
}


def find_account(email: str) -> dict | None:
    return _MOCK_ACCOUNTS.get(email.strip().lower())
