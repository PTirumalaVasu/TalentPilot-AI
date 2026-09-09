"""HTTP routes for the skills module.

Story 6.2 adds the first route: POST /api/admin/skills (FR-20). Story 6.3
adds PATCH/DELETE /api/admin/skills/{id} (FR-21/22) -- out of this story's
scope. Mounted in app/main.py under the /api/admin/skills prefix (admin-only
routes convention, ARCHITECTURE-SPINE.md Consistency Conventions), distinct
from assignments/router.py's pre-existing read-only GET /api/assignments/skills
combobox route.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.core.db import get_db
from app.skills.schemas import CreateSkillRequest, SkillResponse
from app.skills.service import create_skill_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill_route(
    request: CreateSkillRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SkillResponse:
    """Creates a Skill (Story 6.2 AC1) -- HR_ADMIN-only via
    create_skill_service's require_hr_admin gate."""
    return await create_skill_service(session, current_user=current_user, request=request)
