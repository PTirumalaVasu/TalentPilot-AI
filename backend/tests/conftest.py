"""Pytest configuration and fixtures."""
import os
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

# Import models to register them with Base before we use it
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
from app.core.db import Base
from app.core.seeds import run_seeds

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://talentpilot:sails123@localhost:5433/talentpilot")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")


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
    """Create test database engine."""
    test_url = "postgresql+asyncpg://talentpilot:sails123@localhost:5433/talentpilot"

    engine = create_async_engine(test_url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test."""
    async_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # Run seeds
        await run_seeds(session)
        yield session

        # Clean up after test
        await session.rollback()
