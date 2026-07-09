import jwt as pyjwt
import pytest
from fastapi import Depends, FastAPI, Request
from httpx import ASGITransport, AsyncClient

from app.auth.schemas import CurrentUser, Role
from app.auth.service import get_current_user
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.security import create_access_token


def _build_current_user_test_app() -> FastAPI:
    """Isolated app exercising get_current_user, following the established
    pattern of test-file-local routes rather than touching main.py."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/whoami")
    async def whoami(request: Request, current_user: CurrentUser = Depends(get_current_user)):
        return {
            "role": current_user.role.value,
            "user_id": current_user.user_id,
            "state_matches": request.state.current_user is current_user,
        }

    return test_app


def _client(test_app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test")


@pytest.mark.asyncio
async def test_missing_role_claim_returns_401():
    # Craft a token with no "role" claim at all (bypassing create_access_token,
    # which always sets one) to exercise this specific edge case.
    payload = {"user_id": "casey"}
    token = pyjwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    test_app = _build_current_user_test_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/whoami")
        assert response.status_code == 401
        body = response.json()
        assert body["status"] == "error"
        assert "role" in body["message"]


@pytest.mark.asyncio
async def test_invalid_role_value_returns_403_with_invalid_role_code():
    token = create_access_token(user_id="casey", role="UNKNOWN")

    test_app = _build_current_user_test_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/whoami")
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "INVALID_ROLE"
        assert "UNKNOWN" in body["message"]


@pytest.mark.asyncio
async def test_non_string_role_claim_returns_403_not_500():
    """A role claim that isn't even a string (e.g. a list, from a malformed
    token) must still be rejected as INVALID_ROLE, not crash with TypeError."""
    payload = {"role": ["EMPLOYEE"], "user_id": "casey"}
    token = pyjwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    test_app = _build_current_user_test_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/whoami")
        assert response.status_code == 403
        assert response.json()["code"] == "INVALID_ROLE"


@pytest.mark.asyncio
async def test_employee_missing_user_id_returns_400():
    payload = {"role": "EMPLOYEE", "user_id": None}
    token = pyjwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    test_app = _build_current_user_test_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/whoami")
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_employee_absent_user_id_key_returns_400():
    """Distinct from the None-value case: the user_id key is missing entirely."""
    payload = {"role": "EMPLOYEE"}
    token = pyjwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    test_app = _build_current_user_test_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/whoami")
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_hr_admin_missing_user_id_returns_400_not_500():
    """Regression test: HR_ADMIN with no user_id claim previously crashed with
    an unhandled pydantic ValidationError (500) instead of a clean 400."""
    payload = {"role": "HR_ADMIN"}
    token = pyjwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    test_app = _build_current_user_test_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/whoami")
        assert response.status_code == 400
        body = response.json()
        assert body["status"] == "error"


@pytest.mark.asyncio
async def test_valid_hr_admin_passes_and_populates_state():
    token = create_access_token(user_id="rita", role="HR_ADMIN")

    test_app = _build_current_user_test_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/whoami")
        assert response.status_code == 200
        body = response.json()
        assert body["role"] == "HR_ADMIN"
        assert body["user_id"] == "rita"
        assert body["state_matches"] is True


@pytest.mark.asyncio
async def test_valid_employee_passes_and_populates_state():
    token = create_access_token(user_id="casey", role="EMPLOYEE")

    test_app = _build_current_user_test_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/whoami")
        assert response.status_code == 200
        body = response.json()
        assert body["role"] == "EMPLOYEE"
        assert body["user_id"] == "casey"
        assert body["state_matches"] is True


def test_role_enum_members():
    assert Role.HR_ADMIN.value == "HR_ADMIN"
    assert Role.EMPLOYEE.value == "EMPLOYEE"
    with pytest.raises(ValueError):
        Role("UNKNOWN")
