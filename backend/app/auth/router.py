import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.service import get_employee_by_id_service
from app.auth.schemas import CurrentUser, LoginRequest, LoginResponse, MeResponse
from app.auth.service import authenticate, get_current_user, logout, set_session_cookie
from app.core.db import get_db
from app.core.security import create_access_token

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, response: Response) -> LoginResponse:
    user_id, role = authenticate(credentials.email, credentials.password)
    token = create_access_token(user_id=user_id, role=role.value)
    set_session_cookie(response, token)
    return LoginResponse(role=role, user_id=user_id)


@router.post("/logout", status_code=204)
async def logout_route(request: Request, response: Response) -> None:
    logout(request, response)


@router.get("/me", response_model=MeResponse)
async def get_me_route(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MeResponse:
    """Resolves the current session's own display identity (name/email) --
    closes the gap AuthContext.tsx's docstring documented, which previously
    forced ContentDiscovery.tsx to hardcode a placeholder identity instead."""
    employee = await get_employee_by_id_service(session, uuid.UUID(current_user.user_id))
    if employee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee record not found for session")
    return MeResponse(user_id=current_user.user_id, role=current_user.role, name=employee.name, email=employee.email)
