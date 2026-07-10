"""Live-DB tests for core/db.py::get_db (Story 3.1 re-review fix).

Confirms get_db() actually commits on success and rolls back on exception —
the gap found during Story 3.1's re-review: it previously never committed at
all, so every write made through it would silently vanish once a route
depended on it. get_db() wasn't used by any route/dependency at the time of
this fix, so this is new coverage, not a regression test for existing usage.

get_db() is hardwired to app.core.db.engine (the shared singleton) — that's
the whole point of testing it, so unlike other live-DB test files in this
suite this one can't sidestep the shared engine with a private one. Instead,
each test disposes the shared pool immediately before its first use, forcing
a fresh connection bound to *this* module's own asyncio loop — otherwise
running alongside another module-scoped-loop test file that also touches
app.core.db.engine (test_database_schema.py) corrupts the connection
mid-test (confirmed empirically: passes in isolation, fails in the full
suite without this). See deferred-work.md's Story 3.1 entries for the full
diagnosis of this class of bug.
"""
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import Employee
from app.core.config import settings
from app.core.db import engine as shared_engine
from app.core.db import get_db
from app.core.seed_ids import RITA_ID

pytestmark = pytest.mark.asyncio(loop_scope="module")

_engine = create_async_engine(settings.DATABASE_URL)
_verify_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def test_get_db_commits_on_successful_completion():
    await shared_engine.dispose()
    unique_email = f"commit-test-{uuid.uuid4().hex[:8]}@example.com"
    new_id = uuid.uuid4()

    gen = get_db()
    session = await gen.__anext__()
    session.add(Employee(id=new_id, name="Commit Test", email=unique_email, role="EMPLOYEE"))
    await session.flush()

    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()  # drives the code after `yield` -> should commit

    try:
        # Verify via a completely separate session/connection that the row
        # actually persisted, not just that no exception was raised.
        async with _verify_session_factory() as verify_session:
            result = await verify_session.execute(select(Employee).where(Employee.id == new_id))
            assert result.scalar_one_or_none() is not None
    finally:
        # get_db() commits for real, so clean up explicitly rather than
        # relying on a rollback that would no-op against already-committed data.
        async with _verify_session_factory() as cleanup_session:
            emp = await cleanup_session.get(Employee, new_id)
            if emp is not None:
                await cleanup_session.delete(emp)
                await cleanup_session.commit()


async def test_get_db_rolls_back_on_exception():
    await shared_engine.dispose()
    unique_email = f"rollback-test-{uuid.uuid4().hex[:8]}@example.com"
    new_id = uuid.uuid4()

    gen = get_db()
    session = await gen.__anext__()
    session.add(Employee(id=new_id, name="Rollback Test", email=unique_email, role="EMPLOYEE"))
    await session.flush()

    with pytest.raises(RuntimeError):
        await gen.athrow(RuntimeError("simulated route handler failure"))

    async with _verify_session_factory() as verify_session:
        result = await verify_session.execute(select(Employee).where(Employee.id == new_id))
        assert result.scalar_one_or_none() is None
