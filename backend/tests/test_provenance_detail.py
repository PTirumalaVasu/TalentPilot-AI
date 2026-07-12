"""Unit tests for ProgressService.get_provenance_detail() (Story 5-2), the
single AR-3 authority consolidating Story 3.5's derive_dashboard_status_and_percent
and Story 5.3's derive_self_reported_provenance for both the dashboard grid
and the Provenance Drill-Down modal.

Pure function over in-memory (non-persisted) ORM objects — no DB session
needed, sidestepping the documented conftest.py pool-corruption issue
entirely (same approach as test_dashboard_progress_derivation.py /
test_needs_attention_derivation.py)."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.assignments.models import Assignment, AssignmentOverride, Employee, SkillProgress
from app.assignments.schemas import AssignmentStatus
from app.progress.service import ProgressService

NOW = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)


def _assignment(assigned_at: datetime = NOW - timedelta(days=30)) -> Assignment:
    return Assignment(id=uuid4(), employee_id=uuid4(), skill_id=uuid4(), assigned_by=uuid4(), assigned_at=assigned_at)


def test_no_progress_no_override_is_not_started():
    assignment = _assignment(assigned_at=NOW - timedelta(days=3))
    detail = ProgressService.get_provenance_detail(assignment, None, None, video_duration=None, now=NOW)

    assert detail.provenance == "Not Started"
    assert detail.status == AssignmentStatus.NOT_STARTED
    assert detail.percentage == 0
    assert detail.last_updated == assignment.assigned_at
    assert detail.underlying_signal is None


def test_verified_progress_is_verified_branch():
    assignment = _assignment()
    progress = SkillProgress(
        id=uuid4(), assignment_id=assignment.id, watch_position=150, event_time=NOW, verified=True, updated_at=NOW
    )
    detail = ProgressService.get_provenance_detail(assignment, progress, None, video_duration=300, now=NOW)

    assert detail.provenance == "Verified"
    assert detail.status == AssignmentStatus.IN_PROGRESS
    assert detail.percentage == 50
    assert detail.last_updated == NOW


def test_unverified_recent_progress_is_self_reported():
    assignment = _assignment()
    progress = SkillProgress(
        id=uuid4(),
        assignment_id=assignment.id,
        watch_position=100,
        event_time=NOW - timedelta(days=2),
        verified=False,
        updated_at=NOW - timedelta(days=2),
    )
    detail = ProgressService.get_provenance_detail(assignment, progress, None, video_duration=None, now=NOW)

    assert detail.provenance == "Self-reported"
    assert detail.status == AssignmentStatus.IN_PROGRESS


def test_clock_skewed_event_time_falls_back_to_self_reported_instead_of_raising():
    """Code review regression (Story 5-2): derive_self_reported_provenance()
    deliberately raises ValueError on a future (clock-skew) event_time -- fine
    when it had zero callers, but get_provenance_detail() now calls it from two
    live endpoints. Must degrade gracefully, not 500 the whole request."""
    assignment = _assignment()
    progress = SkillProgress(
        id=uuid4(),
        assignment_id=assignment.id,
        watch_position=100,
        event_time=NOW + timedelta(hours=1),  # future relative to `now=NOW` below
        verified=False,
        updated_at=NOW,
    )
    detail = ProgressService.get_provenance_detail(assignment, progress, None, video_duration=None, now=NOW)

    assert detail.provenance == "Self-reported"
    assert detail.status == AssignmentStatus.IN_PROGRESS


def test_unverified_stale_progress_is_needs_attention():
    assignment = _assignment()
    progress = SkillProgress(
        id=uuid4(),
        assignment_id=assignment.id,
        watch_position=100,
        event_time=NOW - timedelta(days=14),
        verified=False,
        updated_at=NOW - timedelta(days=14),
    )
    detail = ProgressService.get_provenance_detail(assignment, progress, None, video_duration=None, now=NOW)

    assert detail.provenance == "Needs Attention"


def test_unknown_duration_never_reports_completed():
    """Deliberate consolidation fix: no assumed 3600s fallback anymore --
    unknown duration must stay indeterminate (0%), never fabricate Completed."""
    assignment = _assignment()
    progress = SkillProgress(
        id=uuid4(), assignment_id=assignment.id, watch_position=5000, event_time=NOW, verified=True, updated_at=NOW
    )
    detail = ProgressService.get_provenance_detail(assignment, progress, None, video_duration=None, now=NOW)

    assert detail.status == AssignmentStatus.IN_PROGRESS
    assert detail.percentage == 0


def test_active_override_takes_precedence_and_preserves_underlying_verified_signal():
    assignment = _assignment()
    progress = SkillProgress(
        id=uuid4(), assignment_id=assignment.id, watch_position=150, event_time=NOW, verified=True, updated_at=NOW
    )
    hr_admin = Employee(id=uuid4(), name="Rita Martinez", email="rita@sails.example.com", role="HR_ADMIN")
    override = AssignmentOverride(
        id=uuid4(),
        assignment_id=assignment.id,
        set_by=hr_admin.id,
        set_at=NOW,
        reason="Verified in conversation",
        active=True,
        override_status="COMPLETED",
    )
    override.set_by_user = hr_admin

    detail = ProgressService.get_provenance_detail(assignment, progress, override, video_duration=300, now=NOW)

    assert detail.provenance == "HR Override"
    assert detail.status == AssignmentStatus.COMPLETED
    assert detail.percentage is None
    assert detail.last_updated == NOW
    assert detail.override_set_by_name == "Rita Martinez"
    assert detail.override_reason == "Verified in conversation"
    assert detail.override_set_at == NOW

    assert detail.underlying_signal is not None
    assert detail.underlying_signal.provenance == "Verified"
    assert detail.underlying_signal.status == AssignmentStatus.IN_PROGRESS
    assert detail.underlying_signal.percentage == 50


def test_active_override_with_no_underlying_signal_at_all():
    assignment = _assignment(assigned_at=NOW - timedelta(days=1))
    hr_admin = Employee(id=uuid4(), name="Rita Martinez", email="rita@sails.example.com", role="HR_ADMIN")
    override = AssignmentOverride(
        id=uuid4(),
        assignment_id=assignment.id,
        set_by=hr_admin.id,
        set_at=NOW,
        reason=None,
        active=True,
        override_status="COMPLETED",
    )
    override.set_by_user = hr_admin

    detail = ProgressService.get_provenance_detail(assignment, None, override, video_duration=None, now=NOW)

    assert detail.provenance == "HR Override"
    assert detail.override_reason is None
    assert detail.underlying_signal.provenance == "Not Started"


def test_inactive_override_is_ignored():
    assignment = _assignment(assigned_at=NOW - timedelta(days=1))
    hr_admin = Employee(id=uuid4(), name="Rita Martinez", email="rita@sails.example.com", role="HR_ADMIN")
    override = AssignmentOverride(
        id=uuid4(),
        assignment_id=assignment.id,
        set_by=hr_admin.id,
        set_at=NOW,
        active=False,
        override_status="COMPLETED",
        reversed_at=NOW,
        reversed_by=hr_admin.id,
    )
    override.set_by_user = hr_admin

    detail = ProgressService.get_provenance_detail(assignment, None, override, video_duration=None, now=NOW)

    assert detail.provenance == "Not Started"
    assert detail.underlying_signal is None
