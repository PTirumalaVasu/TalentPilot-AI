import asyncio

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.auth.service import get_current_token_payload
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.seed_ids import MORGAN_ID
from app.main import app


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _build_protected_test_app() -> FastAPI:
    """Isolated app exercising get_current_token_payload, following the
    established pattern of test-file-local routes rather than touching main.py.
    Shares app.auth.service's module state (including _revoked_tokens) with
    the real `app` used for login/logout in these tests."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/protected")
    async def protected(payload: dict = Depends(get_current_token_payload)):
        return {"user_id": payload["user_id"]}

    return test_app


async def _login(client: AsyncClient, email: str = "casey@sails.example.com") -> str:
    response = await client.post(
        "/api/auth/login", json={"email": email, "password": "demo123"}
    )
    assert response.status_code == 200
    set_cookie_header = response.headers.get("set-cookie", "")
    prefix = f"{settings.SESSION_COOKIE_NAME}="
    assert set_cookie_header.startswith(prefix)
    token = set_cookie_header.split(";", 1)[0][len(prefix) :]

    # A spec-compliant HTTP client -- httpx included -- won't resend a
    # Secure-flagged cookie over this plain-http test transport, and whether
    # the cookie is Secure-flagged depends on COOKIE_SECURE, which varies by
    # checkout (True by default; a local backend/.env may override it to
    # False). Clear the jar (avoids a domain-mismatch CookieConflict across
    # repeated logins on the same client) and set the token explicitly so
    # follow-up requests actually carry it, regardless of local .env
    # configuration.
    client.cookies.clear()
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)
    return token


@pytest.mark.asyncio
async def test_logout_clears_session_cookie():
    async with _client() as client:
        await _login(client)
        response = await client.post("/api/auth/logout")
        assert response.status_code == 204

        set_cookie = response.headers.get("set-cookie", "")
        assert f"{settings.SESSION_COOKIE_NAME}=" in set_cookie
        assert "Max-Age=0" in set_cookie
        assert "Path=/" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "samesite=lax" in set_cookie.lower()


@pytest.mark.asyncio
async def test_logout_response_body_is_empty():
    async with _client() as client:
        await _login(client)
        response = await client.post("/api/auth/logout")
        assert response.status_code == 204
        assert response.content == b""


@pytest.mark.asyncio
async def test_logout_without_active_session_still_succeeds():
    async with _client() as client:
        response = await client.post("/api/auth/logout")
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_logout_called_twice_in_a_row_is_not_an_error():
    async with _client() as client:
        await _login(client)
        first = await client.post("/api/auth/logout")
        second = await client.post("/api/auth/logout")
        assert first.status_code == 204
        assert second.status_code == 204


@pytest.mark.asyncio
async def test_old_token_rejected_after_logout_even_though_not_expired():
    """Core AC1 proof: the raw token string, replayed manually after logout,
    must be rejected server-side -- not just dropped from the browser's
    cookie jar. Uses a fresh client + test-local protected route so httpx's
    own cookie-jar behavior can't accidentally make this test pass for the
    wrong reason."""
    async with _client() as login_client:
        old_token = await _login(login_client)
        logout_response = await login_client.post("/api/auth/logout")
        assert logout_response.status_code == 204

    protected_app = _build_protected_test_app()
    transport = ASGITransport(app=protected_app)
    async with AsyncClient(transport=transport, base_url="http://test") as replay_client:
        replay_client.cookies.set(settings.SESSION_COOKIE_NAME, old_token)
        response = await replay_client.get("/protected")
        assert response.status_code == 401
        assert response.json()["status"] == "error"
        assert response.json()["message"] == "Session has been signed out"


@pytest.mark.asyncio
async def test_logging_in_again_after_logout_issues_a_working_new_session():
    """Revocation is per-token, not per-user (AC4)."""
    async with _client() as client:
        await _login(client, email="morgan@sails.example.com")
        await client.post("/api/auth/logout")

        # create_access_token has whole-second precision, so back-to-back logins
        # for the same user within the same second would mint a byte-identical
        # (and thus already-revoked) token. Cross a second boundary so this test
        # exercises a genuinely new token, not an artifact of two logins landing
        # in the same iat second.
        await asyncio.sleep(1.1)
        new_token = await _login(client, email="morgan@sails.example.com")
        assert new_token is not None

    protected_app = _build_protected_test_app()
    transport = ASGITransport(app=protected_app)
    async with AsyncClient(transport=transport, base_url="http://test") as fresh_client:
        fresh_client.cookies.set(settings.SESSION_COOKIE_NAME, new_token)
        response = await fresh_client.get("/protected")
        assert response.status_code == 200
        assert response.json()["user_id"] == str(MORGAN_ID)
