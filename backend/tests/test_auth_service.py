import jwt
import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from app.auth import service as auth_service
from app.auth.service import get_current_token_payload, set_session_cookie
from app.core.errors import register_exception_handlers
from app.core.security import create_access_token


def test_set_session_cookie_sets_expected_attributes(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "COOKIE_SECURE", True)
    monkeypatch.setattr(auth_service.settings, "JWT_EXPIRATION_HOURS", 24)

    response = JSONResponse(content={})
    set_session_cookie(response, "sometoken")

    set_cookie_header = response.headers["set-cookie"]
    assert "access_token=sometoken" in set_cookie_header
    assert "HttpOnly" in set_cookie_header
    assert "samesite=lax" in set_cookie_header.lower()
    assert "Secure" in set_cookie_header
    assert "Max-Age=86400" in set_cookie_header
    assert "Path=/" in set_cookie_header


def test_set_session_cookie_omits_secure_when_disabled(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "COOKIE_SECURE", False)

    response = JSONResponse(content={})
    set_session_cookie(response, "sometoken")

    set_cookie_header = response.headers["set-cookie"]
    assert "Secure" not in set_cookie_header


def _build_protected_test_app() -> FastAPI:
    """Isolated app exercising get_current_token_payload, following the
    established pattern of test-file-local routes rather than touching main.py."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/protected")
    async def protected(request: Request):
        payload = get_current_token_payload(request)
        return {"user_id": payload["user_id"]}

    return test_app


@pytest.mark.asyncio
async def test_missing_cookie_returns_401_via_error_contract():
    test_app = _build_protected_test_app()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/protected")
        assert response.status_code == 401
        body = response.json()
        assert body["status"] == "error"
        assert "timestamp" in body


@pytest.mark.asyncio
async def test_expired_token_returns_401():
    token = create_access_token(user_id="casey", role="EMPLOYEE", expires_in_hours=-1)
    test_app = _build_protected_test_app()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("access_token", token)
        response = await client.get("/protected")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_tampered_token_returns_401():
    token = create_access_token(user_id="casey", role="EMPLOYEE")
    header, payload, signature = token.split(".")
    flipped = "".join(
        ("A" if c != "A" else "B") if i % 2 == 0 else c for i, c in enumerate(signature)
    )
    tampered = f"{header}.{payload}.{flipped}"

    test_app = _build_protected_test_app()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("access_token", tampered)
        response = await client.get("/protected")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_valid_token_returns_200_with_payload():
    token = create_access_token(user_id="casey", role="EMPLOYEE")
    test_app = _build_protected_test_app()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("access_token", token)
        response = await client.get("/protected")
        assert response.status_code == 200
        assert response.json()["user_id"] == "casey"


@pytest.mark.asyncio
async def test_malformed_cookie_value_returns_401(monkeypatch):
    """Garbage/non-JWT-shaped cookie values are rejected as invalid, not a 500."""
    test_app = _build_protected_test_app()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("access_token", "not-even-close-to-a-jwt")
        response = await client.get("/protected")
        assert response.status_code == 401
        assert response.json()["status"] == "error"


def test_set_session_cookie_uses_configured_cookie_name(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "SESSION_COOKIE_NAME", "custom_session")

    response = JSONResponse(content={})
    set_session_cookie(response, "sometoken")

    assert "custom_session=sometoken" in response.headers["set-cookie"]


@pytest.mark.asyncio
async def test_get_current_token_payload_uses_configured_cookie_name(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "SESSION_COOKIE_NAME", "custom_session")
    token = create_access_token(user_id="casey", role="EMPLOYEE")

    test_app = _build_protected_test_app()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # The default-named cookie must NOT be honored once the setting changes
        client.cookies.set("access_token", token)
        response = await client.get("/protected")
        assert response.status_code == 401

        client.cookies.set("custom_session", token)
        response = await client.get("/protected")
        assert response.status_code == 200
        assert response.json()["user_id"] == "casey"
