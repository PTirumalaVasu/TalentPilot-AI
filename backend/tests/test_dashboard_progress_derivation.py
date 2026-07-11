"""Unit tests for ProgressService.derive_dashboard_status_and_percent() (Story 3.5
dashboard expansion) — a pure function, no DB access, so plain pytest (no
asyncio/live-DB machinery needed unlike this project's other progress tests."""
from app.assignments.schemas import AssignmentStatus
from app.progress.service import ProgressService


def test_no_progress_yet_is_not_started_zero_percent():
    status, percent = ProgressService.derive_dashboard_status_and_percent(0, None)
    assert status == AssignmentStatus.NOT_STARTED
    assert percent == 0


def test_partial_watch_is_in_progress_with_correct_percent():
    status, percent = ProgressService.derive_dashboard_status_and_percent(150, 300)
    assert status == AssignmentStatus.IN_PROGRESS
    assert percent == 50


def test_full_watch_is_completed_100_percent():
    status, percent = ProgressService.derive_dashboard_status_and_percent(300, 300)
    assert status == AssignmentStatus.COMPLETED
    assert percent == 100


def test_percent_is_clamped_at_100_even_if_watch_position_overshoots():
    """watch_position can slightly exceed duration in practice (e.g. rounding
    in the client's periodic-post interval) — must never report >100%."""
    status, percent = ProgressService.derive_dashboard_status_and_percent(310, 300)
    assert status == AssignmentStatus.COMPLETED
    assert percent == 100


def test_percent_rounds_to_nearest_whole_number():
    status, percent = ProgressService.derive_dashboard_status_and_percent(100, 300)
    assert status == AssignmentStatus.IN_PROGRESS
    assert percent == 33  # 33.33...% rounds to 33


def test_zero_watch_position_with_known_duration_is_not_started():
    status, percent = ProgressService.derive_dashboard_status_and_percent(0, 300)
    assert status == AssignmentStatus.NOT_STARTED
    assert percent == 0


def test_no_duration_but_nonzero_watch_position_is_in_progress_zero_percent():
    """Content with no duration metadata (or no content linked) can't produce
    a meaningful percentage, but a nonzero watch_position still means
    something happened — report In Progress with an indeterminate 0%
    rather than silently misreporting Not Started."""
    status, percent = ProgressService.derive_dashboard_status_and_percent(45, None)
    assert status == AssignmentStatus.IN_PROGRESS
    assert percent == 0


def test_zero_duration_is_treated_like_missing_duration():
    status, percent = ProgressService.derive_dashboard_status_and_percent(0, 0)
    assert status == AssignmentStatus.NOT_STARTED
    assert percent == 0


def test_iso8601_duration_string_from_real_youtube_ingestion_does_not_crash():
    """Regression: real content_catalog rows from Story 2.3's YouTube
    ingestion store `duration` as an ISO-8601 string (e.g. "PT10M0S"), not
    seconds-as-int like manually-seeded content does — confirmed by
    inspecting the actual dev DB. Must degrade to "unknown duration"
    (same as None), not raise a TypeError comparing str to int."""
    status, percent = ProgressService.derive_dashboard_status_and_percent(45, "PT10M0S")
    assert status == AssignmentStatus.IN_PROGRESS
    assert percent == 0


def test_numeric_string_duration_is_coerced_to_int():
    """A duration stored as `"300"` (string) rather than `300` (int) should
    still compute a real percentage, not fall back to unknown."""
    status, percent = ProgressService.derive_dashboard_status_and_percent(150, "300")
    assert status == AssignmentStatus.IN_PROGRESS
    assert percent == 50
