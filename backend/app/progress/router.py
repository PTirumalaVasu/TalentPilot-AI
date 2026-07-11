"""Router for progress module endpoints."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user, require_employee
from app.core.db import get_db
from app.progress.repository import ProgressRepository
from app.progress.schemas import RecordWatchProgressRequest, SkillProgressResponse, SkillProgressResponseResume
from app.progress.service import ProgressService

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/api/assignments/{assignment_id}/progress", response_model=SkillProgressResponse, status_code=201)
async def record_progress(
    assignment_id: UUID,
    request: RecordWatchProgressRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SkillProgressResponse:
    """
    Record watch progress for an assignment with server-side anti-spoofing validation.

    **Story 4-4: Anti-Spoofing Validation**

    This endpoint:
    1. Verifies session identity matches assignment employee (AC1, AC8)
    2. Validates position bounds (AC2)
    3. Checks playback rate (AC3)
    4. Verifies event-time coherence (AC4)
    5. Persists result with verified flag (AC5, AC6)

    Silent rejection pattern: failed validation sets verified=false and persists,
    no error response is sent to client.

    Args:
        assignment_id: UUID of the assignment
        request: RecordWatchProgressRequest with watch_position, event_time, video_url
        current_user: Authenticated user from JWT
        session: Database session

    Returns:
        SkillProgressResponse with persisted position and verified flag

    Raises:
        404 Not Found: If assignment doesn't exist
    """
    # Fetch assignment (with content for metadata)
    assignment = await ProgressRepository.get_assignment_for_progress(session, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # Get video duration from content metadata (if available)
    video_duration = ProgressRepository.get_video_duration(assignment)

    # Record progress with anti-spoofing validation (AC1-AC5)
    # Service fetches previous progress internally to avoid race conditions with concurrent updates
    response = await ProgressService.record_watch_progress(
        session=session,
        assignment_id=assignment_id,
        watch_position=request.watch_position,
        event_time=request.event_time,
        current_user=current_user,
        assignment=assignment,
        video_duration=video_duration,
    )

    return response


@router.get("/api/assignments/{assignment_id}/progress", response_model=SkillProgressResponseResume)
async def get_resume_position(
    assignment_id: UUID,
    current_user: CurrentUser = Depends(require_employee),
    session: AsyncSession = Depends(get_db),
) -> SkillProgressResponseResume:
    """
    Retrieve watch position for resume, with hard-scoping to authenticated session identity.

    **Story 4-5: Resume Position Retrieval & Exact-Point Playback (AC1)**

    This endpoint is EMPLOYEE-only and hard-scopes the result to the authenticated session's
    identity at the repository layer (AD-6 compliance). On first view (no recorded progress),
    returns position 0. On out-of-bounds corrupted data, returns 0 as a fail-safe.

    Args:
        assignment_id: UUID of the assignment
        current_user: Authenticated user from JWT (for hard-scoping identity check)
        session: Database session

    Returns:
        SkillProgressResponseResume with exact watch_position (0 if first view or out-of-bounds)

    Raises:
        401 Unauthorized: If no valid session
        403 Forbidden: If user is not the assignment's owner (identity mismatch)
    """
    response = await ProgressService.get_resume_position(
        session=session,
        current_user=current_user,
        assignment_id=assignment_id,
    )

    return response
