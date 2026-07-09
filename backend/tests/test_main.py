import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from app.core.errors import AppException, register_exception_handlers
from app.main import app


@pytest.mark.asyncio
async def test_app_boots_and_root_health_responds():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200


def test_cors_middleware_configured():
    from starlette.middleware.cors import CORSMiddleware

    assert any(m.cls is CORSMiddleware for m in app.user_middleware)


def test_cors_origins_are_explicit_not_wildcard():
    from app.core.config import settings

    origins = settings.allowed_origins_list
    assert "*" not in origins
    assert "http://localhost:5173" in origins


def _build_test_app_with_handlers() -> FastAPI:
    """Isolated app wired with the real handlers, used to exercise error paths
    without adding debug-only routes to the production app in main.py."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/boom")
    async def boom():
        raise RuntimeError("boom")

    @test_app.post("/validate")
    async def validate(payload: dict[str, int]):
        return payload

    @test_app.get("/plain-http-exception")
    async def plain_http_exception():
        raise HTTPException(403, "no custom code here")

    @test_app.get("/app-exception")
    async def app_exception():
        raise AppException(403, error_code="INVALID_ROLE", message="Role 'UNKNOWN' not recognized. Expected: HR_ADMIN or EMPLOYEE")

    return test_app


@pytest.mark.asyncio
async def test_validation_error_returns_centralized_error_contract():
    test_app = _build_test_app_with_handlers()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/validate", content=b"not json")
        assert response.status_code == 422
        body = response.json()
        assert body["status"] == "error"
        assert body["code"] == "VALIDATION_ERROR"
        assert "message" in body
        assert "timestamp" in body


@pytest.mark.asyncio
async def test_unhandled_exception_returns_centralized_error_contract():
    test_app = _build_test_app_with_handlers()
    transport = ASGITransport(app=test_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/boom")
        assert response.status_code == 500
        body = response.json()
        assert body["status"] == "error"
        assert body["code"] == "INTERNAL_SERVER_ERROR"
        assert "timestamp" in body


@pytest.mark.asyncio
async def test_http_exception_returns_centralized_error_contract():
    """A raised HTTPException (401/403/404, used from Story 1.3 onward) must go
    through the same {status, code, message, timestamp} contract, not FastAPI's
    default {"detail": ...} shape."""
    test_app = _build_test_app_with_handlers()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/does-not-exist")
        assert response.status_code == 404
        body = response.json()
        assert body["status"] == "error"
        assert body["code"] == "HTTP_ERROR"
        assert "timestamp" in body


@pytest.mark.asyncio
async def test_plain_http_exception_falls_back_to_generic_error_code():
    """Backward-compatibility guard for Task 0: existing plain HTTPException
    call sites (e.g. Story 1.2's 401s) must keep returning HTTP_ERROR."""
    test_app = _build_test_app_with_handlers()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/plain-http-exception")
        assert response.status_code == 403
        assert response.json()["code"] == "HTTP_ERROR"


@pytest.mark.asyncio
async def test_app_exception_carries_custom_error_code():
    test_app = _build_test_app_with_handlers()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/app-exception")
        assert response.status_code == 403
        body = response.json()
        assert body["status"] == "error"
        assert body["code"] == "INVALID_ROLE"
        assert "UNKNOWN" in body["message"]
        assert "timestamp" in body
