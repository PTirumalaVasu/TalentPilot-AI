import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("email", "expected_role", "expected_user_id"),
    [
        ("rita@sails.example.com", "HR_ADMIN", "rita"),
        ("casey@sails.example.com", "EMPLOYEE", "casey"),
        ("morgan@sails.example.com", "EMPLOYEE", "morgan"),
        ("jordan@sails.example.com", "EMPLOYEE", "jordan"),
        ("sam@sails.example.com", "EMPLOYEE", "sam"),
    ],
)
async def test_login_succeeds_for_each_demo_account(email, expected_role, expected_user_id):
    async with _client() as client:
        response = await client.post(
            "/api/auth/login", json={"email": email, "password": "demo123"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["role"] == expected_role
        assert body["user_id"] == expected_user_id
        assert "token" not in body
        assert "password" not in body


@pytest.mark.asyncio
async def test_login_sets_session_cookie():
    async with _client() as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": "rita@sails.example.com", "password": "demo123"},
        )
        assert response.status_code == 200
        set_cookie = response.headers.get("set-cookie", "")
        assert settings.SESSION_COOKIE_NAME in set_cookie
        assert "HttpOnly" in set_cookie


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401_generic_message():
    async with _client() as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": "rita@sails.example.com", "password": "wrong-password"},
        )
        assert response.status_code == 401
        assert response.json()["message"] == "Email or password incorrect"


@pytest.mark.asyncio
async def test_login_unknown_email_returns_identical_401():
    async with _client() as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": "nobody@sails.example.com", "password": "demo123"},
        )
        assert response.status_code == 401
        assert response.json()["message"] == "Email or password incorrect"


@pytest.mark.asyncio
async def test_login_wrong_password_and_unknown_email_are_indistinguishable():
    async with _client() as client:
        wrong_password = await client.post(
            "/api/auth/login",
            json={"email": "rita@sails.example.com", "password": "wrong-password"},
        )
        unknown_email = await client.post(
            "/api/auth/login",
            json={"email": "nobody@sails.example.com", "password": "demo123"},
        )
        assert wrong_password.status_code == unknown_email.status_code
        assert wrong_password.json()["message"] == unknown_email.json()["message"]
        assert wrong_password.json()["code"] == unknown_email.json()["code"]


@pytest.mark.asyncio
async def test_login_case_insensitive_email_still_succeeds():
    """Regression test: Rita@Sails.example.com (different case) previously
    failed login even with the correct password, since lookup was a raw
    case-sensitive dict key match."""
    async with _client() as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": "Rita@Sails.example.com", "password": "demo123"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == "HR_ADMIN"


@pytest.mark.asyncio
async def test_login_empty_credentials_returns_401_not_500():
    async with _client() as client:
        response = await client.post(
            "/api/auth/login", json={"email": "", "password": ""}
        )
        assert response.status_code == 401
        assert response.json()["message"] == "Email or password incorrect"


@pytest.mark.asyncio
async def test_login_missing_password_field_returns_422_not_500():
    async with _client() as client:
        response = await client.post(
            "/api/auth/login", json={"email": "rita@sails.example.com"}
        )
        assert response.status_code == 422
        assert response.json()["code"] == "VALIDATION_ERROR"
