"""Simple endpoint for employee's own assignments."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.schemas import MyAssignmentsResponse
from app.assignments.service import list_my_assignments
from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.core.db import get_db

router = APIRouter(prefix="/my-assignments", tags=["assignments"])


@router.get("", response_model=MyAssignmentsResponse)
async def get_my_assignments(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MyAssignmentsResponse:
    """Get current employee's assignments."""
    return await list_my_assignments(session, current_user=current_user)
