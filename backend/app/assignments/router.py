from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.schemas import MyAssignmentsResponse
from app.assignments.service import list_my_assignments
from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.core.db import get_db

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("", response_model=MyAssignmentsResponse)
async def list_my_assignments_route(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MyAssignmentsResponse:
    return await list_my_assignments(db, current_user=current_user)
