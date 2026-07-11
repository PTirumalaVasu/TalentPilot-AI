"""Service layer for the progress module. Cross-module callers must go through here (AD-1)."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.progress.models import SkillProgress
from app.progress.repository import ProgressRepository
from app.progress.schemas import SkillProgressResponse


class ProgressService:
    """Service layer for watch progress business logic."""

    @staticmethod
    def derive_status(
        watch_position: int, duration_seconds: int | None = None
    ) -> Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETED"]:
        """Narrow Status-only slice of AD-3's single-derivation-authority rule
        (Story 2.5). Does not compute Provenance, self-report staleness, or HR
        override -- Story 5.1 extends this method with those, it does not
        duplicate it.

        `watch_position` is stored in seconds (SkillProgress.watch_position),
        not a percentage -- AD-3 defines Status from "Watch %", so COMPLETED
        can only be derived when `duration_seconds` is known (e.g. from a
        matched Content item's metadata). Without a known duration, any
        watch_position > 0 is IN_PROGRESS -- never COMPLETED, since a raw
        position in seconds carries no completion signal on its own (a
        150-second position could be 5% or 95% through a video depending on
        its length). Callers own resolving `duration_seconds`; this is pure
        derivation logic with no DB access."""
        if watch_position <= 0:
            return "NOT_STARTED"
        if duration_seconds is not None and duration_seconds > 0 and watch_position >= duration_seconds:
            return "COMPLETED"
        return "IN_PROGRESS"

    @staticmethod
    async def record_watch_progress(
        session: AsyncSession,
        assignment_id: UUID,
        watch_position: int,
        event_time: datetime,
        verified: bool,
    ) -> SkillProgressResponse:
        """
        Record or update watch progress with event-time-ordered conditional write.

        Delegates to ProgressRepository.initialize_or_update() for atomic create-or-update logic.

        Args:
            session: AsyncSession for database operations
            assignment_id: UUID of the assignment
            watch_position: Position in seconds
            event_time: ISO-8601 timestamp when position was observed (client time)
            verified: True if passed server-side anti-spoofing checks

        Returns:
            SkillProgressResponse: The persisted (or updated) progress record
        """
        # Use atomic initialize-or-update: creates new record on first call, updates with conditional write on subsequent calls
        progress = await ProgressRepository.initialize_or_update(
            session, assignment_id, watch_position, event_time, verified
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
