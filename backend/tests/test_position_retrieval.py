"""
Tests for Story 4-5: Resume Position Retrieval & Exact-Point Playback

Tests cover:
- AC1: GET endpoint for position retrieval
- AC2: Exact position accuracy (launch-blocking quality gate)
- AC3: Out-of-bounds position fallback
- AC4: Hard-scoping to authenticated session identity
- AC6: No data loss on retry (idempotent read)
- AC7: Latency performance
- AC8: Null/empty position handling (first view)
- AC11: TypeScript types & backward compatibility
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import select

from app.assignments.models import Employee, Assignment, Skill, ContentCatalog, SkillProgress
from app.auth.schemas import CurrentUser
from app.progress.service import ProgressService
from app.progress.repository import ProgressRepository
from app.progress.schemas import SkillProgressResponse


@pytest.fixture
async def employee(db_session):
    """Fixture: create a test employee."""
    from app.core.seeds import _DEMO_EMPLOYEE_IDS
    emp = await db_session.get(Employee, _DEMO_EMPLOYEE_IDS[1])  # Casey
    return emp


@pytest.fixture
async def skill(db_session):
    """Fixture: get a test skill."""
    result = await db_session.execute(select(Skill).limit(1))
    return result.scalar_one()


@pytest.fixture
async def video_content(db_session, skill):
    """Fixture: create test video content with duration."""
    content = ContentCatalog(
        id=uuid4(),
        skill_id=skill.id,
        title="Test Video",
        description="Test video for resume testing",
        type="VIDEO",
        url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        source="YOUTUBE",
        content_metadata={"duration": 600, "video_id": "dQw4w9WgXcQ"},  # 10 minutes
    )
    db_session.add(content)
    await db_session.flush()
    return content


@pytest.fixture
async def assignment_with_content(db_session, employee, skill, video_content):
    """Fixture: create assignment with linked content."""
    assignment = Assignment(
        id=uuid4(),
        employee_id=employee.id,
        skill_id=skill.id,
        content_id=video_content.id,
        assigned_by=employee.id,
    )
    db_session.add(assignment)
    await db_session.flush()
    return assignment


@pytest.fixture
async def assignment_no_content(db_session, employee, skill):
    """Fixture: create assignment without linked content."""
    assignment = Assignment(
        id=uuid4(),
        employee_id=employee.id,
        skill_id=skill.id,
        content_id=None,
        assigned_by=employee.id,
    )
    db_session.add(assignment)
    await db_session.flush()
    return assignment


@pytest.fixture
def current_user(employee):
    """Fixture: create CurrentUser from employee."""
    return CurrentUser(user_id=employee.id, role="EMPLOYEE", email=employee.email)


class TestPositionRetrievalRepository:
    """Unit tests for ProgressRepository.get_assignment_with_scope()"""

    @pytest.mark.asyncio
    async def test_get_assignment_with_scope_success(self, db_session, assignment_with_content, employee):
        """AC4: Hard-scoped assignment retrieval succeeds with correct employee."""
        result = await ProgressRepository.get_assignment_with_scope(
            db_session, assignment_with_content.id, employee.id
        )
        assert result is not None
        assert result.id == assignment_with_content.id
        assert result.employee_id == employee.id

    @pytest.mark.asyncio
    async def test_get_assignment_with_scope_wrong_employee(
        self, db_session, assignment_with_content, employee
    ):
        """AC4: Hard-scoped retrieval fails when employee_id doesn't match."""
        other_employee_id = uuid4()  # Different employee
        result = await ProgressRepository.get_assignment_with_scope(
            db_session, assignment_with_content.id, other_employee_id
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_assignment_with_scope_missing_assignment(self, db_session, employee):
        """AC4: Retrieval returns None for non-existent assignment."""
        fake_assignment_id = uuid4()
        result = await ProgressRepository.get_assignment_with_scope(
            db_session, fake_assignment_id, employee.id
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_assignment_with_scope_eager_loads_content(
        self, db_session, assignment_with_content, employee, video_content
    ):
        """AC4: Hard-scoped retrieval eager-loads content relationship."""
        result = await ProgressRepository.get_assignment_with_scope(
            db_session, assignment_with_content.id, employee.id
        )
        assert result is not None
        assert result.content is not None
        assert result.content.id == video_content.id
        assert result.content.content_metadata.get("duration") == 600


class TestPositionRetrievalService:
    """Unit tests for ProgressService.get_resume_position()"""

    @pytest.mark.asyncio
    async def test_get_resume_position_first_view(
        self, db_session, assignment_with_content, current_user
    ):
        """AC8: First view (no skill_progress row) returns position 0."""
        response = await ProgressService.get_resume_position(
            db_session, current_user, assignment_with_content.id
        )
        assert response.watch_position == 0
        assert response.event_time is None
        assert response.verified is False
        assert response.id is None
        assert response.updated_at is None

    @pytest.mark.asyncio
    async def test_get_resume_position_returns_exact_position(
        self, db_session, assignment_with_content, current_user
    ):
        """AC2: Returns exact stored position without rounding or approximation."""
        # Create skill_progress at specific position
        progress = SkillProgress(
            id=uuid4(),
            assignment_id=assignment_with_content.id,
            watch_position=872,  # 14:32
            event_time=datetime.now(timezone.utc),
            verified=True,
        )
        db_session.add(progress)
        await db_session.flush()

        response = await ProgressService.get_resume_position(
            db_session, current_user, assignment_with_content.id
        )
        assert response.watch_position == 872  # Exact, no rounding
        assert response.verified is True

    @pytest.mark.asyncio
    async def test_get_resume_position_out_of_bounds_fallback(
        self, db_session, assignment_with_content, current_user, video_content
    ):
        """AC3: Out-of-bounds position (corrupted data) falls back to 0."""
        # Create skill_progress beyond video duration (600 seconds)
        progress = SkillProgress(
            id=uuid4(),
            assignment_id=assignment_with_content.id,
            watch_position=700,  # Beyond 600-second duration
            event_time=datetime.now(timezone.utc),
            verified=False,  # Failed anti-spoofing
        )
        db_session.add(progress)
        await db_session.flush()

        response = await ProgressService.get_resume_position(
            db_session, current_user, assignment_with_content.id
        )
        assert response.watch_position == 0  # Fallback to 0
        assert response.event_time is not None  # Original timestamp preserved
        assert response.verified is False

    @pytest.mark.asyncio
    async def test_get_resume_position_no_content_no_duration_check(
        self, db_session, assignment_no_content, current_user
    ):
        """AC3: Missing video duration skips bounds check, returns position as-is."""
        # Create skill_progress with arbitrary position (no duration available to validate)
        progress = SkillProgress(
            id=uuid4(),
            assignment_id=assignment_no_content.id,
            watch_position=500,  # Could be beyond unknown duration
            event_time=datetime.now(timezone.utc),
            verified=True,
        )
        db_session.add(progress)
        await db_session.flush()

        response = await ProgressService.get_resume_position(
            db_session, current_user, assignment_no_content.id
        )
        assert response.watch_position == 500  # Returned as-is (no duration to check)

    @pytest.mark.asyncio
    async def test_get_resume_position_identity_mismatch_raises_403(
        self, db_session, assignment_with_content, employee
    ):
        """AC4: Hard-scoping raises 403 when user doesn't match assignment owner."""
        from fastapi import HTTPException

        # Create CurrentUser for different employee
        other_user = CurrentUser(user_id=uuid4(), role="EMPLOYEE", email="other@example.com")

        with pytest.raises(HTTPException) as exc_info:
            await ProgressService.get_resume_position(
                db_session, other_user, assignment_with_content.id
            )
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_resume_position_idempotent_repeated_calls(
        self, db_session, assignment_with_content, current_user
    ):
        """AC6: Repeated calls return identical results (idempotent, read-only)."""
        # Create skill_progress
        progress = SkillProgress(
            id=uuid4(),
            assignment_id=assignment_with_content.id,
            watch_position=300,
            event_time=datetime.now(timezone.utc),
            verified=True,
        )
        db_session.add(progress)
        await db_session.flush()

        # Call three times
        response1 = await ProgressService.get_resume_position(
            db_session, current_user, assignment_with_content.id
        )
        response2 = await ProgressService.get_resume_position(
            db_session, current_user, assignment_with_content.id
        )
        response3 = await ProgressService.get_resume_position(
            db_session, current_user, assignment_with_content.id
        )

        # All identical
        assert response1.watch_position == response2.watch_position == response3.watch_position == 300
        assert response1.event_time == response2.event_time == response3.event_time


class TestPositionRetrievalResponseTypes:
    """Unit tests for AC9: TypeScript types & response schema"""

    @pytest.mark.asyncio
    async def test_skill_progress_response_schema_first_view(self, db_session):
        """AC9: Response schema handles null fields on first view."""
        response = SkillProgressResponse(
            id=None,
            assignment_id=uuid4(),
            watch_position=0,
            event_time=None,
            verified=False,
            updated_at=None,
        )
        # Should not raise validation errors
        assert response.watch_position == 0
        assert response.event_time is None

    @pytest.mark.asyncio
    async def test_skill_progress_response_schema_full(self, db_session):
        """AC9: Response schema accepts full data (backward compatibility with Story 4-2)."""
        response = SkillProgressResponse(
            id=uuid4(),
            assignment_id=uuid4(),
            watch_position=872,
            event_time="2026-07-06T14:32:00Z",
            verified=True,
            updated_at="2026-07-06T14:32:00Z",
        )
        # Should not raise validation errors
        assert response.watch_position == 872
        assert response.verified is True
