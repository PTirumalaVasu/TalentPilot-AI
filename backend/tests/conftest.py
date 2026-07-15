"""Pytest configuration and fixtures."""
import os
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Import models to register them with SQLAlchemy's mapper registry before we use it
# noqa: F401 - imported for side-effects
from app.auth.models import Account  # noqa: F401
from app.assignments.models import (  # noqa: F401
    Employee,
    Skill,
    ContentCatalog,
    Assignment,
    SkillProgress,
    AssignmentOverride,
)
from app.core.seeds import run_seeds

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://talentpilot:sails123@localhost:5433/talentpilot")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")

# app.core.db builds one module-level engine/pool at import time. asyncpg
# connections are bound to the event loop that first used them, but test
# modules run on a mix of function- and module-scoped loops (several set
# `loop_scope="module"` deliberately -- see their docstrings). A pooled
# connection handed out on one loop and reused on another raises
# "cannot perform operation: another operation is in progress". NullPool
# opens a fresh connection per checkout and never hands a connection across
# a request boundary, so no connection can outlive the loop that made it.
import app.core.db as _app_db
from app.core.config import settings as _settings

_app_db.engine = create_async_engine(_settings.DATABASE_URL, poolclass=NullPool)
_app_db.async_session_factory = async_sessionmaker(_app_db.engine, expire_on_commit=False)

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

@pytest.fixture
async def test_engine():
    """Create test database engine, connected to the already-migrated database.

    Does NOT run Base.metadata.create_all()/drop_all() -- the schema is
    already owned and provisioned by Alembic (Story 1.7). This fixture
    previously ran create_all()/drop_all() against the REAL
    settings.DATABASE_URL (same DB as Docker Compose's dev Postgres), which
    wiped EVERY table in the app on every single test's teardown once the
    fixture's scope moved from session to function. See deferred-work.md
    ("code review of 2-1-content-catalog-data-model-and-schema") for the
    full diagnosis. Test isolation is provided entirely by db_session's
    rollback below -- callers must use flush(), not commit(), to keep
    changes rollback-able."""
    test_url = "postgresql+asyncpg://talentpilot:sails123@localhost:5433/talentpilot"

    engine = create_async_engine(test_url, echo=False)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test.

    Tests must use `await db_session.flush()`, not `.commit()`, for any rows
    they add -- the rollback below is what keeps them from persisting into
    the shared dev database."""
    async_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # Run seeds
        await run_seeds(session)
        yield session

        # Clean up after test
        await session.rollback()
