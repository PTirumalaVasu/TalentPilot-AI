"""Unit tests for Story 5.3's Needs Attention / self-reported staleness
derivation — a pure function, no DB access (same reasoning as Story 3.5's
test_dashboard_progress_derivation.py), so plain pytest with hand-built
datetime values, no asyncio/live-DB machinery needed."""
from datetime import datetime, timedelta, timezone

import pytest

from app.assignments.schemas import ProvenanceLabel
from app.progress.service import NEEDS_ATTENTION_STALENESS_DAYS, ProgressService

NOW = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)


def test_threshold_constant_is_locked_at_seven_days():
    """Guards against an accidental future edit silently changing the
    PRD-locked 7-day value (project-context.md: "Needs-Attention staleness
    threshold locked at 7 days") — same reasoning as Story 3.2's
    _EXPECTED_SKILL_NAMES regression-guard pattern."""
    assert NEEDS_ATTENTION_STALENESS_DAYS == 7


def test_no_signal_at_all_is_not_started():
    result = ProgressService.derive_self_reported_provenance(None, now=NOW)
    assert result == ProvenanceLabel.NOT_STARTED


def test_just_reported_is_self_reported():
    result = ProgressService.derive_self_reported_provenance(NOW, now=NOW)
    assert result == ProvenanceLabel.SELF_REPORTED


def test_six_days_stale_is_still_self_reported():
    last_update = NOW - timedelta(days=6)
    result = ProgressService.derive_self_reported_provenance(last_update, now=NOW)
    assert result == ProvenanceLabel.SELF_REPORTED


def test_exactly_seven_days_stale_is_still_self_reported():
    """AC1's threshold is a strict '> 7 days', not '>= 7 days' — the
    boundary itself must not flip to Needs Attention."""
    last_update = NOW - timedelta(days=7)
    result = ProgressService.derive_self_reported_provenance(last_update, now=NOW)
    assert result == ProvenanceLabel.SELF_REPORTED


def test_seven_days_and_one_second_stale_is_needs_attention():
    last_update = NOW - timedelta(days=7, seconds=1)
    result = ProgressService.derive_self_reported_provenance(last_update, now=NOW)
    assert result == ProvenanceLabel.NEEDS_ATTENTION


def test_thirty_days_stale_is_needs_attention():
    last_update = NOW - timedelta(days=30)
    result = ProgressService.derive_self_reported_provenance(last_update, now=NOW)
    assert result == ProvenanceLabel.NEEDS_ATTENTION


def test_naive_datetime_input_raises_instead_of_silently_miscomparing():
    """AR-10: all timestamps are ISO-8601 UTC. A naive datetime slipping in
    (e.g. from an un-normalized DB read) must fail loudly, not produce a
    wrong staleness comparison. Narrowed to the specific ValueError the
    implementation actually raises (code review, 2026-07-11) — a prior
    version of this test accepted (ValueError, TypeError), which would not
    have caught a regression that let a raw TypeError leak through instead
    of the intended, friendlier, AR-10-branded message."""
    naive_last_update = datetime(2026, 7, 1, 12, 0, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        ProgressService.derive_self_reported_provenance(naive_last_update, now=NOW)


def test_naive_now_input_raises_when_explicitly_passed():
    """Code review, 2026-07-11: `now` previously had no equivalent guard to
    `last_update`'s naive-datetime check — a naive `now` passed alongside an
    aware `last_update` used to surface a raw, unguarded TypeError from the
    subtraction itself instead of this function's own friendly ValueError."""
    naive_now = datetime(2026, 7, 11, 12, 0, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        ProgressService.derive_self_reported_provenance(NOW, now=naive_now)


def test_now_defaults_to_current_utc_time_when_not_passed():
    """`now` is injectable for deterministic tests but must default to a
    real current UTC timestamp in production use, not a fixed/frozen value.
    Strengthened (code review, 2026-07-11): the prior version used a
    `last_update` only 1 second stale, which a badly-broken hardcoded-past
    default would also (wrongly) classify as SELF_REPORTED via a negative
    delta, silently passing either way. This version anchors `last_update`
    9 days before the *real* wall clock (not the module-level NOW fixture)
    and asserts NEEDS_ATTENTION — a broken default would instead make
    last_update appear to be in the future relative to it, which now raises
    (see test_last_update_after_now_raises below) rather than passing."""
    stale_relative_to_real_now = datetime.now(timezone.utc) - timedelta(days=9)
    result = ProgressService.derive_self_reported_provenance(stale_relative_to_real_now)
    assert result == ProvenanceLabel.NEEDS_ATTENTION


def test_last_update_after_now_raises():
    """Code review, 2026-07-11: a `last_update` after `now` (clock skew,
    forged/corrupt data) previously produced a negative elapsed time that
    silently compared as SELF_REPORTED rather than being flagged as invalid
    input — matches this project's established precedent of rejecting
    future timestamps at similar validation points (Story 4.4's antiflow
    `event_time_future_rejected`)."""
    future_last_update = NOW + timedelta(seconds=1)
    with pytest.raises(ValueError, match="after 'now'"):
        ProgressService.derive_self_reported_provenance(future_last_update, now=NOW)


def test_never_returns_verified_or_hr_override():
    """AC3: this derivation is exclusively a self-reported-data concern —
    Verified (video) and HR Override are derived elsewhere (Story 5.2/5.5),
    never by this function. Confirmed by enumerating every reachable input
    class and asserting the return value is always one of the 3 members
    this story actually defines."""
    reachable_results = {
        ProgressService.derive_self_reported_provenance(None, now=NOW),
        ProgressService.derive_self_reported_provenance(NOW, now=NOW),
        ProgressService.derive_self_reported_provenance(NOW - timedelta(days=8), now=NOW),
    }
    assert reachable_results <= {
        ProvenanceLabel.NOT_STARTED,
        ProvenanceLabel.SELF_REPORTED,
        ProvenanceLabel.NEEDS_ATTENTION,
    }
