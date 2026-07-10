"""Service layer for the progress module. Cross-module callers must go through here (AD-1)."""
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.progress.models import SkillProgress
from app.progress.repository import ProgressRepository
from app.progress.schemas import SkillProgressResponse


class ProgressService:
    """Service layer for watch progress business logic."""

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
