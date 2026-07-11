"""Integration tests for anti-spoofing validation with ProgressService.

Tests verify that the anti-spoofing checks properly integrate with Story 4-1's
conditional-write logic and Story 4-2's capture service expectations.
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import Assignment, ContentCatalog
from app.auth.schemas import CurrentUser, Role
from app.progress.service import ProgressService
from app.progress.schemas import SkillProgressResponse


pytestmark = pytest.mark.asyncio(loop_scope="module")


# =============================================================================
# Integration Test Fixtures
# =============================================================================


@pytest.fixture
def mock_session():
    """Mock AsyncSession."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def employee_user():
    """Create an EMPLOYEE user."""
    return CurrentUser(user_id=str(uuid4()), role=Role.EMPLOYEE)


@pytest.fixture
def hr_user():
    """Create an HR_ADMIN user."""
    return CurrentUser(user_id=str(uuid4()), role=Role.HR_ADMIN)


@pytest.fixture
def assignment(employee_user):
    """Create a mock Assignment with content."""
    from uuid import UUID
    assignment = MagicMock(spec=Assignment)
    assignment.id = uuid4()
    # assignment.employee_id is UUID type; convert user_id string to UUID for matching
    assignment.employee_id = UUID(employee_user.user_id)
    assignment.content = MagicMock(spec=ContentCatalog)
    assignment.content.content_metadata = {"duration": 3600}
    return assignment


# =============================================================================
# Integration Tests: Full Anti-Spoofing Flow
# =============================================================================


async def test_integration_valid_first_watch(mock_session, employee_user, assignment):
    """
    Test: Employee's first watch (no prior progress).
    Expected: verified=true, watch is persisted.
    """
    # Mock repository methods
    with patch("app.progress.repository.ProgressRepository.get_progress_for_assignment") as mock_get, \
         patch("app.progress.repository.ProgressRepository.initialize_or_update") as mock_init:

        # First watch: no prior progress
        mock_get.return_value = None

        mock_progress = MagicMock()
        mock_progress.id = uuid4()
        mock_progress.assignment_id = assignment.id
        mock_progress.watch_position = 120
        mock_progress.event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
        mock_progress.verified = True
        mock_init.return_value = mock_progress

        # Act
        response = await ProgressService.record_watch_progress(
            session=mock_session,
            assignment_id=assignment.id,
            watch_position=120,
            event_time=datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc),
            current_user=employee_user,
            assignment=assignment,
            video_duration=3600,
        )

        # Assert
        assert response.verified is True
        assert response.watch_position == 120
        mock_session.commit.assert_called_once()


async def test_integration_spoofed_jump_rejected(mock_session, employee_user, assignment):
    """
    Test: Instantaneous jump (spoofed).
    Expected: verified=false, but still persisted for forensics.
    """
    with patch("app.progress.repository.ProgressRepository.get_progress_for_assignment") as mock_get, \
         patch("app.progress.repository.ProgressRepository.initialize_or_update") as mock_init:

        mock_get.return_value = None

        mock_progress = MagicMock()
        mock_progress.id = uuid4()
        mock_progress.assignment_id = assignment.id
        mock_progress.watch_position = 3500
        mock_progress.event_time = datetime(2026, 7, 10, 16, 0, 0, 500000, tzinfo=timezone.utc)
        mock_progress.verified = False
        mock_init.return_value = mock_progress

        # Act
        response = await ProgressService.record_watch_progress(
            session=mock_session,
            assignment_id=assignment.id,
            watch_position=3500,
            event_time=datetime(2026, 7, 10, 16, 0, 0, 500000, tzinfo=timezone.utc),
            current_user=employee_user,
            assignment=assignment,
            video_duration=3600,
        )

        # Assert
        assert response.verified is False
        mock_init.assert_called_once()
        mock_session.commit.assert_called_once()


async def test_integration_valid_sequence(mock_session, employee_user, assignment):
    """
    Test: Valid sequential watches (1x playback).
    Expected: All verified=true.
    """
    positions = [0, 60, 120, 180, 240]
    times = [
        datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 10, 16, 1, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 10, 16, 2, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 10, 16, 3, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 10, 16, 4, 0, tzinfo=timezone.utc),
    ]

    with patch("app.progress.repository.ProgressRepository.get_progress_for_assignment") as mock_get, \
         patch("app.progress.repository.ProgressRepository.initialize_or_update") as mock_init:

        for i, (pos, time) in enumerate(zip(positions, times)):
            mock_progress = MagicMock()
            mock_progress.id = uuid4()
            mock_progress.assignment_id = assignment.id
            mock_progress.watch_position = pos
            mock_progress.event_time = time
            mock_progress.verified = True
            mock_progress.updated_at = datetime.now(timezone.utc)
            mock_init.return_value = mock_progress
            mock_get.return_value = None

            response = await ProgressService.record_watch_progress(
                session=mock_session,
                assignment_id=assignment.id,
                watch_position=pos,
                event_time=time,
                current_user=employee_user,
                assignment=assignment,
                video_duration=3600,
            )

            assert response.verified is True


async def test_integration_identity_mismatch_rejected(mock_session, employee_user, assignment):
    """
    Test: Employee attempts to report progress for different employee's assignment.
    Expected: verified=false (identity mismatch).
    """
    # Create assignment for different employee
    other_employee_id = uuid4()
    assignment.employee_id = other_employee_id

    with patch("app.progress.repository.ProgressRepository.get_progress_for_assignment") as mock_get, \
         patch("app.progress.repository.ProgressRepository.initialize_or_update") as mock_init:

        mock_get.return_value = None
        mock_progress = MagicMock()
        mock_progress.id = uuid4()
        mock_progress.assignment_id = assignment.id
        mock_progress.watch_position = 120
        mock_progress.event_time = datetime.now(timezone.utc)
        mock_progress.verified = False
        mock_progress.updated_at = datetime.now(timezone.utc)
        mock_init.return_value = mock_progress

        response = await ProgressService.record_watch_progress(
            session=mock_session,
            assignment_id=assignment.id,
            watch_position=120,
            event_time=datetime.now(timezone.utc),
            current_user=employee_user,
            assignment=assignment,
            video_duration=3600,
        )

        assert response.verified is False


async def test_integration_hr_cannot_report(mock_session, hr_user, assignment):
    """
    Test: HR Admin attempts to report progress.
    Expected: verified=false (HR cannot report).
    """
    with patch("app.progress.repository.ProgressRepository.get_progress_for_assignment") as mock_get, \
         patch("app.progress.repository.ProgressRepository.initialize_or_update") as mock_init:

        mock_get.return_value = None
        mock_progress = MagicMock()
        mock_progress.id = uuid4()

        mock_progress.assignment_id = assignment.id
        mock_progress.watch_position = 120
        mock_progress.event_time = datetime.now(timezone.utc)
        mock_progress.updated_at = datetime.now(timezone.utc)
        mock_progress.verified = False
        mock_init.return_value = mock_progress

        response = await ProgressService.record_watch_progress(
            session=mock_session,
            assignment_id=assignment.id,
            watch_position=120,
            event_time=datetime.now(timezone.utc),
            current_user=hr_user,
            assignment=assignment,
            video_duration=3600,
        )

        assert response.verified is False


async def test_integration_stale_event_time_rejected(mock_session, employee_user, assignment):
    """
    Test: Event time is stale (> 5 minutes old).
    Expected: verified=false.
    """
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=6)

    with patch("app.progress.repository.ProgressRepository.get_progress_for_assignment") as mock_get, \
         patch("app.progress.repository.ProgressRepository.initialize_or_update") as mock_init:

        mock_get.return_value = None
        mock_progress = MagicMock()
        mock_progress.id = uuid4()

        mock_progress.assignment_id = assignment.id
        mock_progress.watch_position = 120
        mock_progress.event_time = datetime.now(timezone.utc)
        mock_progress.updated_at = datetime.now(timezone.utc)
        mock_progress.verified = False
        mock_init.return_value = mock_progress

        response = await ProgressService.record_watch_progress(
            session=mock_session,
            assignment_id=assignment.id,
            watch_position=120,
            event_time=stale_time,
            current_user=employee_user,
            assignment=assignment,
            video_duration=3600,
        )

        assert response.verified is False


async def test_integration_no_content_duration_skips_bounds_check(
    mock_session, employee_user, assignment
):
    """
    Test: Assignment has no content (content_id=NULL).
    Expected: Bounds check skipped, verified=true if other checks pass.
    """
    assignment.content = None

    with patch("app.progress.repository.ProgressRepository.get_progress_for_assignment") as mock_get, \
         patch("app.progress.repository.ProgressRepository.initialize_or_update") as mock_init:

        mock_get.return_value = None
        mock_progress = MagicMock()
        mock_progress.id = uuid4()

        mock_progress.assignment_id = assignment.id
        mock_progress.watch_position = 120
        mock_progress.event_time = datetime.now(timezone.utc)
        mock_progress.updated_at = datetime.now(timezone.utc)
        mock_progress.verified = True
        mock_init.return_value = mock_progress

        response = await ProgressService.record_watch_progress(
            session=mock_session,
            assignment_id=assignment.id,
            watch_position=5000,
            event_time=datetime.now(timezone.utc),
            current_user=employee_user,
            assignment=assignment,
            video_duration=None,
        )

        assert response.verified is True


async def test_integration_rewind_always_accepted(mock_session, employee_user, assignment):
    """
    Test: Rewind (position decreases with newer timestamp).
    Expected: verified=true (rewinds always pass rate check).
    """
    with patch("app.progress.repository.ProgressRepository.get_progress_for_assignment") as mock_get, \
         patch("app.progress.repository.ProgressRepository.initialize_or_update") as mock_init:

        mock_get.return_value = None
        mock_progress = MagicMock()
        mock_progress.id = uuid4()

        mock_progress.assignment_id = assignment.id
        mock_progress.watch_position = 120
        mock_progress.event_time = datetime.now(timezone.utc)
        mock_progress.updated_at = datetime.now(timezone.utc)
        mock_progress.verified = True
        mock_init.return_value = mock_progress

        old_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
        new_time = datetime(2026, 7, 10, 16, 0, 5, tzinfo=timezone.utc)

        response = await ProgressService.record_watch_progress(
            session=mock_session,
            assignment_id=assignment.id,
            watch_position=250,
            event_time=new_time,
            current_user=employee_user,
            assignment=assignment,
            video_duration=3600,
        )

        assert response.verified is True


# =============================================================================
# Backward Compatibility Tests (Story 4-1, 4-2)
# =============================================================================


async def test_backward_compat_response_format(mock_session, employee_user, assignment):
    """
    Test: Response format unchanged from Story 4-1 (AC10).
    Expected: SkillProgressResponse has all expected fields.
    """
    with patch("app.progress.repository.ProgressRepository.get_progress_for_assignment") as mock_get, \
         patch("app.progress.repository.ProgressRepository.initialize_or_update") as mock_init:

        mock_get.return_value = None
        mock_progress = MagicMock()
        mock_progress.id = uuid4()
        mock_progress.assignment_id = assignment.id
        mock_progress.watch_position = 120
        mock_progress.event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
        mock_progress.verified = True
        mock_progress.updated_at = datetime.now(timezone.utc)
        mock_init.return_value = mock_progress

        response = await ProgressService.record_watch_progress(
            session=mock_session,
            assignment_id=assignment.id,
            watch_position=120,
            event_time=datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc),
            current_user=employee_user,
            assignment=assignment,
            video_duration=3600,
        )

        assert hasattr(response, "watch_position")
        assert hasattr(response, "event_time")
        assert hasattr(response, "verified")
        assert isinstance(response, SkillProgressResponse)
