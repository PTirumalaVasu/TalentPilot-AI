"""HTTP routes for approving/attaching reviewed content candidates (Story
6.8, FR-18). Mounted separately from content/router.py (which owns
/api/content) and skills/router.py (which owns /api/admin/skills/{id}/...
sub-resources) at /api/admin/content -- the architecture spine's own
Consistency Conventions table names this exact route. Mirrors
content/admin_api_keys_router.py's shape exactly: own file, own prefix,
thin routes calling straight into content/service.py.
"""
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
