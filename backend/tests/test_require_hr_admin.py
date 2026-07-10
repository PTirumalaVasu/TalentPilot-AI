"""Tests for auth/service.py's require_hr_admin dependency (Story 3.1 AC4)."""
import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user, require_hr_admin
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.security import create_access_token


def _build_hr_admin_only_test_app() -> FastAPI:
    """Isolated app exercising require_hr_admin, following the established
    pattern of test-file-local routes rather than touching main.py."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/hr-only")
    async def hr_only(current_user: CurrentUser = Depends(require_hr_admin)):
        return {"role": current_user.role.value, "user_id": current_user.user_id}

    return test_app


def _client(test_app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test")


@pytest.mark.asyncio
async def test_hr_admin_passes_through_unchanged():
    token = create_access_token(user_id="rita", role="HR_ADMIN")

    test_app = _build_hr_admin_only_test_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/hr-only")
        assert response.status_code == 200
        body = response.json()
        assert body["role"] == "HR_ADMIN"
        assert body["user_id"] == "rita"


@pytest.mark.asyncio
async def test_employee_is_rejected_with_403_and_distinguishable_code():
    token = create_access_token(user_id="casey", role="EMPLOYEE")

    test_app = _build_hr_admin_only_test_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/hr-only")
        assert response.status_code == 403
        body = response.json()
        assert body["code"] == "FORBIDDEN_NOT_HR_ADMIN"
        assert body["status"] == "error"


@pytest.mark.asyncio
async def test_missing_session_still_returns_401_not_403():
    """require_hr_admin composes on get_current_user (via Depends) rather than
    re-implementing session/role validation — a missing session must fail with
    get_current_user's existing 401, not require_hr_admin's 403."""
    test_app = _build_hr_admin_only_test_app()
    async with _client(test_app) as client:
        response = await client.get("/hr-only")
        assert response.status_code == 401


def test_require_hr_admin_depends_on_get_current_user():
    """Structural check: require_hr_admin must compose on get_current_user via
    Depends, not duplicate cookie-extraction/JWT-decode/role-parsing logic."""
    import inspect

    sig = inspect.signature(require_hr_admin)
    current_user_param = sig.parameters["current_user"]
    assert current_user_param.default.dependency is get_current_user
