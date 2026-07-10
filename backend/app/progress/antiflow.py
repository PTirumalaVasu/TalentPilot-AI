"""Anti-spoofing validation for watch-progress writes (Story 4-4).

This module implements server-side validation to detect and reject forged or spoofed
watch-position updates. All checks are deterministic and follow a "silent rejection"
pattern: failed checks set verified=false and persist the write for forensics, rather
than throwing errors or rejecting the request.

Validation checks (in order):
1. AC1 & AC8: Session identity tie (JWT user_id must match assignment employee_id)
2. AC2: Position bounds (0 <= position <= video_duration)
3. AC3: Rate check (position advances at reasonable playback speed, ≤10x)
4. AC4: Event-time coherence (timestamp within ±5 minutes of server time)

References:
- AD-5: Watch-progress write path (anti-spoofing + conditional-write)
- AD-6: Server-side session/role/identity gate (JWT verification)
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from app.assignments.models import Assignment
from app.auth.schemas import CurrentUser, Role

logger = logging.getLogger(__name__)

# Configuration constants (adjustable post-pilot)
CLOCK_SKEW_TOLERANCE_MINUTES = 5
RATE_MULTIPLIER_LIMIT = 10  # Allow up to 10x playback speed


def validate_session_identity(
    current_user: CurrentUser,
    assignment: Assignment,
) -> Optional[str]:
    """
    AC1 & AC8: Verify session identity matches assignment employee_id.

    Only EMPLOYEE sessions can report progress on their own assignments.
    HR_ADMIN sessions cannot report progress (must be tied to individual employee).

    Args:
        current_user: Authenticated user from JWT
        assignment: Assignment record

    Returns:
        None if validation passes, rejection reason string if fails
    """
    # HR_ADMIN cannot report progress (only employees can)
    if current_user.role == Role.HR_ADMIN:
        logger.warning(
            f"HR_ADMIN attempted to report progress for assignment {assignment.id}. "
            f"Only employees can report their own progress."
        )
        return "identity_mismatch"

    # EMPLOYEE must match assignment's employee_id
    # Note: user_id is str (from JWT), employee_id is UUID; convert to str for comparison
    if str(assignment.employee_id) != current_user.user_id:
        logger.warning(
            f"Session identity mismatch for assignment {assignment.id}: "
            f"session user_id={current_user.user_id}, assignment employee_id={assignment.employee_id}"
        )
        return "identity_mismatch"

    return None


def validate_position_bounds(
    watch_position: int,
    video_duration: Optional[int],
) -> Optional[str]:
    """
    AC2: Validate position is within valid bounds.

    Range: 0 <= watch_position <= video_duration

    If video_duration is None (no content attached), bounds check is skipped.

    Args:
        watch_position: Position in seconds (from request)
        video_duration: Video duration in seconds (from content metadata), or None

    Returns:
        None if validation passes or is skipped, rejection reason if fails
    """
    # If no video duration available, skip bounds check
    if video_duration is None:
        logger.debug(f"Skipping bounds check: video_duration not available")
        return None

    # Handle malformed duration gracefully
    try:
        duration = int(video_duration)
    except (TypeError, ValueError):
        logger.debug(f"Skipping bounds check: video_duration not an integer ({video_duration})")
        return None

    # Validate bounds: 0 <= position <= duration
    if watch_position < 0 or watch_position > duration:
        logger.warning(
            f"Position out of bounds: watch_position={watch_position}, video_duration={duration}"
        )
        return "bounds_check_failed"

    return None


def validate_rate_check(
    old_position: Optional[int],
    old_event_time: Optional[datetime],
    new_position: int,
    new_event_time: datetime,
    video_duration: Optional[int],
) -> Optional[str]:
    """
    AC3: Validate position advance rate is consistent with real playback.

    Rule: (new_position - old_position) / (new_event_time - old_event_time) ≤ (video_duration / 10) per second

    Allows:
    - Normal playback (~1x speed)
    - Faster playback (up to 10x speed)
    - Rewinds (any negative delta with newer timestamp)

    Rejects:
    - Instantaneous jumps toward 100%
    - Same timestamp with different positions (mathematically invalid)

    If no prior record exists (first watch), rate check is skipped.

    Args:
        old_position: Previous position in seconds, or None
        old_event_time: Previous event timestamp, or None
        new_position: Current position in seconds
        new_event_time: Current event timestamp
        video_duration: Video duration in seconds, or None

    Returns:
        None if validation passes or is skipped, rejection reason if fails
    """
    # If no prior record, skip rate check (first watch)
    if old_position is None or old_event_time is None:
        logger.debug(f"Skipping rate check: first watch for assignment")
        return None

    # Calculate time delta
    time_delta = (new_event_time - old_event_time).total_seconds()

    # Reject same timestamp with different position (mathematically invalid)
    if time_delta == 0:
        logger.warning(
            f"Rate check failed: same event_time with different positions. "
            f"old_position={old_position}, new_position={new_position}"
        )
        return "rate_check_failed"

    # Reject backward-time scenarios (negative time_delta is impossible)
    if time_delta < 0:
        logger.warning(
            f"Rate check failed: backward time delta. "
            f"old_event_time={old_event_time}, new_event_time={new_event_time}, "
            f"time_delta={time_delta}s"
        )
        return "rate_check_failed"

    # Calculate position advance rate (seconds per second of elapsed time)
    position_delta = new_position - old_position
    rate_per_second = position_delta / time_delta

    # Allow rewinds (negative position delta with forward time) - always pass
    if rate_per_second < 0:
        logger.debug(f"Rewind detected: position_delta={position_delta}, time_delta={time_delta}s")
        return None

    # If no video duration, skip rate check (cannot calculate threshold)
    if video_duration is None:
        logger.debug(f"Skipping rate check: video_duration not available")
        return None

    # Handle type conversion for video_duration (may be string from JSON)
    try:
        duration = int(video_duration)
    except (TypeError, ValueError):
        logger.debug(f"Skipping rate check: video_duration not an integer ({video_duration})")
        return None

    # Calculate allowed rate: video_duration / 10 per second
    allowed_rate_per_second = duration / RATE_MULTIPLIER_LIMIT

    # Reject if rate exceeds threshold
    if rate_per_second > allowed_rate_per_second:
        logger.warning(
            f"Rate check failed: playback speed too fast. "
            f"rate_per_second={rate_per_second:.1f}, allowed={allowed_rate_per_second:.1f}, "
            f"position_delta={position_delta}, time_delta={time_delta}s"
        )
        return "rate_check_failed"

    return None


def validate_event_time_coherence(
    event_time: datetime,
    server_now: Optional[datetime] = None,
) -> Optional[str]:
    """
    AC4: Validate event_time is recent (within ±5 minutes of server time).

    Tolerates client-clock skew; rejects obviously stale or impossible timestamps.

    Range: (now - 5 min) <= event_time <= now (strict: no future times)

    Args:
        event_time: Client timestamp from request
        server_now: Server time for comparison (defaults to current time)

    Returns:
        None if validation passes, rejection reason if fails
    """
    if server_now is None:
        server_now = datetime.now(timezone.utc)

    # Ensure event_time is timezone-aware (convert if naive)
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)

    # Calculate 5-minute boundaries
    cutoff_past = server_now - timedelta(minutes=CLOCK_SKEW_TOLERANCE_MINUTES)

    # Reject stale (older than 5 minutes)
    if event_time < cutoff_past:
        logger.warning(
            f"Event time stale: event_time={event_time}, cutoff_past={cutoff_past}, "
            f"minutes_old={(server_now - event_time).total_seconds() / 60:.1f}"
        )
        return "event_time_incoherent"

    # Reject future (even 1 second in future)
    if event_time > server_now:
        logger.warning(
            f"Event time in future: event_time={event_time}, server_now={server_now}, "
            f"minutes_ahead={(event_time - server_now).total_seconds() / 60:.1f}"
        )
        return "event_time_incoherent"

    return None


def run_all_validations(
    current_user: CurrentUser,
    assignment: Assignment,
    watch_position: int,
    event_time: datetime,
    old_position: Optional[int] = None,
    old_event_time: Optional[datetime] = None,
    video_duration: Optional[int] = None,
) -> bool:
    """
    AC5: Run all validation checks and determine verified flag.

    Deterministic: same input always produces same result.
    Silent rejection: failed checks set verified=false, never throw.

    Args:
        current_user: Authenticated user from JWT
        assignment: Assignment record
        watch_position: Position in seconds
        event_time: Event timestamp from client
        old_position: Previous position (for rate check), or None
        old_event_time: Previous event timestamp (for rate check), or None
        video_duration: Video duration in seconds (for bounds/rate checks), or None

    Returns:
        bool: True if all checks pass (verified=true), False if any fail (verified=false)
    """
    # Run checks in order; collect all failures for comprehensive logging
    failures = []

    # AC1 & AC8: Session identity
    rejection = validate_session_identity(current_user, assignment)
    if rejection:
        failures.append(rejection)

    # AC2: Position bounds
    rejection = validate_position_bounds(watch_position, video_duration)
    if rejection:
        failures.append(rejection)

    # AC3: Rate check
    rejection = validate_rate_check(old_position, old_event_time, watch_position, event_time, video_duration)
    if rejection:
        failures.append(rejection)

    # AC4: Event-time coherence
    rejection = validate_event_time_coherence(event_time)
    if rejection:
        failures.append(rejection)

    # Log comprehensive result
    if failures:
        logger.info(
            f"Watch progress validation failed for assignment {assignment.id}: "
            f"failures={failures}, verified=false"
        )
        return False

    logger.info(
        f"Watch progress validation passed for assignment {assignment.id}, "
        f"position={watch_position}, event_time={event_time}, verified=true"
    )
    return True
