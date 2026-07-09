from fastapi import APIRouter, Request, Response

from app.auth.schemas import LoginRequest, LoginResponse
from app.auth.service import authenticate, logout, set_session_cookie
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
