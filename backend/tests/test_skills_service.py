"""Tests for the skills module's service layer (Story 6.1, AD-11; Story 6.2, FR-20).

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

create_skill_service (Story 6.2) tests below cover the service-layer
contract directly (embedding computed, ever_assigned defaults False,
case-insensitive duplicate -> 409 with existing id/name, EMPLOYEE -> 403).
Router-level HTTP assertions (status codes, response shape over the wire)
live in test_skills_router.py instead of being duplicated here.
"""
import uuid
from contextlib import asynccontextmanager
from unittest import mock

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.schemas import CurrentUser, Role
from app.core.config import settings
from app.core.errors import AppException
from app.core.seeds import run_seeds
from app.skills import repository as skills_repository
from app.skills.models import Skill
from app.skills.schemas import CreateSkillRequest
from app.skills.service import _build_embedding_text, create_skill_service, get_skill_embedding, list_all_skills

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


_HR_ADMIN = CurrentUser(role=Role.HR_ADMIN, user_id=str(uuid.uuid4()))
_EMPLOYEE = CurrentUser(role=Role.EMPLOYEE, user_id=str(uuid.uuid4()))


@pytest.mark.asyncio(loop_scope="module")
async def test_create_skill_service_computes_embedding_and_defaults_ever_assigned_false():
    name = f"Create Skill Test {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            response = await create_skill_service(
                session,
                current_user=_HR_ADMIN,
                request=CreateSkillRequest(name=name, description="A brand new skill"),
            )

            assert response.name == name
            assert response.description == "A brand new skill"
            assert response.ever_assigned is False

            embedding = await get_skill_embedding(session, response.id)
            assert embedding is not None
            assert len(embedding) == 384
        finally:
            await session.execute(delete(Skill).where(Skill.name == name))
            await session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_create_skill_service_rejects_case_insensitive_duplicate():
    name = f"Duplicate Skill Test {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            original = await create_skill_service(
                session, current_user=_HR_ADMIN, request=CreateSkillRequest(name=name)
            )

            with pytest.raises(AppException) as exc_info:
                await create_skill_service(
                    session, current_user=_HR_ADMIN, request=CreateSkillRequest(name=name.upper())
                )

            assert exc_info.value.status_code == 409
            assert exc_info.value.error_code == "SKILL_NAME_CONFLICT"
            assert exc_info.value.extra["existing_skill"]["id"] == str(original.id)
            assert exc_info.value.extra["existing_skill"]["name"] == name

            all_skills = await list_all_skills(session)
            matching = [s for s in all_skills if s.name.lower() == name.lower()]
            assert len(matching) == 1
        finally:
            await session.execute(delete(Skill).where(Skill.name == name))
            await session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_create_skill_service_converts_integrity_error_to_409_on_exact_name_race():
    """Simulates the race migration 006's DB-level unique index guards
    against: get_skill_by_name_ci returns None (as if the pre-check ran
    just before a concurrent request for the identical name committed),
    so the insert proceeds and hits the real DB constraint. Verifies the
    resulting IntegrityError is caught and converted to the same clean
    409 -- not a raw, unhandled 500."""
    # Two independent sessions, matching how get_db actually behaves in
    # production (a fresh session per request) -- the "concurrent" request
    # commits on its own session *before* our session's insert attempt, the
    # same order a real DB-level UniqueViolation requires (the other
    # transaction must have already committed for our insert to conflict
    # with it; if it had merely flushed-and-not-committed, Postgres would
    # block our insert until that other transaction resolves, not fail it
    # immediately). Two calls sharing one session would rollback() the
    # *first* call's still-uncommitted insert too when handling the
    # second's IntegrityError -- an artifact of sharing a transaction, not
    # a real race; caught while writing this test.
    name = f"Race Test {uuid.uuid4().hex[:8]}"
    try:
        async with _session_factory() as concurrent_session:
            await run_seeds(concurrent_session)
            original = await create_skill_service(
                concurrent_session, current_user=_HR_ADMIN, request=CreateSkillRequest(name=name)
            )
            await concurrent_session.commit()

        async with _session_factory() as session:
            real_get_skill_by_name_ci = skills_repository.get_skill_by_name_ci
            call_count = 0

            async def _pre_check_misses_once(db, lookup_name):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return None
                return await real_get_skill_by_name_ci(db, lookup_name)

            with mock.patch(
                "app.skills.service.repository.get_skill_by_name_ci", side_effect=_pre_check_misses_once
            ):
                with pytest.raises(AppException) as exc_info:
                    await create_skill_service(session, current_user=_HR_ADMIN, request=CreateSkillRequest(name=name))

            assert exc_info.value.status_code == 409
            assert exc_info.value.error_code == "SKILL_NAME_CONFLICT"
            assert exc_info.value.extra["existing_skill"]["id"] == str(original.id)
            assert exc_info.value.extra["existing_skill"]["name"] == name
            assert call_count == 2

            all_skills = await list_all_skills(session)
            matching = [s for s in all_skills if s.name == name]
            assert len(matching) == 1
    finally:
        async with _session_factory() as cleanup_session:
            await cleanup_session.execute(delete(Skill).where(Skill.name == name))
            await cleanup_session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_create_skill_service_rejects_employee_role():
    async with _seeded_session() as session:
        with pytest.raises(AppException) as exc_info:
            await create_skill_service(
                session, current_user=_EMPLOYEE, request=CreateSkillRequest(name="Employee Attempt")
            )

        assert exc_info.value.status_code == 403
