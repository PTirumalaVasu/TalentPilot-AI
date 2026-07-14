"""Repository layer for the progress module. Only this module's own code may query its tables."""
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.assignments.models import Assignment, AssignmentOverride, SkillProgress

logger = logging.getLogger(__name__)

_ISO8601_DURATION_RE = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


class ProgressRepository:
    """Repository for skill_progress table operations."""

    @staticmethod
    async def record_watch_progress(
        session: AsyncSession,
        assignment_id: UUID,
        watch_position: int,
        event_time: datetime,
        verified: bool,
    ) -> SkillProgress:
        """
        Record watch progress with event-time-ordered conditional write.

        **Atomic SQL UPDATE with WHERE clause on event_time prevents stale writes.**

        If a progress record exists and incoming event_time <= stored event_time, the write is skipped.
        If incoming event_time > stored event_time, the record is updated (new event is newer).

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment
            watch_position: Position in seconds
            event_time: ISO-8601 timestamp when position was observed (client time)
            verified: True if passed server-side anti-spoofing checks

        Returns:
            SkillProgress: The current/newly created progress record
        """
        # Use atomic SQL UPDATE with WHERE on event_time for conditional write
        # This prevents stale out-of-order writes from regressing progress
        result = await session.execute(
            text("""
                UPDATE skill_progress
                SET watch_position = :position,
                    event_time = :event_time,
                    updated_at = NOW(),
                    verified = :verified
                WHERE assignment_id = :assignment_id
                  AND (event_time IS NULL OR event_time < :event_time)
                RETURNING id, assignment_id, watch_position, event_time, verified, updated_at
            """),
            {
                "position": watch_position,
                "event_time": event_time,
                "verified": verified,
                "assignment_id": assignment_id,
            },
        )
        row = result.mappings().first()

        if row:
            # Newer write accepted
            logger.debug(
                f"Updated skill_progress for {assignment_id}: position={watch_position}, "
                f"event_time={event_time}, verified={verified}"
            )
            return SkillProgress(**row)
        else:
            # Stale write detected (0 rows affected)
            logger.debug(
                f"Skipped stale write for {assignment_id}: incoming_event_time={event_time} "
                f"(stored event_time is newer or equal)"
            )
            # Fetch and return current stored record (may be None if called on first write)
            current = await session.execute(
                select(SkillProgress).where(SkillProgress.assignment_id == assignment_id)
            )
            stored = current.scalar_one_or_none()
            if stored is None:
                # Race condition: record was deleted between stale-write check and fetch.
                # Create new record as fallback (idempotent).
                return await ProgressRepository.create_watch_progress(
                    session, assignment_id, watch_position, event_time, verified
                )
            return stored

    @staticmethod
    async def create_watch_progress(
        session: AsyncSession,
        assignment_id: UUID,
        watch_position: int,
        event_time: datetime,
        verified: bool,
    ) -> SkillProgress:
        """
        Create a new watch progress record (first watch for an assignment).

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment
            watch_position: Position in seconds
            event_time: ISO-8601 timestamp when position was observed (client time)
            verified: True if passed server-side anti-spoofing checks

        Returns:
            SkillProgress: The newly created progress record
        """
        progress = SkillProgress(
            id=uuid4(),
            assignment_id=assignment_id,
            watch_position=watch_position,
            event_time=event_time,
            verified=verified,
            updated_at=datetime.now(timezone.utc),
        )
        session.add(progress)
        await session.flush()
        logger.debug(f"Created new skill_progress for {assignment_id}: position={watch_position}")
        return progress

    @staticmethod
    async def get_progress_for_assignment(session: AsyncSession, assignment_id: UUID) -> SkillProgress | None:
        """
        Retrieve watch progress for an assignment.

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment

        Returns:
            SkillProgress if found, None if no progress recorded yet
        """
        result = await session.execute(
            select(SkillProgress).where(SkillProgress.assignment_id == assignment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def initialize_or_update(
        session: AsyncSession,
        assignment_id: UUID,
        watch_position: int,
        event_time: datetime,
        verified: bool,
        existing: Optional[SkillProgress] = None,
    ) -> SkillProgress:
        """
        Initialize a new progress record OR update if stale write scenario applies.

        This is a convenience wrapper that handles both creation and conditional update cases.

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment
            watch_position: Position in seconds
            event_time: ISO-8601 timestamp when position was observed (client time)
            verified: True if passed server-side anti-spoofing checks
            existing: Optional pre-fetched progress record (avoids redundant query if provided)

        Returns:
            SkillProgress: The created or updated progress record
        """
        if existing is None:
            existing = await ProgressRepository.get_progress_for_assignment(session, assignment_id)

        if existing is None:
            return await ProgressRepository.create_watch_progress(
                session, assignment_id, watch_position, event_time, verified
            )
        else:
            return await ProgressRepository.record_watch_progress(
                session, assignment_id, watch_position, event_time, verified
            )

    @staticmethod
    def parse_duration_seconds(duration_raw: object | None) -> int | None:
        """Best-effort parse of a Content row's raw `duration` metadata value
        into whole seconds -- the single derivation authority for this
        (AD-3), since every caller that needs a numeric duration (dashboard
        percentage, resume-position bounds, anti-spoofing bounds/rate checks,
        employee Content Discovery grid) must agree on the same parsing or
        silently diverge, which is exactly the drift this centralizes.

        Real YouTube-ingested content (Story 2.3) stores an ISO-8601 duration
        string (e.g. "PT4H20M39S"); some manually-seeded rows store a plain
        int, or an int-as-string, instead -- both are accepted. Anything that
        matches neither shape returns None rather than raising: a video with
        an unknown/malformed duration simply can't derive a percentage or a
        COMPLETED status, it never blocks the read.
        """
        if duration_raw is None:
            return None
        if isinstance(duration_raw, str):
            match = _ISO8601_DURATION_RE.match(duration_raw)
            if match:
                hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
                return hours * 3600 + minutes * 60 + seconds
        try:
            return int(duration_raw)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_video_duration(assignment: Assignment) -> int | None:
        """
        Extract video duration (in seconds) from assignment content metadata
        (DRY helper).

        Args:
            assignment: Assignment with eager-loaded content

        Returns:
            Video duration in seconds, or None if not available
        """
        if assignment.content and assignment.content.content_metadata:
            return ProgressRepository.parse_duration_seconds(assignment.content.content_metadata.get("duration"))
        return None

    @staticmethod
    def _build_assignment_query(assignment_id: UUID, employee_id: UUID | None = None) -> select:
        """
        Build a base assignment query with eager loading (DRY pattern for shared query construction).

        Args:
            assignment_id: UUID of the assignment
            employee_id: Optional UUID for hard-scoping to employee (AD-6)

        Returns:
            SQLAlchemy select statement with eager loading of content and skill

        Excludes soft-deleted assignments (Story 3.7 code review, decision-needed
        finding 1) -- without this, an Employee's already-open video page (SPA, no
        reload) could keep writing/reading watch progress against an assignment HR
        already deleted, contradicting FR-15's "disappears everywhere" intent.
        Callers already treat a None/not-found result as 404 (get_assignment_for_progress)
        so this is a safe, already-handled path, not a new error case.
        """
        stmt = (
            select(Assignment)
            .where(Assignment.id == assignment_id, Assignment.active.is_(True))
            .options(joinedload(Assignment.content), joinedload(Assignment.skill))
        )
        if employee_id is not None:
            stmt = stmt.where(Assignment.employee_id == employee_id)
        return stmt

    @staticmethod
    async def get_assignment_for_progress(session: AsyncSession, assignment_id: UUID) -> Assignment | None:
        """
        Retrieve assignment with content metadata (for anti-spoofing validation).

        Fetches assignment with eager-loaded content and skill relationships.

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment

        Returns:
            Assignment with content and skill loaded, or None if not found
        """
        result = await session.execute(ProgressRepository._build_assignment_query(assignment_id))
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_assignment_with_scope(
        session: AsyncSession, assignment_id: UUID, employee_id: UUID
    ) -> tuple[Assignment | None, SkillProgress | None]:
        """
        Retrieve assignment (hard-scoped) and progress in one LEFT JOIN query (Story 4-5 optimization).

        **Story 4-5: Resume Position Retrieval & Exact-Point Playback**

        Hard-scoping enforced at the repository layer ensures that even if a client attempts
        to override or bypass the identity check (e.g., via request body), the query itself
        contains the WHERE clause limiting results to the authenticated session's identity.

        Combines two queries into one LEFT JOIN for 50% latency improvement on hot path.

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment
            employee_id: UUID of the employee (from authenticated session, never from request body)

        Returns:
            Tuple of (Assignment, SkillProgress) where progress may be None if no watch history.
            Returns (None, None) if assignment not found, identity mismatch, or soft-deleted.

        Excludes soft-deleted assignments (Story 3.7 code review, decision-needed
        finding 1) -- see _build_assignment_query's docstring for the reasoning;
        the caller (ProgressService.get_resume_position) already treats a None
        assignment as 403, so this is a safe, already-handled path.
        """
        result = await session.execute(
            select(Assignment, SkillProgress)
            .where(
                Assignment.id == assignment_id,
                Assignment.employee_id == employee_id,
                Assignment.active.is_(True),
            )
            .outerjoin(SkillProgress, Assignment.id == SkillProgress.assignment_id)
            .options(joinedload(Assignment.content), joinedload(Assignment.skill))
        )
        row = result.unique().first()
        if row is None:
            return None, None
        return row[0], row[1]

    @staticmethod
    async def _get_assignment_by_id(
        session: AsyncSession, assignment_id: UUID, employee_id: UUID | None = None
    ) -> Assignment | None:
        """
        Helper: Retrieve assignment with optional hard-scoping (DRY pattern).

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment
            employee_id: Optional UUID for hard-scoping to employee (AD-6)

        Returns:
            Assignment with content and skill loaded, or None if not found or identity mismatch
        """
        result = await session.execute(
            ProgressRepository._build_assignment_query(assignment_id, employee_id)
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def acquire_override_lock(session: AsyncSession, assignment_id: UUID) -> None:
        """Serializes concurrent `set_override` calls for the same assignment
        (Story 5.5 code review finding: the read-active -> deactivate -> create
        sequence has no DB-level guard, so two concurrent "set" calls with no
        currently-active override can both insert, violating AC9's
        at-most-one-active-override invariant). A row-level `SELECT ... FOR
        UPDATE` can't help here since there is nothing to lock when zero
        overrides are active yet -- a Postgres transaction-scoped advisory
        lock keyed on the assignment_id works from a cold start too, and is
        auto-released on commit/rollback, so it needs no schema change and no
        explicit unlock call. Call this before the read-then-write sequence,
        never on a read-only path (get_drill_down_service) where the extra
        serialization would be pure overhead.
        """
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:assignment_id))"),
            {"assignment_id": str(assignment_id)},
        )

    @staticmethod
    async def get_active_override_for_assignment(
        session: AsyncSession, assignment_id: UUID
    ) -> AssignmentOverride | None:
        """
        Fetch the active HR override for an assignment, if any (AD-4).

        Returns the most recent active override record where active=true.

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment

        Returns:
            AssignmentOverride if active override exists, None otherwise
        """
        result = await session.execute(
            select(AssignmentOverride)
            .where(AssignmentOverride.assignment_id == assignment_id, AssignmentOverride.active == True)
            .order_by(AssignmentOverride.set_at.desc())
            .limit(1)
            .options(joinedload(AssignmentOverride.set_by_user))
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def create_override(
        session: AsyncSession, *, assignment_id: UUID, set_by: UUID, reason: str | None
    ) -> AssignmentOverride:
        """
        Create a new HR Override record (Story 5.5, AC3/AD-4). Never touches
        skill_progress -- a separate, coexisting record. override_status
        always defaults to "COMPLETED": the request contract has no field for
        HR to pick a different override status (epics.md's
        `{action: 'set', reason?}`).

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment being overridden
            set_by: UUID of the HR Admin creating the override (from the
                authenticated session, never the request body)
            reason: Optional, already-trimmed reason (None if not provided or blank)

        Returns:
            AssignmentOverride: The newly created, active override record
        """
        override = AssignmentOverride(
            id=uuid4(),
            assignment_id=assignment_id,
            set_by=set_by,
            set_at=datetime.now(timezone.utc),
            reason=reason,
            active=True,
            override_status="COMPLETED",
        )
        session.add(override)
        await session.flush()
        logger.debug(f"Created assignment_overrides row for {assignment_id}: set_by={set_by}")
        return override

    @staticmethod
    async def deactivate_override(
        session: AsyncSession, override: AssignmentOverride, *, reversed_by: UUID
    ) -> None:
        """
        Deactivate an active HR Override in place (Story 5.5, AC6/AC9). Reused
        for both the explicit `unset` action (AC6) and the "deactivate the
        stale override before creating a new one" re-mark case (AC9) -- one
        method, two callers, preserving the at-most-one-active invariant.

        Args:
            session: AsyncSession for database operations
            override: The AssignmentOverride record to deactivate (mutated in place)
            reversed_by: UUID of the HR Admin performing the deactivation
        """
        override.active = False
        override.reversed_at = datetime.now(timezone.utc)
        override.reversed_by = reversed_by
        await session.flush()
        logger.debug(f"Deactivated assignment_overrides row {override.id} for {override.assignment_id}")

    @staticmethod
    async def get_progress_for_assignments(
        session: AsyncSession, assignment_ids: list[UUID]
    ) -> list[SkillProgress]:
        """
        Batch-fetch all progress records for multiple assignments (prevents N+1).

        Args:
            session: AsyncSession for database operations
            assignment_ids: List of assignment UUIDs

        Returns:
            List of SkillProgress records (may be fewer than input IDs if no progress for some)
        """
        if not assignment_ids:
            return []

        result = await session.execute(
            select(SkillProgress).where(SkillProgress.assignment_id.in_(assignment_ids))
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_active_overrides_for_assignments(
        session: AsyncSession, assignment_ids: list[UUID]
    ) -> list[AssignmentOverride]:
        """
        Batch-fetch all active override records for multiple assignments (prevents N+1).

        Args:
            session: AsyncSession for database operations
            assignment_ids: List of assignment UUIDs

        Returns:
            List of AssignmentOverride records where active=true (one per assignment, most recent)
        """
        if not assignment_ids:
            return []

        from sqlalchemy import and_

        result = await session.execute(
            select(AssignmentOverride)
            .where(
                and_(
                    AssignmentOverride.assignment_id.in_(assignment_ids),
                    AssignmentOverride.active == True,
                )
            )
            .order_by(AssignmentOverride.assignment_id, AssignmentOverride.set_at.desc())
            .options(joinedload(AssignmentOverride.set_by_user))
        )
        overrides = list(result.unique().scalars().all())

        deduped = {}
        for override in overrides:
            if override.assignment_id not in deduped:
                deduped[override.assignment_id] = override

        return list(deduped.values())
