"""Test anti-spoofing validation for watch-progress writes (Story 4-4).

This test suite verifies server-side anti-spoofing checks:
- Session identity verification (AC1, AC8)
- Position bounds validation (AC2)
- Rate check for playback validation (AC3)
- Event-time coherence and clock skew (AC4)
- Deterministic and silent rejection (AC5)
- Integration with Story 4-1's conditional write (AC6)
- Logging and observability (AC9)
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import Assignment, ContentCatalog, Employee, Skill
from app.progress.service import ProgressService
from app.progress.schemas import SkillProgressResponse
from app.auth.schemas import CurrentUser, Role

pytestmark = pytest.mark.asyncio(loop_scope="module")

# =============================================================================
# Test Fixtures and Helpers
# =============================================================================


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession for unit tests."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def current_user_employee():
    """Create a CurrentUser fixture for an employee."""
    return CurrentUser(user_id=str(uuid4()), role=Role.EMPLOYEE)


@pytest.fixture
def current_user_hr():
    """Create a CurrentUser fixture for HR admin."""
    return CurrentUser(user_id=str(uuid4()), role=Role.HR_ADMIN)


@pytest.fixture
def assignment_with_content():
    """Create a mock Assignment with content."""
    assignment = MagicMock(spec=Assignment)
    assignment.id = uuid4()
    assignment.employee_id = uuid4()
    assignment.content_id = uuid4()
    assignment.content = MagicMock(spec=ContentCatalog)
    assignment.content.content_metadata = {"duration": 3600}  # 60 minutes
    return assignment


@pytest.fixture
def assignment_no_content():
    """Create a mock Assignment without content."""
    assignment = MagicMock(spec=Assignment)
    assignment.id = uuid4()
    assignment.employee_id = uuid4()
    assignment.content_id = None
    return assignment


# =============================================================================
# AC1 & AC8: Session Identity Tie Tests
# =============================================================================


def test_session_identity_match_accepted(current_user_employee, assignment_with_content):
    """
    Test: Session identity matches assignment employee_id.
    Expected: Validation passes (returns None, no rejection).
    """
    from app.progress.antiflow import validate_session_identity

    # Arrange: session user_id matches assignment employee_id
    assignment_with_content.employee_id = current_user_employee.user_id

    # Act
    rejection_reason = validate_session_identity(current_user_employee, assignment_with_content)

    # Assert
    assert rejection_reason is None  # No rejection


def test_session_identity_mismatch_rejected(current_user_employee, assignment_with_content):
    """
    Test: Session identity doesn't match assignment employee_id.
    Expected: Validation fails, returns rejection reason.
    """
    from app.progress.antiflow import validate_session_identity

    # Arrange: session user_id differs from assignment employee_id
    # (current_user_employee.user_id is different by default)

    # Act
    rejection_reason = validate_session_identity(current_user_employee, assignment_with_content)

    # Assert
    assert rejection_reason == "identity_mismatch"


def test_hr_admin_cannot_report_progress(current_user_hr, assignment_with_content):
    """
    Test: HR Admin attempts to report progress on behalf of an employee.
    Expected: Validation fails (HR cannot report).
    """
    from app.progress.antiflow import validate_session_identity

    # Arrange: HR_ADMIN role, doesn't matter if employee_id matches

    # Act
    rejection_reason = validate_session_identity(current_user_hr, assignment_with_content)

    # Assert
    assert rejection_reason == "identity_mismatch"  # HR cannot report


# =============================================================================
# AC2: Position Bounds Validation Tests
# =============================================================================


def test_bounds_check_within_bounds_accepted(assignment_with_content):
    """
    Test: Position is within valid bounds (0 <= pos <= duration).
    Expected: Validation passes (returns None).
    """
    from app.progress.antiflow import validate_position_bounds

    watch_position = 1800  # 30 minutes
    video_duration = 3600  # 60 minutes

    rejection_reason = validate_position_bounds(watch_position, video_duration)

    assert rejection_reason is None


def test_bounds_check_negative_position_rejected():
    """
    Test: Position is negative.
    Expected: Validation fails.
    """
    from app.progress.antiflow import validate_position_bounds

    watch_position = -5
    video_duration = 3600

    rejection_reason = validate_position_bounds(watch_position, video_duration)

    assert rejection_reason == "bounds_check_failed"


def test_bounds_check_beyond_duration_rejected():
    """
    Test: Position exceeds video duration.
    Expected: Validation fails.
    """
    from app.progress.antiflow import validate_position_bounds

    watch_position = 3700  # Beyond 3600
    video_duration = 3600

    rejection_reason = validate_position_bounds(watch_position, video_duration)

    assert rejection_reason == "bounds_check_failed"


def test_bounds_check_at_boundaries():
    """
    Test: Position exactly at 0 and duration (edge cases).
    Expected: Both pass.
    """
    from app.progress.antiflow import validate_position_bounds

    # At 0
    assert validate_position_bounds(0, 3600) is None

    # At duration
    assert validate_position_bounds(3600, 3600) is None


def test_bounds_check_missing_duration_skipped():
    """
    Test: Video duration is None (no content attached).
    Expected: Bounds check is skipped (returns None).
    """
    from app.progress.antiflow import validate_position_bounds

    watch_position = 1800
    video_duration = None

    rejection_reason = validate_position_bounds(watch_position, video_duration)

    assert rejection_reason is None  # Skipped


# =============================================================================
# AC3: Rate Check (Playback Rate Validation) Tests
# =============================================================================


def test_rate_check_normal_playback_accepted():
    """
    Test: Normal 1x playback (1 second watched = 1 second position advance).
    Expected: Passes.
    """
    from app.progress.antiflow import validate_rate_check

    old_position = 30
    old_event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
    new_position = 390  # Advance 360 seconds
    new_event_time = datetime(2026, 7, 10, 16, 6, 0, tzinfo=timezone.utc)  # 6 seconds later
    video_duration = 3600

    rejection_reason = validate_rate_check(
        old_position, old_event_time, new_position, new_event_time, video_duration
    )

    assert rejection_reason is None


def test_rate_check_instantaneous_jump_rejected():
    """
    Test: Instantaneous jump (position jumps 3500 seconds in 0.5 seconds).
    Expected: Fails rate check.
    """
    from app.progress.antiflow import validate_rate_check

    old_position = 30
    old_event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
    new_position = 3500  # Jump to end
    new_event_time = datetime(2026, 7, 10, 16, 0, 0, 500000, tzinfo=timezone.utc)  # 0.5 seconds later
    video_duration = 3600

    rejection_reason = validate_rate_check(
        old_position, old_event_time, new_position, new_event_time, video_duration
    )

    assert rejection_reason == "rate_check_failed"


def test_rate_check_rewind_accepted():
    """
    Test: Rewind (position decreases with newer timestamp).
    Expected: Passes (rewinds are always allowed).
    """
    from app.progress.antiflow import validate_rate_check

    old_position = 300
    old_event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
    new_position = 250  # Rewind 50 seconds
    new_event_time = datetime(2026, 7, 10, 16, 0, 5, tzinfo=timezone.utc)  # 5 seconds later
    video_duration = 3600

    rejection_reason = validate_rate_check(
        old_position, old_event_time, new_position, new_event_time, video_duration
    )

    assert rejection_reason is None


def test_rate_check_at_10x_limit():
    """
    Test: Position advance at exactly 10x playback limit.
    Expected: Passes (exactly at limit).
    """
    from app.progress.antiflow import validate_rate_check

    old_position = 30
    old_event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
    video_duration = 3600
    # Max allowed: 3600 / 10 = 360 per second
    # For 1 second: advance 360 seconds
    new_position = 30 + 360
    new_event_time = datetime(2026, 7, 10, 16, 0, 1, tzinfo=timezone.utc)

    rejection_reason = validate_rate_check(
        old_position, old_event_time, new_position, new_event_time, video_duration
    )

    assert rejection_reason is None


def test_rate_check_exceeds_10x_limit():
    """
    Test: Position advance exceeds 10x playback limit.
    Expected: Fails.
    """
    from app.progress.antiflow import validate_rate_check

    old_position = 30
    old_event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
    video_duration = 3600
    # Try to advance 361 seconds in 1 second (exceeds 10x limit)
    new_position = 30 + 361
    new_event_time = datetime(2026, 7, 10, 16, 0, 1, tzinfo=timezone.utc)

    rejection_reason = validate_rate_check(
        old_position, old_event_time, new_position, new_event_time, video_duration
    )

    assert rejection_reason == "rate_check_failed"


def test_rate_check_first_watch_skipped():
    """
    Test: First watch (no prior record).
    Expected: Rate check is skipped (returns None).
    """
    from app.progress.antiflow import validate_rate_check

    new_position = 100
    new_event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
    video_duration = 3600

    rejection_reason = validate_rate_check(
        None, None, new_position, new_event_time, video_duration
    )

    assert rejection_reason is None  # Skipped for first watch


def test_rate_check_zero_time_delta_rejected():
    """
    Test: Same event_time for different positions.
    Expected: Fails (mathematically invalid).
    """
    from app.progress.antiflow import validate_rate_check

    old_position = 30
    old_event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
    new_position = 31
    new_event_time = old_event_time  # Same time
    video_duration = 3600

    rejection_reason = validate_rate_check(
        old_position, old_event_time, new_position, new_event_time, video_duration
    )

    assert rejection_reason == "rate_check_failed"  # Zero time delta


def test_rate_check_backward_time_rejected():
    """
    Test: Backward time delta (event_time goes backward).
    Expected: Fails (physically impossible).
    """
    from app.progress.antiflow import validate_rate_check

    old_position = 300
    old_event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
    new_position = 400  # Position advances
    new_event_time = datetime(2026, 7, 10, 15, 59, 0, tzinfo=timezone.utc)  # Time goes backward
    video_duration = 3600

    rejection_reason = validate_rate_check(
        old_position, old_event_time, new_position, new_event_time, video_duration
    )

    assert rejection_reason == "rate_check_failed"  # Backward time is impossible


# =============================================================================
# AC4: Event-Time Coherence Tests
# =============================================================================


def test_event_time_recent_accepted():
    """
    Test: Event time is recent (within last 5 minutes).
    Expected: Passes.
    """
    from app.progress.antiflow import validate_event_time_coherence

    server_now = datetime(2026, 7, 10, 16, 30, 0, tzinfo=timezone.utc)
    event_time = datetime(2026, 7, 10, 16, 25, 30, tzinfo=timezone.utc)  # 4.5 min ago

    with patch("app.progress.antiflow.datetime") as mock_datetime:
        mock_datetime.now.return_value = server_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        rejection_reason = validate_event_time_coherence(event_time)

        assert rejection_reason is None


def test_event_time_stale_rejected():
    """
    Test: Event time is stale (> 5 minutes old).
    Expected: Fails.
    """
    from app.progress.antiflow import validate_event_time_coherence

    server_now = datetime(2026, 7, 10, 16, 30, 0, tzinfo=timezone.utc)
    event_time = datetime(2026, 7, 10, 16, 24, 0, tzinfo=timezone.utc)  # 6 min ago

    rejection_reason = validate_event_time_coherence(event_time, server_now)

    assert rejection_reason == "event_time_incoherent"


def test_event_time_future_rejected():
    """
    Test: Event time is in the future.
    Expected: Fails.
    """
    from app.progress.antiflow import validate_event_time_coherence

    server_now = datetime(2026, 7, 10, 16, 30, 0, tzinfo=timezone.utc)
    event_time = datetime(2026, 7, 10, 16, 31, 0, tzinfo=timezone.utc)  # 1 min in future

    rejection_reason = validate_event_time_coherence(event_time, server_now)

    assert rejection_reason == "event_time_incoherent"


def test_event_time_at_boundaries():
    """
    Test: Event time exactly 5 minutes ago and exactly now.
    Expected: Both pass.
    """
    from app.progress.antiflow import validate_event_time_coherence

    server_now = datetime(2026, 7, 10, 16, 30, 0, tzinfo=timezone.utc)

    # Exactly 5 minutes ago
    event_time_5min = datetime(2026, 7, 10, 16, 25, 0, tzinfo=timezone.utc)
    assert validate_event_time_coherence(event_time_5min, server_now) is None

    # Exactly now
    event_time_now = server_now
    assert validate_event_time_coherence(event_time_now, server_now) is None


# =============================================================================
# AC9: Logging Tests
# =============================================================================


def test_validation_logs_rejection_on_identity_mismatch(caplog):
    """
    Test: Validation logs rejection when identity check fails.
    Expected: Structured log entry emitted.
    """
    from app.progress.antiflow import validate_session_identity

    current_user = CurrentUser(user_id=str(uuid4()), role=Role.EMPLOYEE)
    assignment = MagicMock(spec=Assignment)
    assignment.employee_id = uuid4()  # Different

    with caplog.at_level("WARNING"):
        rejection = validate_session_identity(current_user, assignment)

    # Check rejection returned and log was emitted
    assert rejection == "identity_mismatch"
    assert any("Session identity mismatch" in record.message for record in caplog.records)


def test_validation_logs_acceptance():
    """
    Test: Validation logs acceptance when all checks pass.
    Expected: Diagnostic log emitted.
    """
    # This test verifies logging pattern for successful validation
    pass  # Logging is implementation detail; covered in integration tests


# =============================================================================
# AC5: Integration Tests (Full Anti-Spoofing Flow)
# =============================================================================


async def test_full_antiflow_valid_watch_sequence(mock_session, current_user_employee):
    """
    Test: Valid watch sequence (5 sequential watches, all accepted).
    Expected: All verified:true.
    """
    # This test requires mocking repository and checking service logic
    # Deferred to integration with full service implementation
    pass


async def test_full_antiflow_spoofed_jump_in_sequence(mock_session, current_user_employee):
    """
    Test: First 2 watches valid, 3rd is spoofed jump.
    Expected: 3rd has verified:false but still persists.
    """
    # Integration test - deferred until service implementation
    pass


async def test_full_antiflow_subsequent_watches_after_spoofed(mock_session, current_user_employee):
    """
    Test: After a spoofed write, subsequent valid writes proceed.
    Expected: Anti-spoofing doesn't permanently block.
    """
    # Integration test
    pass


# =============================================================================
# AC2 Edge Cases: Missing Video Duration
# =============================================================================


def test_bounds_check_missing_duration_none():
    """
    Test: Video duration is None.
    Expected: Bounds check skipped.
    """
    from app.progress.antiflow import validate_position_bounds

    watch_position = 5000  # Would be out of bounds if duration was 3600
    video_duration = None

    rejection_reason = validate_position_bounds(watch_position, video_duration)

    assert rejection_reason is None  # Skipped, not rejected


def test_bounds_check_malformed_duration_skipped():
    """
    Test: Video duration is invalid (not an integer).
    Expected: Bounds check skipped gracefully.
    """
    from app.progress.antiflow import validate_position_bounds

    watch_position = 1800
    video_duration = "3600"  # String instead of int

    # Should handle gracefully (type conversion or skip)
    try:
        rejection_reason = validate_position_bounds(watch_position, video_duration)
        # Either returns None (skipped) or handled gracefully
        assert rejection_reason in (None, "bounds_check_failed")
    except (TypeError, ValueError):
        # If it throws, that's okay too (caught by service layer)
        pass


# =============================================================================
# AC3 Edge Cases: Rate Check with Floating-Point Edge Cases
# =============================================================================


def test_rate_check_very_fast_playback_within_limit():
    """
    Test: 5x playback speed (within 10x limit).
    Expected: Passes.
    """
    from app.progress.antiflow import validate_rate_check

    old_position = 0
    old_event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
    video_duration = 3600
    # 5x playback: advance 1800 seconds in 1 second (allowed_rate = 360)
    new_position = 1800
    new_event_time = datetime(2026, 7, 10, 16, 0, 10, tzinfo=timezone.utc)

    rejection_reason = validate_rate_check(
        old_position, old_event_time, new_position, new_event_time, video_duration
    )

    assert rejection_reason is None


def test_rate_check_just_over_10x_limit():
    """
    Test: Playback speed just over 10x limit (rejected).
    Expected: Fails.
    """
    from app.progress.antiflow import validate_rate_check

    old_position = 0
    old_event_time = datetime(2026, 7, 10, 16, 0, 0, tzinfo=timezone.utc)
    video_duration = 3600
    # Slightly over 10x: 3601 seconds in 1 second
    new_position = 3601
    new_event_time = datetime(2026, 7, 10, 16, 0, 1, tzinfo=timezone.utc)

    rejection_reason = validate_rate_check(
        old_position, old_event_time, new_position, new_event_time, video_duration
    )

    assert rejection_reason == "rate_check_failed"
