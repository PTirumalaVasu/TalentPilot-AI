"""HTTP routes for approving/rejecting reviewed content candidates (Stories
6.8/6.9, FR-18/FR-23). Mounted separately from content/router.py (which owns
/api/content) and skills/router.py (which owns /api/admin/skills/{id}/...
sub-resources) at /api/admin/content -- the architecture spine's own
Consistency Conventions table names both these exact routes. Mirrors
content/admin_api_keys_router.py's shape exactly: own file, own prefix,
thin routes calling straight into content/service.py.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.content import service as content_service
from app.content.schemas import AttachContentRequest, ContentResponse
from app.core.db import get_db

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/attach", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def attach_content_route(
    request: AttachContentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ContentResponse:
    """Approves a reviewed candidate (searched or manual) as Content for a
    Skill (Story 6.8 AC2-AC6). Thin -- the actual write/embedding logic
    lives in content/service.py::attach_content (AD-1)."""
    return await content_service.attach_content(
        session,
        current_user=current_user,
        skill_id=request.skill_id,
        title=request.title,
        source=request.source,
        url=request.url,
        duration_hours=request.duration_hours,
    )


@router.delete("/{content_id}/reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_content_route(
    content_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Rejects (hard-deletes) a previously-approved Content row (Story 6.9
    AC1-AC5). Thin -- the actual delete logic lives in
    content/service.py::reject_content (AD-1)."""
    await content_service.reject_content(session, current_user=current_user, content_id=content_id)
