"""Live-DB tests: seeded Skills must have precise, correct data — not just a
row count — including real, correctly-shaped embeddings computed via the
shared embed_text() utility (Story 3.2 AC2, AC4).

Regression coverage for the integration point never tested before: does
seed_skills()'s call to embed_text() (refactored in Story 2.2 away from an
inline SentenceTransformer instantiation) actually produce a real, non-
degenerate 384-dim vector for each seeded skill, end-to-end, when run
through the real seed pipeline? A stub, caching bug, or silent zero-vector
fallback would pass the existing test_database_schema.py::test_seed_skills_exist
(row-count only) without being caught.

Uses a private engine/session-factory, not the shared app.core.db.engine
singleton — see test_assignments_repository.py's module docstring (Story 3.1)
for why: two module-scoped-loop live-DB test files sharing the same pooled
engine corrupt each other's connections.
"""
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import Skill
from app.core.config import settings
from app.core.embedding import EMBEDDING_DIM
from app.core.seeds import (
    SKILL_COMMUNICATION_ID,
    SKILL_DATA_VIZ_ID,
    SKILL_PYTHON_ID,
    SKILL_SALESFORCE_ID,
    SKILL_SQL_ID,
    run_seeds,
    seed_skills,
)

pytestmark = pytest.mark.asyncio(loop_scope="module")

_engine = create_async_engine(settings.DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)

_EXPECTED_SKILL_NAMES = {
    SKILL_DATA_VIZ_ID: "Data Visualization",
    SKILL_SALESFORCE_ID: "Salesforce Admin",
    SKILL_PYTHON_ID: "Python Programming",
    SKILL_SQL_ID: "SQL & Databases",
    SKILL_COMMUNICATION_ID: "Communication Skills",
}
_DEMO_SKILL_IDS = list(_EXPECTED_SKILL_NAMES.keys())


@asynccontextmanager
async def _seeded_session():
    async with _session_factory() as session:
        await run_seeds(session)
        try:
            yield session
        finally:
            await session.rollback()


async def test_exactly_five_skills_seeded_with_expected_names():
    async with _seeded_session() as session:
        result = await session.execute(select(Skill).where(Skill.id.in_(_DEMO_SKILL_IDS)))
        skills = result.scalars().all()

        assert len(skills) == 5
        actual_names = {skill.id: skill.name for skill in skills}
        assert actual_names == _EXPECTED_SKILL_NAMES


@pytest.mark.parametrize(("skill_id", "expected_name"), list(_EXPECTED_SKILL_NAMES.items()))
async def test_each_skill_has_a_correctly_shaped_nondegenerate_embedding(skill_id, expected_name):
    async with _seeded_session() as session:
        result = await session.execute(select(Skill).where(Skill.id == skill_id))
        skill = result.scalar_one_or_none()
        assert skill is not None, f"{expected_name} not seeded"

        assert skill.name == expected_name
        assert len(skill.embedding) == EMBEDDING_DIM
        # A real sentence-transformer embedding is never all-zero; a
        # zero-vector would indicate a stub/fallback path silently firing
        # instead of the real embed_text() call.
        assert any(component != 0.0 for component in skill.embedding)


async def test_different_skills_have_distinct_embeddings():
    """A single "not all-zero" check would still pass for a degenerate stub
    (a one-hot vector, a hash-based pseudo-embedding, a constant-fill vector
    with one non-zero component). A real sentence-transformer model produces
    measurably different vectors for semantically different input text —
    prove that distinctness directly, rather than only ruling out all-zero."""
    async with _seeded_session() as session:
        result = await session.execute(select(Skill).where(Skill.id.in_(_DEMO_SKILL_IDS)))
        skills = result.scalars().all()
        assert len(skills) == 5

        embeddings = [tuple(skill.embedding) for skill in skills]
        # Every pair of distinct skills must have a distinct embedding —
        # a degenerate/constant-fill/stub path would produce identical (or
        # near-identical) vectors regardless of input text.
        assert len(set(embeddings)) == len(embeddings), "Two different skills produced identical embeddings"


async def test_skill_description_is_genuinely_nullable():
    """AC2 lists description as optional text — the 5 real seeded skills all
    have one, so that path was never exercised end-to-end until now."""
    async with _seeded_session() as session:
        skill = Skill(
            name="Nullable Description Test Skill",
            description=None,
            embedding=[0.1] * EMBEDDING_DIM,
        )
        session.add(skill)
        await session.flush()

        result = await session.execute(select(Skill).where(Skill.id == skill.id))
        fetched = result.scalar_one()
        assert fetched.description is None


async def test_skill_name_uniqueness_enforced_at_db_level():
    async with _seeded_session() as session:
        duplicate = Skill(
            name="Data Visualization",  # matches the already-seeded skill's name
            description="Duplicate name should be rejected",
            embedding=[0.1] * EMBEDDING_DIM,
        )
        session.add(duplicate)

        with pytest.raises(IntegrityError):
            await session.flush()


async def test_seed_skills_is_idempotent_at_the_function_level():
    """test_database_schema.py::test_seed_script_idempotent already covers this
    via the full run_seeds() pipeline; this isolates seed_skills() itself so a
    future change to seed_employees()/create_default_accounts() can't mask a
    seed_skills() regression.

    Follows Story 3.3's test_seed_employees_is_idempotent_at_the_function_level
    pattern exactly (fixed through two rounds of review): explicitly deletes
    the 5 demo skill rows within this test's own uncommitted transaction first
    (rolled back at the end, restoring ambient state), guarded against
    IntegrityError since content_catalog.skill_id/assignments.skill_id both
    FK-reference skills.id with no ondelete=CASCADE (default RESTRICT), and
    asserts the delete's rowcount to distinguish "deleted 5 pre-existing rows"
    from "deleted 0 because none existed" rather than collapsing both paths
    into the same downstream assertions."""
    async with _session_factory() as session:
        try:
            try:
                delete_result = await session.execute(delete(Skill).where(Skill.id.in_(_DEMO_SKILL_IDS)))
                await session.flush()
            except IntegrityError:
                pytest.skip(
                    "Demo skills are referenced by other committed rows "
                    "(content_catalog/assignments) — cannot safely delete "
                    "to exercise the insert path of this idempotency check."
                )

            baseline = await session.execute(select(Skill).where(Skill.id.in_(_DEMO_SKILL_IDS)))
            assert baseline.scalars().all() == []
            assert delete_result.rowcount in (0, 5), (
                f"Expected to delete 0 or 5 pre-existing demo skills, deleted {delete_result.rowcount}"
            )

            await seed_skills(session)
            result1 = await session.execute(select(Skill).where(Skill.id.in_(_DEMO_SKILL_IDS)))
            count1 = len(result1.scalars().all())
            assert count1 == 5

            await seed_skills(session)  # second call must be a true no-op
            result2 = await session.execute(select(Skill).where(Skill.id.in_(_DEMO_SKILL_IDS)))
            count2 = len(result2.scalars().all())

            assert count1 == count2 == 5
        finally:
            await session.rollback()
