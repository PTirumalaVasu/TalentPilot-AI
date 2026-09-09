"""Tests for the skills module's service layer (Story 6.1, AD-11).

`_build_embedding_text` is the "embedding-write helper" this story is
scoped to provide -- Story 6.2 (create) and Story 6.3 (rename) will call
it when they land, so it's unit-tested standalone here rather than through
an endpoint that doesn't exist yet. Mirrors
test_content_ingestion.py::test_build_embedding_text_* exactly, since
skills/'s helper is a deliberate copy of content/'s pattern (AD-11 point 4).

list_all_skills/get_skill_embedding are thin repository wrappers -- live-DB
covered via test_skills_repository.py already exercising the underlying
repository functions; here they're smoke-tested through the Service API
surface cross-module callers (content/) actually depend on.
"""
import uuid
from contextlib import asynccontextmanager

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.seeds import run_seeds
from app.skills.models import Skill
from app.skills.service import _build_embedding_text, get_skill_embedding, list_all_skills

# Per-test @pytest.mark.asyncio(loop_scope="module") below, not a blanket
# module-level pytestmark (unlike test_skills_repository.py) -- this file
# mixes plain sync tests (_build_embedding_text) with async ones sharing
# the module-level `_engine` below; applying the asyncio mark to a sync
# function only warns, but *omitting* loop_scope="module" on the async
# tests is a real bug, not cosmetic: each async test would then run on its
# own function-scoped loop while reusing the same pooled asyncpg
# connection from `_engine`, which is bound to whichever loop first used
# it -- "cannot perform operation: another operation is in progress" on
# every test after the first (reproduced while writing this file).

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


def test_build_embedding_text_truncates_long_input():
    """Must truncate to 1000 chars before embed_text ever sees the string --
    same budget/behavior as content/service.py's _build_embedding_text."""
    long_description = "x" * 5000

    result = _build_embedding_text("Skill Name", long_description)

    assert len(result) == 1000
    assert result.startswith("Skill Name:")


def test_build_embedding_text_handles_none_description():
    result = _build_embedding_text("Just A Name", None)

    assert result == "Just A Name: "


@pytest.mark.asyncio(loop_scope="module")
async def test_service_list_all_skills_returns_seeded_skills():
    async with _seeded_session() as session:
        skills = await list_all_skills(session)

        assert len(skills) >= 5
        assert all(isinstance(s, Skill) for s in skills)


@pytest.mark.asyncio(loop_scope="module")
async def test_service_get_skill_embedding_returns_none_for_nonexistent_skill():
    async with _seeded_session() as session:
        embedding = await get_skill_embedding(session, uuid.uuid4())

        assert embedding is None


@pytest.mark.asyncio(loop_scope="module")
async def test_service_get_skill_embedding_round_trips_through_repository():
    async with _seeded_session() as session:
        skill = Skill(
            name=f"Round Trip Skill {uuid.uuid4().hex[:8]}",
            description="Round trip test",
            embedding=[0.42] * 384,
        )
        session.add(skill)
        await session.flush()

        embedding = await get_skill_embedding(session, skill.id)

        assert embedding is not None
        assert len(embedding) == 384
