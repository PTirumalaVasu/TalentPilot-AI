"""Service layer for the progress module. Cross-module callers must go through here (AD-1)."""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import Assignment
from app.auth.schemas import CurrentUser
from app.progress.antiflow import run_all_validations
from app.progress.models import SkillProgress
from app.progress.repository import ProgressRepository
from app.progress.schemas import SkillProgressResponse

logger = logging.getLogger(__name__)


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
