"""Service layer for the auth module. Cross-module callers must go through here (AD-1)."""

import logging
import secrets

import jwt
from fastapi import Depends, HTTPException, Request, Response, status

from app.auth.repository import find_account
from app.auth.schemas import CurrentUser, Role
from app.core.config import settings
from app.core.errors import AppException
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)

# In-memory, per-process record of signed-out tokens (Story 1.5). Deliberately
# not DB/Redis-backed: local-single-process MVP scope (AR-15/AR-16, and Story
# 1.1's "no Redis service" call), wiped on restart, unbounded-but-tiny growth
# accepted for a five-user demo pilot.
_revoked_tokens: set[str] = set()


def authenticate(email: str, password: str) -> tuple[str, Role]:
    account = find_account(email)
    if account is None or not secrets.compare_digest(account["password"], password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password incorrect")

    return account["user_id"], Role(account["role"])


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.JWT_EXPIRATION_HOURS * 3600,
        path="/",
    )


def get_current_token_payload(request: Request) -> dict:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No active session")

    if token in _revoked_tokens:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session has been signed out")

    try:
        return decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session") from exc


def logout(request: Request, response: Response) -> None:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token:
        _revoked_tokens.add(token)

    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )


def get_current_user(
    request: Request, payload: dict = Depends(get_current_token_payload)
) -> CurrentUser:
    role_claim = payload.get("role")
    if role_claim is None:
        logger.warning("Rejected request: JWT missing 'role' claim")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "JWT missing required 'role' claim")

    try:
        role = Role(role_claim)
    except (ValueError, TypeError):
        logger.warning("Rejected request: invalid role claim %r", role_claim)
        raise AppException(
            status.HTTP_403_FORBIDDEN,
            error_code="INVALID_ROLE",
            message=f"Role '{role_claim}' not recognized. Expected: HR_ADMIN or EMPLOYEE",
        ) from None

    user_id = payload.get("user_id")
    if not user_id:
        message = (
            "EMPLOYEE role requires user_id claim; token rejected"
            if role == Role.EMPLOYEE
            else "user_id claim is required; token rejected"
        )
        logger.warning("Rejected request: %s", message)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, message)

    current_user = CurrentUser(role=role, user_id=user_id)
    request.state.current_user = current_user
    return current_user
