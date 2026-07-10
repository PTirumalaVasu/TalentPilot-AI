"""Story 1.6: the auth gate must be wired onto assignments/content/progress/dashboard
routers at construction, so any route those routers gain later is protected too."""
import pytest
from fastapi import APIRouter, Depends, FastAPI, Request
from httpx import ASGITransport, AsyncClient

from app.assignments.router import router as assignments_router
from app.auth import service as auth_service
from app.auth.router import router as auth_router
from app.auth.schemas import CurrentUser
from app.auth.service import get_current_user
from app.content.router import router as content_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.security import create_access_token
from app.dashboard.router import router as dashboard_router
from app.progress.router import router as progress_router

PROTECTED_ROUTERS = {
    "assignments_router": assignments_router,
    "content_router": content_router,
    "progress_router": progress_router,
    "dashboard_router": dashboard_router,
}


@pytest.mark.parametrize("name", PROTECTED_ROUTERS.keys())
def test_protected_router_declares_the_gate_at_construction(name):
    router = PROTECTED_ROUTERS[name]
    assert any(
        dep.dependency is get_current_user for dep in router.dependencies
    ), f"{name} is missing APIRouter(dependencies=[Depends(get_current_user)])"


def test_auth_router_is_not_gated():
    """Regression guard: /login and /logout must stay reachable without a session."""
    assert auth_router.dependencies == []


def _build_probe_app() -> tuple[FastAPI, list[int]]:
    """Mirrors exactly how Epic 2-5 will add real routes: construct the router with
    the gate, then register a route on it afterward (established pattern, see
    test_current_user.py's _build_current_user_test_app).

    Returns the app alongside a `call_count` cell (a single-item list, mutated by
    the handler) so tests can prove the handler body itself never ran on a 401,
    rather than just inferring non-execution from the response shape."""
    call_count = [0]
    probe_router = APIRouter(dependencies=[Depends(get_current_user)])

    @probe_router.get("/probe")
    async def probe(request: Request, current_user: CurrentUser = Depends(get_current_user)):
        call_count[0] += 1
        return {
            "user_id": current_user.user_id,
            "state_matches": request.state.current_user is current_user,
        }

    test_app = FastAPI()
    register_exception_handlers(test_app)
    test_app.include_router(probe_router, prefix="/gated")
    return test_app, call_count


def _client(test_app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test")


@pytest.mark.asyncio
async def test_no_cookie_returns_401_before_handler_runs():
    test_app, call_count = _build_probe_app()
    async with _client(test_app) as client:
        response = await client.get("/gated/probe")
        assert response.status_code == 401
        body = response.json()
        assert body["status"] == "error"
        assert set(body.keys()) == {"status", "code", "message", "timestamp"}
        assert call_count[0] == 0, "handler body ran despite the missing session"


@pytest.mark.asyncio
async def test_expired_token_returns_401():
    token = create_access_token(user_id="casey", role="EMPLOYEE", expires_in_hours=-1)
    test_app, call_count = _build_probe_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/gated/probe")
        assert response.status_code == 401
        assert call_count[0] == 0


@pytest.mark.asyncio
async def test_tampered_token_returns_401():
    token = create_access_token(user_id="casey", role="EMPLOYEE")
    header, payload, signature = token.split(".")
    flipped = "".join(
        ("A" if c != "A" else "B") if i % 2 == 0 else c for i, c in enumerate(signature)
    )
    tampered = f"{header}.{payload}.{flipped}"

    test_app, call_count = _build_probe_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, tampered)
        response = await client.get("/gated/probe")
        assert response.status_code == 401
        assert call_count[0] == 0


@pytest.mark.asyncio
async def test_revoked_token_returns_401():
    token = create_access_token(user_id="casey", role="EMPLOYEE")
    auth_service._revoked_tokens.add(token)

    test_app, call_count = _build_probe_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/gated/probe")
        assert response.status_code == 401
        assert response.json()["message"] == "Session has been signed out"
        assert call_count[0] == 0


@pytest.mark.asyncio
async def test_valid_token_passes_the_gate_and_reaches_the_handler():
    token = create_access_token(user_id="casey", role="EMPLOYEE")
    test_app, call_count = _build_probe_app()
    async with _client(test_app) as client:
        client.cookies.set(settings.SESSION_COOKIE_NAME, token)
        response = await client.get("/gated/probe")
        assert response.status_code == 200
        body = response.json()
        assert body["user_id"] == "casey"
        assert body["state_matches"] is True
        assert call_count[0] == 1
