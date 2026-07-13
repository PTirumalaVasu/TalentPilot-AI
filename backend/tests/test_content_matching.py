"""Live-DB tests for content matching (Story 2.4, AC1-AC7).

Uses a private engine/session -- the established Story 3.1 pattern (see
test_assignments_repository.py) -- rather than conftest.py's shared
db_session/test_engine fixture, which is a known, still-unfixed landmine:
its teardown runs Base.metadata.drop_all() against the real dev database,
wiping every table app-wide after every test that uses it (deferred-work.md).
Nothing here ever commits its own test rows beyond run_seeds' internal
commit (idempotent, pre-existing seed data) -- test-created Skills/Content
are only flush()'d, so a plain rollback() in the finally block is sufficient
cleanup with zero risk to the shared schema/seed data.
"""
import math
import uuid
from contextlib import asynccontextmanager

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import ContentCatalog, Skill
from app.content.repository import find_best_matching_content, get_skill_embedding
from app.content.service import match_content_for_skill, reembed_content_for_skill
from app.core.config import settings
from app.core.embedding import embed_text
from app.core.seeds import run_seeds

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


def _unit_vector(index: int) -> list[float]:
    """A 384-dim unit vector with 1.0 at `index`, 0.0 elsewhere."""
    vector = [0.0] * 384
    vector[index] = 1.0
    return vector


def _vector_at_similarity(similarity: float) -> list[float]:
    """A 384-dim unit vector whose cosine similarity to _unit_vector(0) is
    `similarity`, in double precision. pgvector stores components as
    float32, so real query results carry ~1e-7 relative noise -- callers
    should not assert bit-exact equality at a boundary value, only a clear
    margin either side of it (see the just-above/just-below threshold tests)."""
    orthogonal = math.sqrt(max(0.0, 1.0 - similarity**2))
    vector = [0.0] * 384
    vector[0] = similarity
    vector[1] = orthogonal
    return vector


async def _make_skill(session, *, embedding: list[float]) -> Skill:
    skill = Skill(
        name=f"Test Skill {uuid.uuid4().hex[:8]}",
        description="Test skill for content matching",
        embedding=embedding,
    )
    session.add(skill)
    await session.flush()
    return skill


async def _make_content(
    session,
    *,
    skill_id,
    embedding: list[float],
    content_id=None,
    title: str = "Test Content",
) -> ContentCatalog:
    content = ContentCatalog(
        id=content_id or uuid.uuid4(),
        skill_id=skill_id,
        title=title,
        description="Test content description",
        type="VIDEO",
        url="https://example.com/video",
        embedding=embedding,
        source="MANUAL",
    )
    session.add(content)
    await session.flush()
    return content


# --- AC1: pre-filter ---------------------------------------------------------


async def test_prefilter_never_returns_content_from_a_different_skill():
    async with _seeded_session() as session:
        skill_a = await _make_skill(session, embedding=_unit_vector(0))
        skill_b = await _make_skill(session, embedding=_unit_vector(1))

        content_a = await _make_content(
            session, skill_id=skill_a.id, embedding=_vector_at_similarity(0.8), title="A's own content"
        )
        # Deliberately more similar to Skill A's embedding than A's own
        # content is, but tagged to Skill B -- must never surface for A.
        await _make_content(
            session, skill_id=skill_b.id, embedding=_vector_at_similarity(0.99), title="B's content, closer to A"
        )

        result = await find_best_matching_content(session, skill_a.id, skill_a.embedding)

        assert result is not None
        assert result.id == content_a.id


# --- AC2 / AC4: rank + top-1 --------------------------------------------------


async def test_ranks_by_similarity_and_returns_only_the_top_match():
    async with _seeded_session() as session:
        skill = await _make_skill(session, embedding=_unit_vector(0))

        await _make_content(session, skill_id=skill.id, embedding=_vector_at_similarity(0.75), title="lowest")
        await _make_content(session, skill_id=skill.id, embedding=_vector_at_similarity(0.85), title="middle")
        best = await _make_content(session, skill_id=skill.id, embedding=_vector_at_similarity(0.95), title="best")

        result = await find_best_matching_content(session, skill.id, skill.embedding)

        assert result is not None
        assert result.id == best.id


# --- AC3: threshold ------------------------------------------------------------
# Boundary values below are relative to SIMILARITY_THRESHOLD (repository.py),
# not hardcoded independent of it -- recalibrated 2026-07-12 when the
# threshold itself moved from 0.7 to 0.4 (measured against real embeddings,
# see repository.py's inline comment). The old 0.4/0.71/0.69 values were
# clear-margin/just-above/just-below relative to 0.7 and silently started
# asserting the wrong thing once the threshold changed underneath them --
# caught via a full test-suite run, not by the threshold change itself.


async def test_returns_none_when_only_candidate_is_below_threshold():
    async with _seeded_session() as session:
        skill = await _make_skill(session, embedding=_unit_vector(0))
        await _make_content(session, skill_id=skill.id, embedding=_vector_at_similarity(0.1))

        result = await find_best_matching_content(session, skill.id, skill.embedding)

        assert result is None


async def test_includes_content_just_above_threshold():
    async with _seeded_session() as session:
        skill = await _make_skill(session, embedding=_unit_vector(0))
        content = await _make_content(session, skill_id=skill.id, embedding=_vector_at_similarity(0.41))

        result = await find_best_matching_content(session, skill.id, skill.embedding)

        assert result is not None
        assert result.id == content.id


async def test_excludes_content_just_below_threshold():
    async with _seeded_session() as session:
        skill = await _make_skill(session, embedding=_unit_vector(0))
        await _make_content(session, skill_id=skill.id, embedding=_vector_at_similarity(0.39))

        result = await find_best_matching_content(session, skill.id, skill.embedding)

        assert result is None


# --- AC5: null-result paths ----------------------------------------------------


async def test_returns_none_for_skill_with_zero_content():
    async with _seeded_session() as session:
        skill = await _make_skill(session, embedding=_unit_vector(0))

        result = await find_best_matching_content(session, skill.id, skill.embedding)

        assert result is None


async def test_service_returns_none_when_no_content_clears_threshold():
    async with _seeded_session() as session:
        skill = await _make_skill(session, embedding=_unit_vector(0))
        await _make_content(session, skill_id=skill.id, embedding=_vector_at_similarity(0.2))

        result = await match_content_for_skill(session, skill.id)

        assert result is None


# --- AC7: nonexistent skill -----------------------------------------------------


async def test_get_skill_embedding_returns_none_for_nonexistent_skill():
    async with _seeded_session() as session:
        embedding = await get_skill_embedding(session, uuid.uuid4())

        assert embedding is None


async def test_service_returns_none_for_nonexistent_skill():
    async with _seeded_session() as session:
        result = await match_content_for_skill(session, uuid.uuid4())

        assert result is None


# --- AC6: determinism ------------------------------------------------------------


async def test_matching_is_deterministic_across_repeated_calls():
    async with _seeded_session() as session:
        skill = await _make_skill(session, embedding=_unit_vector(0))
        best = await _make_content(session, skill_id=skill.id, embedding=_vector_at_similarity(0.9))
        await _make_content(session, skill_id=skill.id, embedding=_vector_at_similarity(0.75))

        first = await find_best_matching_content(session, skill.id, skill.embedding)
        second = await find_best_matching_content(session, skill.id, skill.embedding)

        assert first is not None and first.id == best.id
        assert second is not None and second.id == best.id


async def test_exact_tie_breaks_deterministically_by_content_id():
    async with _seeded_session() as session:
        skill = await _make_skill(session, embedding=_unit_vector(0))
        tied_embedding = _vector_at_similarity(0.9)

        lower_id = uuid.UUID(int=1)
        higher_id = uuid.UUID(int=2)
        # Insert the higher-id row first, so a pass here proves the winner
        # is chosen by id value, not by insertion/fetch order.
        await _make_content(
            session, skill_id=skill.id, embedding=tied_embedding, content_id=higher_id, title="higher id"
        )
        lower = await _make_content(
            session, skill_id=skill.id, embedding=tied_embedding, content_id=lower_id, title="lower id"
        )

        first = await find_best_matching_content(session, skill.id, skill.embedding)
        second = await find_best_matching_content(session, skill.id, skill.embedding)

        assert first is not None and first.id == lower.id == lower_id
        assert second is not None and second.id == lower_id


# --- Re-embed-and-retry fallback (no video meets threshold -> re-embed -> retry) ---


async def test_reembeds_stale_content_and_finds_a_match_on_retry():
    """A Content row whose stored embedding is stale/wrong (e.g. computed
    under an older text-building convention) should fail the first
    filter-then-rank pass, get re-embedded from its current title/
    description, and match on the retry -- all without any YouTube call."""
    async with _seeded_session() as session:
        skill_embedding = embed_text("Data Visualization: creating charts, graphs, and dashboards")
        skill = await _make_skill(session, embedding=skill_embedding)

        content = await _make_content(
            session,
            skill_id=skill.id,
            # Deliberately unrelated/stale stored embedding -- if this were
            # used as-is, it would fall below SIMILARITY_THRESHOLD.
            embedding=_vector_at_similarity(0.1),
            title="Excel Charting Tutorial",
        )
        content.description = "how to build charts and graphs in Excel"
        await session.flush()

        result = await match_content_for_skill(session, skill.id)

        assert result is not None
        assert result.id == content.id


async def test_reembed_content_for_skill_returns_zero_for_skill_with_no_content():
    async with _seeded_session() as session:
        skill = await _make_skill(session, embedding=_unit_vector(0))

        count = await reembed_content_for_skill(session, skill.id)

        assert count == 0


async def test_service_still_returns_none_when_reembed_does_not_rescue_a_match():
    """The retry is a best-effort rescue, not a guarantee -- genuinely
    unrelated content stays below threshold even after re-embedding from
    its real (also unrelated) title/description."""
    async with _seeded_session() as session:
        skill_embedding = embed_text("Data Visualization: creating charts, graphs, and dashboards")
        skill = await _make_skill(session, embedding=skill_embedding)
        content = await _make_content(
            session,
            skill_id=skill.id,
            embedding=_vector_at_similarity(0.1),
            title="How to boil pasta al dente",
        )
        content.description = "a simple cooking guide"
        await session.flush()

        result = await match_content_for_skill(session, skill.id)

        assert result is None


# --- Real-embedding integration check ---------------------------------------------


async def test_ranks_correctly_with_real_embed_text_output():
    """Not a threshold test (real model scores aren't controllable to an
    exact cut point) -- verifies the SQL-level cosine query correctly
    prefers a related result over an unrelated one using real
    sentence-transformers output, not just hand-crafted vectors."""
    async with _seeded_session() as session:
        skill_embedding = embed_text("Data Visualization: creating charts, graphs, and dashboards")
        skill = await _make_skill(session, embedding=skill_embedding)

        related = await _make_content(
            session,
            skill_id=skill.id,
            embedding=embed_text("Excel Charting Tutorial: how to build charts and graphs in Excel"),
            title="related",
        )
        await _make_content(
            session,
            skill_id=skill.id,
            embedding=embed_text("How to boil pasta al dente: a simple cooking guide"),
            title="unrelated",
        )

        # threshold=0.0 so both candidates clear it -- this test is about
        # ranking correctness, not the 0.7 cutoff.
        result = await find_best_matching_content(session, skill.id, skill_embedding, threshold=0.0)

        assert result is not None
        assert result.id == related.id
