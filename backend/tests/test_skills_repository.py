"""Tests for the skills module's repository layer (Story 6.1, AD-11).

Uses a private engine/session -- the established Story 3.1/2.4 pattern
(see test_assignments_repository.py's module docstring) -- rather than
conftest.py's shared db_session/test_engine fixture, a known unfixed
landmine whose teardown runs Base.metadata.drop_all() against the real
dev database (deferred-work.md). Test-created rows are only flush()'d, so
a plain rollback() in the finally block is sufficient cleanup.

list_all_skills and get_skill_embedding relocate here from
content/repository.py (Story 2.3 scope note 2 / Story 2.4), now that
skills/ is the table's real owning module -- see test_content_ingestion.py
and test_content_matching.py's own history for the tests these replace.
"""
import uuid
from contextlib import asynccontextmanager

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.seeds import run_seeds
from app.skills.models import Skill
from app.skills.repository import get_skill_embedding, list_all_skills

pytestmark = pytest.mark.asyncio(loop_scope="module")

_engine = create_async_engine(settings.DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


@asynccontextmanager
async def _seeded_session():
    async with _session_factory() as session:
        await run_seeds(session)
        try:
            yield session
        finally:
            await session.rollback()


async def _make_skill(session, *, name: str | None = None, embedding: list[float] | None = None) -> Skill:
    skill = Skill(
        name=name or f"Test Skill {uuid.uuid4().hex[:8]}",
        description="Test skill for skills repository",
        embedding=embedding or [0.1] * 384,
    )
    session.add(skill)
    await session.flush()
    return skill


async def test_list_all_skills_returns_seeded_skills():
    async with _seeded_session() as session:
        skills = await list_all_skills(session)

        assert len(skills) >= 5
        assert all(isinstance(s, Skill) for s in skills)


async def test_list_all_skills_includes_a_freshly_created_skill():
    async with _seeded_session() as session:
        created = await _make_skill(session)

        skills = await list_all_skills(session)

        assert any(s.id == created.id for s in skills)


async def test_get_skill_embedding_returns_none_for_nonexistent_skill():
    async with _seeded_session() as session:
        embedding = await get_skill_embedding(session, uuid.uuid4())

        assert embedding is None


async def test_get_skill_embedding_returns_the_stored_vector_as_a_plain_list():
    async with _seeded_session() as session:
        expected = [0.25] * 384
        skill = await _make_skill(session, embedding=expected)

        embedding = await get_skill_embedding(session, skill.id)

        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(component, float) for component in embedding)


async def test_new_skill_defaults_ever_assigned_to_false():
    """AD-11's permanent lock starts open -- a freshly-created Skill (that
    never specifies ever_assigned) must default to False, not NULL/True,
    both at the ORM level and once round-tripped through Postgres."""
    async with _seeded_session() as session:
        skill = await _make_skill(session)

        await session.refresh(skill)

        assert skill.ever_assigned is False

