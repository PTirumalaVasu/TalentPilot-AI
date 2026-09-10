"""HTTP routes for the skills module.

Story 6.2 adds the first route: POST /api/admin/skills (FR-20). Story 6.3
adds PATCH/DELETE /api/admin/skills/{id} (FR-21/22). Mounted in app/main.py
under the /api/admin/skills prefix (admin-only routes convention,
ARCHITECTURE-SPINE.md Consistency Conventions), distinct from
assignments/router.py's pre-existing read-only GET /api/assignments/skills
combobox route.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.content.schemas import ContentLookupRequest, ContentLookupResponse
from app.content.service import search_content_for_skill
from app.core.db import get_db
from app.skills.schemas import CreateSkillRequest, SkillResponse, UpdateSkillRequest
from app.skills.service import create_skill_service, delete_skill_service, update_skill_service

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


@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill_route(
    skill_id: UUID,
    request: UpdateSkillRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SkillResponse:
    """Renames/re-describes a Skill (Story 6.3 AC1) -- 403 if the Skill is
    permanently locked (AC2), 409 on a case-insensitive name conflict with
    a different Skill."""
    return await update_skill_service(session, current_user=current_user, skill_id=skill_id, request=request)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill_route(
    skill_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Hard-deletes a Skill and its attached Content (Story 6.3 AC3/AC4) --
    403 if the Skill is permanently locked (AC2)."""
    await delete_skill_service(session, current_user=current_user, skill_id=skill_id)


@router.post("/{skill_id}/content-lookup", response_model=ContentLookupResponse)
async def content_lookup_route(
    skill_id: UUID,
    request: ContentLookupRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ContentLookupResponse:
    """Live search across YouTube (per-admin key) and Udemy (org-wide
    credential) for a Skill (Story 6.6 AC1-AC7). Thin -- the actual
    search/credential logic lives in content/service.py (AD-1: only
    content/ may import youtube_client/udemy_client/the credential
    tables); this route only exists here because the URL is a Skill
    sub-resource (Story 6.6 Scope Note 2)."""
    return await search_content_for_skill(
        session, current_user=current_user, skill_id=skill_id, query=request.query
    )
