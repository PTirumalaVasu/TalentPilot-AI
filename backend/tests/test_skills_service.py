"""Tests for the skills module's service layer (Story 6.1, AD-11; Story 6.2, FR-20;
Story 6.3, FR-21/22).

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
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from pydantic import ValidationError

from app.assignments.models import Assignment, ContentCatalog
from app.auth.schemas import CurrentUser, Role
from app.core.config import settings
from app.core.errors import AppException
from app.core.seed_ids import CASEY_ID, RITA_ID
from app.core.seeds import run_seeds
from app.skills import repository as skills_repository
from app.skills.models import Skill
from app.skills.schemas import CreateSkillRequest, UpdateSkillRequest
from app.skills.service import (
    _build_embedding_text,
    create_skill_service,
    delete_skill_service,
    get_skill_embedding,
    list_all_skills,
    update_skill_service,
)

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


# ---------------------------------------------------------------------------
# Story 6.3: update_skill_service / delete_skill_service
# ---------------------------------------------------------------------------


async def _create_unlocked_skill(session, *, name: str, description: str | None = "original description") -> Skill:
    response = await create_skill_service(
        session, current_user=_HR_ADMIN, request=CreateSkillRequest(name=name, description=description)
    )
    result = await session.execute(select(Skill).where(Skill.id == response.id))
    return result.scalar_one()


@pytest.mark.asyncio(loop_scope="module")
async def test_update_skill_service_renames_and_recomputes_embedding():
    name = f"Rename Source {uuid.uuid4().hex[:8]}"
    new_name = f"Rename Target {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            skill = await _create_unlocked_skill(session, name=name)
            original_embedding = await get_skill_embedding(session, skill.id)

            response = await update_skill_service(
                session,
                current_user=_HR_ADMIN,
                skill_id=skill.id,
                request=UpdateSkillRequest(name=new_name, description="new description"),
            )

            assert response.name == new_name
            assert response.description == "new description"
            new_embedding = await get_skill_embedding(session, skill.id)
            assert new_embedding != original_embedding
        finally:
            await session.execute(delete(Skill).where(Skill.name.in_([name, new_name])))
            await session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_update_skill_service_resubmitting_own_current_name_is_not_a_conflict():
    name = f"Self Resubmit {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            skill = await _create_unlocked_skill(session, name=name)

            response = await update_skill_service(
                session,
                current_user=_HR_ADMIN,
                skill_id=skill.id,
                request=UpdateSkillRequest(name=name),
            )

            assert response.name == name
        finally:
            await session.execute(delete(Skill).where(Skill.name == name))
            await session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_update_skill_service_unchanged_fields_do_not_recompute_embedding():
    name = f"No Change {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            skill = await _create_unlocked_skill(session, name=name, description="same description")
            original_embedding = await get_skill_embedding(session, skill.id)

            await update_skill_service(
                session,
                current_user=_HR_ADMIN,
                skill_id=skill.id,
                request=UpdateSkillRequest(name=name, description="same description"),
            )

            unchanged_embedding = await get_skill_embedding(session, skill.id)
            assert unchanged_embedding == original_embedding
        finally:
            await session.execute(delete(Skill).where(Skill.name == name))
            await session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_update_skill_service_partial_update_leaves_other_field_untouched():
    name = f"Partial Update {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            skill = await _create_unlocked_skill(session, name=name, description="keep me")

            response = await update_skill_service(
                session,
                current_user=_HR_ADMIN,
                skill_id=skill.id,
                request=UpdateSkillRequest(description="changed"),
            )

            assert response.name == name
            assert response.description == "changed"
        finally:
            await session.execute(delete(Skill).where(Skill.name == name))
            await session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_update_skill_service_rejects_duplicate_name_excluding_self():
    first_name = f"Duplicate Rename A {uuid.uuid4().hex[:8]}"
    second_name = f"Duplicate Rename B {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            first = await _create_unlocked_skill(session, name=first_name)
            second = await _create_unlocked_skill(session, name=second_name)

            with pytest.raises(AppException) as exc_info:
                await update_skill_service(
                    session,
                    current_user=_HR_ADMIN,
                    skill_id=second.id,
                    request=UpdateSkillRequest(name=first_name),
                )

            assert exc_info.value.status_code == 409
            assert exc_info.value.error_code == "SKILL_NAME_CONFLICT"
            # Unlike create's 409 (Story 6.2), rename's 409 carries no
            # existing_skill redirect payload -- AC1's explicit "no
            # redirect payload" requirement (code review, 2026-09-09).
            assert exc_info.value.extra == {}
        finally:
            await session.execute(delete(Skill).where(Skill.name.in_([first_name, second_name])))
            await session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_update_skill_service_rejects_locked_skill():
    name = f"Locked Update {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            skill = await _create_unlocked_skill(session, name=name)
            skill.ever_assigned = True
            await session.flush()

            with pytest.raises(AppException) as exc_info:
                await update_skill_service(
                    session,
                    current_user=_HR_ADMIN,
                    skill_id=skill.id,
                    request=UpdateSkillRequest(name="Should Not Apply"),
                )

            assert exc_info.value.status_code == 403
            assert exc_info.value.error_code == "SKILL_LOCKED"
        finally:
            await session.execute(delete(Skill).where(Skill.name == name))
            await session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_update_skill_service_rejects_nonexistent_skill():
    async with _seeded_session() as session:
        with pytest.raises(AppException) as exc_info:
            await update_skill_service(
                session,
                current_user=_HR_ADMIN,
                skill_id=uuid.uuid4(),
                request=UpdateSkillRequest(name="Whatever"),
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.error_code == "SKILL_NOT_FOUND"


@pytest.mark.asyncio(loop_scope="module")
async def test_update_skill_service_rejects_employee_role():
    name = f"Employee Update Attempt {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            skill = await _create_unlocked_skill(session, name=name)

            with pytest.raises(AppException) as exc_info:
                await update_skill_service(
                    session,
                    current_user=_EMPLOYEE,
                    skill_id=skill.id,
                    request=UpdateSkillRequest(name="New Name"),
                )

            assert exc_info.value.status_code == 403
        finally:
            await session.execute(delete(Skill).where(Skill.name == name))
            await session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_delete_skill_service_hard_deletes_skill_with_no_content():
    name = f"Delete Empty {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        skill = await _create_unlocked_skill(session, name=name)
        skill_id = skill.id

        await delete_skill_service(session, current_user=_HR_ADMIN, skill_id=skill_id)

        result = await session.execute(select(Skill).where(Skill.id == skill_id))
        assert result.scalar_one_or_none() is None


@pytest.mark.asyncio(loop_scope="module")
async def test_delete_skill_service_cascades_attached_content_catalog_rows():
    name = f"Delete With Content {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        skill = await _create_unlocked_skill(session, name=name)
        content = ContentCatalog(
            skill_id=skill.id,
            title="Attached Content",
            type="VIDEO",
            url="https://example.com/video",
            embedding=[0.1] * 384,
            source="MANUAL",
        )
        session.add(content)
        await session.flush()
        content_id = content.id

        await delete_skill_service(session, current_user=_HR_ADMIN, skill_id=skill.id)

        skill_result = await session.execute(select(Skill).where(Skill.id == skill.id))
        assert skill_result.scalar_one_or_none() is None
        content_result = await session.execute(select(ContentCatalog).where(ContentCatalog.id == content_id))
        assert content_result.scalar_one_or_none() is None


@pytest.mark.asyncio(loop_scope="module")
async def test_delete_skill_service_rejects_locked_skill():
    name = f"Locked Delete {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            skill = await _create_unlocked_skill(session, name=name)
            skill.ever_assigned = True
            await session.flush()

            with pytest.raises(AppException) as exc_info:
                await delete_skill_service(session, current_user=_HR_ADMIN, skill_id=skill.id)

            assert exc_info.value.status_code == 403
            assert exc_info.value.error_code == "SKILL_LOCKED"

            result = await session.execute(select(Skill).where(Skill.id == skill.id))
            assert result.scalar_one_or_none() is not None
        finally:
            await session.execute(delete(Skill).where(Skill.name == name))
            await session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_delete_skill_service_rejects_nonexistent_skill():
    async with _seeded_session() as session:
        with pytest.raises(AppException) as exc_info:
            await delete_skill_service(session, current_user=_HR_ADMIN, skill_id=uuid.uuid4())

        assert exc_info.value.status_code == 404
        assert exc_info.value.error_code == "SKILL_NOT_FOUND"


@pytest.mark.asyncio(loop_scope="module")
async def test_delete_skill_service_rejects_employee_role():
    name = f"Employee Delete Attempt {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            skill = await _create_unlocked_skill(session, name=name)

            with pytest.raises(AppException) as exc_info:
                await delete_skill_service(session, current_user=_EMPLOYEE, skill_id=skill.id)

            assert exc_info.value.status_code == 403

            result = await session.execute(select(Skill).where(Skill.id == skill.id))
            assert result.scalar_one_or_none() is not None
        finally:
            await session.execute(delete(Skill).where(Skill.name == name))
            await session.commit()


def test_update_skill_request_rejects_explicit_null_name():
    # Code review, 2026-09-09: `name` is a required Skill-identity field --
    # unlike `description`, an explicit `{"name": null}` must be rejected,
    # not silently accepted as "no change."
    with pytest.raises(ValidationError):
        UpdateSkillRequest(name=None)


def test_update_skill_request_omitted_name_is_fine():
    # Omitting `name` entirely (as opposed to sending it as null) is the
    # normal partial-update case and must not raise.
    request = UpdateSkillRequest(description="only this changes")
    assert "name" not in request.model_dump(exclude_unset=True)


@pytest.mark.asyncio(loop_scope="module")
async def test_update_skill_service_explicit_null_description_clears_it():
    name = f"Null Description {uuid.uuid4().hex[:8]}"
    async with _seeded_session() as session:
        try:
            skill = await _create_unlocked_skill(session, name=name, description="has a value")

            response = await update_skill_service(
                session, current_user=_HR_ADMIN, skill_id=skill.id, request=UpdateSkillRequest(description=None)
            )

            assert response.description is None
        finally:
            await session.execute(delete(Skill).where(Skill.name == name))
            await session.commit()


@pytest.mark.asyncio(loop_scope="module")
async def test_delete_skill_service_converts_integrity_error_to_locked_403():
    """Simulates the exact stale-flag scenario this story's code review
    flagged as a decision-needed item (deferred to Story 6.4): a Skill
    whose `ever_assigned` still reads `false` but which a real Assignment
    already references (constructed directly here since `mark_ever_assigned`
    doesn't exist yet). `delete_skill_service` must convert the resulting
    FK RESTRICT violation into a clean 403, not an unhandled 500.

    Setup is committed (not just flushed) in its own session first, so that
    the expected `db.rollback()` inside `delete_skill_service`'s
    `IntegrityError` handler only undoes the failed delete attempt, not the
    Skill/Assignment fixture rows themselves -- mirrors how a real request
    would hit this against already-committed data.
    """
    name = f"Stale Flag Delete {uuid.uuid4().hex[:8]}"
    async with _session_factory() as setup_session:
        skill = await _create_unlocked_skill(setup_session, name=name)
        assert skill.ever_assigned is False
        assignment = Assignment(employee_id=CASEY_ID, skill_id=skill.id, assigned_by=RITA_ID)
        setup_session.add(assignment)
        await setup_session.commit()
        skill_id = skill.id

    try:
        async with _session_factory() as session:
            with pytest.raises(AppException) as exc_info:
                await delete_skill_service(session, current_user=_HR_ADMIN, skill_id=skill_id)

            assert exc_info.value.status_code == 403
            assert exc_info.value.error_code == "SKILL_LOCKED"

        async with _session_factory() as verify_session:
            result = await verify_session.execute(select(Skill).where(Skill.id == skill_id))
            assert result.scalar_one_or_none() is not None
    finally:
        async with _session_factory() as cleanup_session:
            await cleanup_session.execute(delete(Assignment).where(Assignment.skill_id == skill_id))
            await cleanup_session.execute(delete(Skill).where(Skill.id == skill_id))
            await cleanup_session.commit()
