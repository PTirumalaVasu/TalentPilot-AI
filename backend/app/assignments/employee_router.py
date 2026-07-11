from fastapi import APIRouter

router = APIRouter(prefix="/my-assignments", tags=["assignments"])


@router.get("")
async def get_my_assignments_test():
    """Test endpoint for my-assignments."""
    return {"message": "test"}


# @router.get("", response_model=MyAssignmentsResponse)
# async def get_my_assignments(
#     current_user: CurrentUser = Depends(get_current_user),
#     session: AsyncSession = Depends(get_db),
# ) -> MyAssignmentsResponse:
#     """Fetch current EMPLOYEE's assignments with progress counts (Story 2.5)."""
#     return await list_my_assignments(session, current_user=current_user)
