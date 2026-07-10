from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_user
from app.content.schemas import ContentResponse
from app.content.service import match_content_for_skill
from app.core.db import get_db

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/match", response_model=ContentResponse | None)
async def content_match_route(
    skill_id: UUID, session: AsyncSession = Depends(get_db)
) -> ContentResponse | None:
    """Best-available Content match for a Skill (Story 3.4 AC3/AC6), now
    backed by Story 2.4's real filter-then-rank semantic matching — a
    query-param form rather than the spine's /api/skills/{id}/content nested
    path, chosen deliberately so "no content found" can return a clean `null`
    body distinguishable from a 404 (see story Dev Notes for the full
    rationale)."""
    return await match_content_for_skill(session, skill_id)
