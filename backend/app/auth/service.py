"""Service layer for the auth module. Cross-module callers must go through here (AD-1)."""

import logging
import secrets
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repository import find_account, get_account_by_id
from app.auth.schemas import CurrentUser, Role
from app.core.config import settings
from app.core.db import get_db
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


async def get_current_user(
    request: Request,
    payload: dict = Depends(get_current_token_payload),
    db: AsyncSession = Depends(get_db),
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

    # Story 7.5 (FR-27/AR-25) AC4: revalidate an ARCHIVED identity's status
    # on every request, not only at login/token-issue time -- a still-
    # unexpired, non-revoked JWT for an Employee archived after it was
    # issued must still be rejected. Checked against Account.archived_at
    # (mirrors employees.archived_at, kept in sync by employees/service.py's
    # archive path) rather than importing app.employees.models.Employee
    # here, which would create a circular import (employees/service.py
    # already imports this module for require_hr_admin/account writes).
    #
    # Deliberately does NOT reject on a *missing* Account (hard-delete, or a
    # user_id that isn't UUID-shaped at all) -- this layer has never
    # required user_id to resolve to a real DB row (Story 1.3's own
    # docstring: "not guaranteed UUID-shaped... nothing upstream enforces
    # that"), and a large, pre-existing slice of this codebase's test suite
    # (PR #80's non-owning-HR-admin tests, test_current_user.py,
    # test_protected_router_gate.py, etc.) relies on exactly that -- minting
    # tokens for fabricated UUIDs or plain strings ("rita", "casey") with no
    # backing Account row, purely to exercise role/identity logic. AC4's own
    # text is scoped to archived Employees specifically, not hard-deleted
    # ones (who have zero Assignment history by construction, AC1) -- so
    # this narrower check satisfies the AC without an irreconcilable
    # conflict with that established convention.
    try:
        account_id = UUID(user_id)
    except (ValueError, TypeError):
        account_id = None

    if account_id is not None:
        account = await get_account_by_id(db, account_id)
        if account is not None and account.archived_at is not None:
            logger.warning("Rejected request: account %r has been archived", user_id)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account has been archived")

    current_user = CurrentUser(role=role, user_id=user_id)
    request.state.current_user = current_user
    return current_user


def require_hr_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Reusable HR-Admin-only gate for mutation-capable endpoints/services (Story
    3.1 AC4). Composes on get_current_user rather than re-validating the session
    itself, so a missing/invalid session still surfaces get_current_user's 401.

    Called as a plain function from service-layer code today (e.g.
    assignments/service.py::create_assignment_service), not via FastAPI's
    Depends() graph — no route exists yet to wire it into (Story 3.1 AC7
    deliberately adds none). Both call styles are valid since this is just a
    normal Python function with a Depends()-default; if a future route also
    adds Depends(require_hr_admin) at the router level, the check runs twice
    per request (redundant, not harmful) — prefer wiring it once, at
    whichever layer ends up owning the route."""
    if current_user.role != Role.HR_ADMIN:
        logger.warning(
            "Rejected request: role %r is not HR_ADMIN (user_id=%r)", current_user.role, current_user.user_id
        )
        raise AppException(
            status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN_NOT_HR_ADMIN",
            message="This action requires an HR Admin session",
        )
    return current_user


def require_employee(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Reusable Employee-only gate for employee-scoped read operations (Story 4-5 AC1).
    Follows the same composition pattern as require_hr_admin."""
    if current_user.role != Role.EMPLOYEE:
        logger.warning(
            "Rejected request: role %r is not EMPLOYEE (user_id=%r)", current_user.role, current_user.user_id
        )
        raise AppException(
            status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN_NOT_EMPLOYEE",
            message="This action requires an Employee session",
        )
    return current_user
