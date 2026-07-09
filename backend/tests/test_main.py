import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.errors import register_exception_handlers
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
