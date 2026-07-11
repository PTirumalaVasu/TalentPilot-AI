"""Live-DB tests for Content Discovery grid data (Story 2.5, AC1-AC3).

Uses a private engine/session -- the established Story 3.1/2.4 pattern --
rather than conftest.py's shared db_session/test_engine fixture (still an
unfixed drop_all() landmine per deferred-work.md). Test-created rows are only
flush()'d and cleaned up via rollback() in the finally block.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import ContentCatalog, Skill
from app.assignments.repository import create_assignment
from app.assignments.service import list_my_assignments
from app.auth.schemas import CurrentUser, Role
from app.core.config import settings
from app.core.embedding import embed_text
from app.core.errors import AppException
from app.core.seed_ids import JORDAN_ID
from app.core.seeds import CASEY_ID, MORGAN_ID, RITA_ID, SKILL_DATA_VIZ_ID, SKILL_PYTHON_ID, run_seeds
from app.progress.repository import ProgressRepository

pytestmark = pytest.mark.asyncio(loop_scope="module")

_engine = create_async_engine(settings.DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)

_SKILL_EMBEDDING = embed_text("Data Visualization: creating charts, graphs, and dashboards")


@asynccontextmanager
async def _seeded_session():
    async with _session_factory() as session:
        await run_seeds(session)
        try:
            yield session
        finally:
            await session.rollback()


async def _make_matching_content(session, *, skill_id, duration: str | None = "PT10M0S") -> ContentCatalog:
    """A Content row with an embedding identical to the fixed skill embedding
    used in these tests, guaranteeing a match clears the 0.7 threshold."""
    content = ContentCatalog(
        skill_id=skill_id,
        title="Excel Charting Tutorial",
        description="How to build charts and graphs in Excel",
        type="VIDEO",
        url="https://example.com/video",
        embedding=_SKILL_EMBEDDING,
        source="YOUTUBE" if duration else "MANUAL",
        content_metadata={"duration": duration} if duration else None,
    )
    session.add(content)
    await session.flush()
    return content


async def _make_unrelated_content(session, *, skill_id) -> ContentCatalog:
    """A Content row embedded far enough from the fixed skill embedding to
    never clear the 0.7 similarity threshold."""
    content = ContentCatalog(
        skill_id=skill_id,
        title="Unrelated content",
        description="How to boil pasta al dente",
        type="VIDEO",
        url="https://example.com/unrelated",
        embedding=embed_text("How to boil pasta al dente: a simple cooking guide"),
        source="MANUAL",
    )
    session.add(content)
    await session.flush()
    return content


# --- AC1: hard-scoping + EMPLOYEE-only gate ----------------------------------


async def test_hr_admin_is_rejected_with_403():
    async with _seeded_session() as session:
        hr_user = CurrentUser(role=Role.HR_ADMIN, user_id=str(RITA_ID))

        with pytest.raises(AppException) as exc_info:
            await list_my_assignments(session, current_user=hr_user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.error_code == "FORBIDDEN_NOT_EMPLOYEE"


async def test_employee_sees_only_own_assignments():
    async with _seeded_session() as session:
        await create_assignment(
            session, employee_id=CASEY_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )
        await create_assignment(
            session, employee_id=MORGAN_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )

        casey_user = CurrentUser(role=Role.EMPLOYEE, user_id=str(CASEY_ID))
        response = await list_my_assignments(session, current_user=casey_user)

        employee_assignment_skill_ids = {item.skill_id for item in response.assignments}
        assert SKILL_DATA_VIZ_ID in employee_assignment_skill_ids
        # Casey's own list must never leak Morgan's assignment count.
        casey_assignment_count = sum(1 for item in response.assignments if item.skill_id == SKILL_DATA_VIZ_ID)
        assert casey_assignment_count == 1


# --- AC2: content composition + status/group derivation ----------------------


async def test_assignment_with_matching_content_populates_content_field():
    async with _seeded_session() as session:
        content = await _make_matching_content(session, skill_id=SKILL_DATA_VIZ_ID)
        # Force the seeded Skill's embedding to match, so match_content_for_skill finds it.
        skill = await session.get(Skill, SKILL_DATA_VIZ_ID)
        skill.embedding = _SKILL_EMBEDDING
        await session.flush()

        await create_assignment(
            session, employee_id=CASEY_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )

        casey_user = CurrentUser(role=Role.EMPLOYEE, user_id=str(CASEY_ID))
        response = await list_my_assignments(session, current_user=casey_user)

        item = next(i for i in response.assignments if i.skill_id == SKILL_DATA_VIZ_ID)
        assert item.content is not None
        assert item.content.id == content.id
        assert item.skill_name == "Data Visualization"


async def test_assignment_with_no_qualifying_content_has_null_content():
    async with _seeded_session() as session:
        await _make_unrelated_content(session, skill_id=SKILL_PYTHON_ID)

        await create_assignment(
            session, employee_id=CASEY_ID, skill_id=SKILL_PYTHON_ID, content_id=None, assigned_by=RITA_ID
        )

        casey_user = CurrentUser(role=Role.EMPLOYEE, user_id=str(CASEY_ID))
        response = await list_my_assignments(session, current_user=casey_user)

        item = next(i for i in response.assignments if i.skill_id == SKILL_PYTHON_ID)
        assert item.content is None


async def test_status_and_group_derivation_from_watch_position():
    async with _seeded_session() as session:
        not_started = await create_assignment(
            session, employee_id=MORGAN_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )
        in_progress = await create_assignment(
            session, employee_id=MORGAN_ID, skill_id=SKILL_PYTHON_ID, content_id=None, assigned_by=RITA_ID
        )

        await ProgressRepository.create_watch_progress(
            session, in_progress.id, 50, datetime.now(timezone.utc), False
        )

        morgan_user = CurrentUser(role=Role.EMPLOYEE, user_id=str(MORGAN_ID))
        response = await list_my_assignments(session, current_user=morgan_user)

        not_started_item = next(i for i in response.assignments if i.assignment_id == not_started.id)
        in_progress_item = next(i for i in response.assignments if i.assignment_id == in_progress.id)

        assert not_started_item.status == "NOT_STARTED"
        assert not_started_item.group == "TO_START"
        assert in_progress_item.status == "IN_PROGRESS"
        assert in_progress_item.group == "IN_PROGRESS"


async def test_completed_status_folds_into_in_progress_group():
    """A watch_position at/above the matched Content's known duration derives
    COMPLETED -- and, per the Dev Notes' deliberate folding decision (not a
    reproduction of the prototype's disappearing-video bug), COMPLETED still
    groups as IN_PROGRESS for section placement, not a third ungrouped bucket."""
    async with _seeded_session() as session:
        content = await _make_matching_content(session, skill_id=SKILL_DATA_VIZ_ID, duration="PT10M0S")
        skill = await session.get(Skill, SKILL_DATA_VIZ_ID)
        skill.embedding = _SKILL_EMBEDDING
        await session.flush()

        assignment = await create_assignment(
            session, employee_id=CASEY_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )
        # duration is 600s (PT10M0S) -- a watch_position >= 600 derives COMPLETED.
        await ProgressRepository.create_watch_progress(session, assignment.id, 600, datetime.now(timezone.utc), False)

        casey_user = CurrentUser(role=Role.EMPLOYEE, user_id=str(CASEY_ID))
        response = await list_my_assignments(session, current_user=casey_user)

        item = next(i for i in response.assignments if i.assignment_id == assignment.id)
        assert item.content is not None and item.content.id == content.id
        assert item.status == "COMPLETED"
        assert item.group == "IN_PROGRESS"
        assert response.in_progress_count >= 1
        assert response.total == response.in_progress_count + response.to_start_count


# --- AC3: summary counts always match the assembled list ---------------------


async def test_summary_counts_match_assignment_groups():
    async with _seeded_session() as session:
        to_start = await create_assignment(
            session, employee_id=JORDAN_ID, skill_id=SKILL_DATA_VIZ_ID, content_id=None, assigned_by=RITA_ID
        )
        in_progress = await create_assignment(
            session, employee_id=JORDAN_ID, skill_id=SKILL_PYTHON_ID, content_id=None, assigned_by=RITA_ID
        )

        await ProgressRepository.create_watch_progress(
            session, in_progress.id, 30, datetime.now(timezone.utc), False
        )

        jordan_user = CurrentUser(role=Role.EMPLOYEE, user_id=str(JORDAN_ID))
        response = await list_my_assignments(session, current_user=jordan_user)

        assert response.total == len(response.assignments)
        assert response.in_progress_count == sum(1 for i in response.assignments if i.group == "IN_PROGRESS")
        assert response.to_start_count == sum(1 for i in response.assignments if i.group == "TO_START")
        assert response.total == response.in_progress_count + response.to_start_count

        # Sanity: our two freshly-created assignments really did land in each bucket.
        to_start_item = next(i for i in response.assignments if i.assignment_id == to_start.id)
        in_progress_item = next(i for i in response.assignments if i.assignment_id == in_progress.id)
        assert to_start_item.group == "TO_START"
        assert in_progress_item.group == "IN_PROGRESS"
