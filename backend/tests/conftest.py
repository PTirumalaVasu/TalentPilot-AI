import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://talentpilot:talentpilot@localhost:5432/talentpilot")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")

import pytest

from app.auth import service as auth_service


@pytest.fixture(autouse=True)
def _clear_revoked_tokens():
    """_revoked_tokens (Story 1.5) is a module-level global that persists for
    the whole test process. Without this, one test's logout can "pre-revoke"
    another test's freshly-minted token whenever create_access_token's
    whole-second-precision iat causes two tokens to collide byte-for-byte."""
    auth_service._revoked_tokens.clear()
    yield
    auth_service._revoked_tokens.clear()
