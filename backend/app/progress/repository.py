"""Repository layer for the progress module. Only this module's own code may query its tables."""
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.assignments.models import Assignment, SkillProgress

logger = logging.getLogger(__name__)


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
        result = await session.execute(
            select(Assignment)
            .where(Assignment.id == assignment_id)
            .options(joinedload(Assignment.content), joinedload(Assignment.skill))
        )
        return result.unique().scalar_one_or_none()
