"""Service layer for the progress module. Cross-module callers must go through here (AD-1)."""
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import Assignment
from app.assignments.schemas import AssignmentStatus, ProvenanceLabel
from app.auth.schemas import CurrentUser
from app.progress.antiflow import run_all_validations
from app.progress.models import SkillProgress
from app.progress.repository import ProgressRepository
from app.progress.schemas import SkillProgressResponse, SkillProgressResponseResume

logger = logging.getLogger(__name__)

# Story 5.3: locked PRD value (project-context.md — "sourced from the
# original design-thinking success-metric proposal, not invented during PRD
# authoring"). Module-level constant, not a Settings/.env field, mirroring
# content/repository.py's SIMILARITY_THRESHOLD precedent (Story 2.4) — this
# threshold has no legitimate per-environment override case.
NEEDS_ATTENTION_STALENESS_DAYS = 7


class ProgressService:
    """Service layer for watch progress business logic."""

    @staticmethod
    async def record_watch_progress(
        session: AsyncSession,
        assignment_id: UUID,
        watch_position: int,
        event_time: datetime,
        current_user: CurrentUser,
        assignment: Assignment,
        video_duration: int | None = None,
    ) -> SkillProgressResponse:
        """
        Record or update watch progress with server-side anti-spoofing validation.

        **AC1-AC5 (Story 4-4): Anti-spoofing validation runs here BEFORE repository write.**

        Flow:
        1. Fetch previous progress record (for rate check baseline)
        2. Run all anti-spoofing validation checks (AC1-AC4)
        3. Compute verified flag based on validation results
        4. Delegate to repository for atomic conditional-write (Story 4-1 logic)
        5. Commit and return response

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment
            watch_position: Position in seconds
            event_time: ISO-8601 timestamp when position was observed (client time)
            current_user: Authenticated user from JWT (for identity verification)
            assignment: Assignment record (for employee_id and content metadata)
            video_duration: Video duration in seconds (for bounds/rate checks), or None

        Returns:
            SkillProgressResponse: The persisted (or updated) progress record
        """
        # Fetch previous progress BEFORE validation (for rate check baseline)
        # This avoids a race condition where concurrent updates would invalidate the baseline
        previous_progress = await ProgressRepository.get_progress_for_assignment(session, assignment_id)
        old_position = previous_progress.watch_position if previous_progress else None
        old_event_time = previous_progress.event_time if previous_progress else None

        # AC1-AC5: Run all anti-spoofing validation checks
        verified = run_all_validations(
            current_user=current_user,
            assignment=assignment,
            watch_position=watch_position,
            event_time=event_time,
            old_position=old_position,
            old_event_time=old_event_time,
            video_duration=video_duration,
        )

        # Use atomic initialize-or-update: creates new record on first call, updates with conditional write on subsequent calls
        # Pass previous_progress to avoid redundant query
        progress = await ProgressRepository.initialize_or_update(
            session, assignment_id, watch_position, event_time, verified, existing=previous_progress
        )
        await session.commit()
        return SkillProgressResponse.model_validate(progress)

    @staticmethod
    async def get_progress(session: AsyncSession, assignment_id: UUID) -> SkillProgressResponse | None:
        """
        Retrieve watch progress for an assignment.

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment

        Returns:
            SkillProgressResponse if found, None if no progress recorded yet
        """
        progress = await ProgressRepository.get_progress_for_assignment(session, assignment_id)
        if progress is None:
            return None
        return SkillProgressResponse.model_validate(progress)

    @staticmethod
    async def get_resume_position(
        session: AsyncSession,
        current_user: CurrentUser,
        assignment_id: UUID,
    ) -> SkillProgressResponseResume:
        """
        Retrieve watch position for resume, with hard-scoping to authenticated session identity.

        **Story 4-5: Resume Position Retrieval & Exact-Point Playback**

        This method enforces hard-scoping at the repository layer (AD-6) and handles edge cases:
        - First view (no skill_progress row): returns position 0
        - Out-of-bounds position (corrupted data): returns 0 as fallback
        - Missing video duration: skips bounds validation, returns as-is

        Args:
            session: AsyncSession for database operations
            current_user: Authenticated user from JWT (for hard-scoping identity check)
            assignment_id: UUID of the assignment

        Returns:
            SkillProgressResponseResume with position (0 if first view or out-of-bounds)

        Raises:
            HTTPException with 403 Forbidden: If assignment does not exist or user cannot access it
        """
        # Fetch assignment and progress in one query (optimized LEFT JOIN for 50% latency gain)
        # CRITICAL: Convert string user_id to UUID for type safety (AD-6 compliance)
        assignment, progress = await ProgressRepository.get_assignment_with_scope(
            session, assignment_id, UUID(current_user.user_id)
        )
        if not assignment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this assignment")

        # If no progress recorded yet (first view): return 0, null event_time
        if progress is None:
            return SkillProgressResponseResume(
                id=None,
                assignment_id=assignment_id,
                watch_position=0,
                event_time=None,
                verified=False,
                updated_at=None,
            )

        # Validate bounds (out-of-bounds fallback): if stored position > video_duration, return 0
        video_duration = ProgressRepository.get_video_duration(assignment)

        if video_duration and progress.watch_position > video_duration:
            logger.warning(
                f"Resume position out of bounds: assignment={assignment_id}, "
                f"stored_position={progress.watch_position}, video_duration={video_duration}. "
                f"Falling back to position 0."
            )
            return SkillProgressResponseResume(
                id=progress.id,
                assignment_id=progress.assignment_id,
                watch_position=0,
                event_time=progress.event_time,
                verified=progress.verified,
                updated_at=progress.updated_at,
            )

        # Return stored position (exact, no approximation)
        return SkillProgressResponseResume.model_validate(progress)

    @staticmethod
    def derive_dashboard_status_and_percent(
        watch_seconds: int, duration_seconds: object | None
    ) -> tuple[AssignmentStatus, int]:
        """Pure Status/percent derivation for the HR dashboard list (Story 3.5's
        dashboard expansion, AD-3: `progress/` is the sole derivation
        authority). No DB access — callers pass in a `SkillProgress.watch_position`
        (0 if no progress row exists yet) and the linked content's duration
        (via `ProgressRepository.get_video_duration`, None if no content or no
        duration metadata).

        - No duration known: 0 watch → Not Started; any watch → In Progress
          at an indeterminate 0% (no total to compute a percentage against).
        - Known duration: percent = watch/duration, clamped to [0, 100].
          100% → Completed, >0% → In Progress, 0% → Not Started.

        `duration_seconds` is typed loosely (not `int | None`) on purpose:
        `content_metadata` is a raw, unvalidated JSON column, and real rows
        in this dev DB (Story 2.3's YouTube ingestion) store `duration` as
        an ISO-8601 string (e.g. `"PT10M0S"`), not seconds-as-int like
        manually-seeded content does — a pre-existing shape inconsistency
        already flagged in deferred-work.md, not something to silently
        assume away. Anything that isn't cleanly int-coercible (including
        ISO-8601 strings — not parsed here, that's separate follow-up work)
        is treated as an unknown duration rather than raising.
        """
        try:
            duration_seconds = int(duration_seconds) if duration_seconds is not None else None
        except (TypeError, ValueError):
            duration_seconds = None

        if not duration_seconds or duration_seconds <= 0:
            status = AssignmentStatus.IN_PROGRESS if watch_seconds > 0 else AssignmentStatus.NOT_STARTED
            return (status, 0)

        percent = min(100, round((watch_seconds / duration_seconds) * 100))
        if percent >= 100:
            return (AssignmentStatus.COMPLETED, 100)
        if percent > 0:
            return (AssignmentStatus.IN_PROGRESS, percent)
        return (AssignmentStatus.NOT_STARTED, 0)

    @staticmethod
    def derive_self_reported_provenance(
        last_update: datetime | None, *, now: datetime | None = None
    ) -> ProvenanceLabel:
        """Pure Provenance derivation for self-reported (non-video) signals
        only (Story 5.3, AR-3: `progress/` is the sole derivation authority).
        Sibling to `derive_dashboard_status_and_percent` (Story 3.5) — same
        "pure function, no DB access, caller passes in already-fetched
        values" pattern. Verified/video rows never call this; that axis is
        Story 5.2's job.

        `last_update` is the self-report's last-update timestamp (None if no
        self-report record exists at all — e.g. an assignment with no video
        progress and no self-report either). Must be timezone-aware (AR-10
        mandates UTC specifically, but this function only enforces
        tzinfo-not-None — Python's datetime subtraction already normalizes
        any timezone-aware offset correctly, so a non-UTC-but-aware value
        still compares correctly; it is simply outside this function's
        documented input contract). A naive datetime raises rather than
        silently miscomparing.

        `now` is injectable for deterministic tests, defaulting to the real
        current UTC time in production use; if passed explicitly it must
        also be timezone-aware, for the same reason as `last_update`.

        `last_update` after `now` (clock skew, forged/corrupt data) raises
        rather than silently treating negative elapsed time as fresh.

        Per AC1's literal wording ("> 7 days"), the threshold is a strict
        inequality: exactly `NEEDS_ATTENTION_STALENESS_DAYS` days old is
        still SELF_REPORTED, not yet NEEDS_ATTENTION.
        """
        if last_update is None:
            return ProvenanceLabel.NOT_STARTED

        if last_update.tzinfo is None:
            raise ValueError(
                "derive_self_reported_provenance() requires a timezone-aware "
                "last_update (AR-10: all timestamps are ISO-8601 UTC); got a "
                "naive datetime"
            )

        if now is not None and now.tzinfo is None:
            raise ValueError(
                "derive_self_reported_provenance() requires a timezone-aware "
                "'now' when explicitly passed (AR-10: all timestamps are "
                "ISO-8601 UTC); got a naive datetime"
            )

        now = now if now is not None else datetime.now(timezone.utc)

        if last_update > now:
            raise ValueError(
                "derive_self_reported_provenance() received a last_update "
                f"({last_update.isoformat()}) after 'now' ({now.isoformat()}) "
                "— clock skew or corrupt data, not a valid staleness input"
            )

        if (now - last_update) > timedelta(days=NEEDS_ATTENTION_STALENESS_DAYS):
            return ProvenanceLabel.NEEDS_ATTENTION
        return ProvenanceLabel.SELF_REPORTED
