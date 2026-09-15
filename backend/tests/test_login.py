from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import Account
from app.core.config import settings
from app.core.seed_ids import CASEY_ID, JORDAN_ID, MORGAN_ID, RITA_ID, SAM_ID
from app.main import app

_engine = create_async_engine(settings.DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("email", "expected_role", "expected_user_id"),
    [
        ("rita@sails.example.com", "HR_ADMIN", str(RITA_ID)),
        ("casey@sails.example.com", "EMPLOYEE", str(CASEY_ID)),
        ("morgan@sails.example.com", "EMPLOYEE", str(MORGAN_ID)),
        ("jordan@sails.example.com", "EMPLOYEE", str(JORDAN_ID)),
        ("sam@sails.example.com", "EMPLOYEE", str(SAM_ID)),
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


@pytest.mark.asyncio
async def test_login_rejects_an_archived_account():
    """authenticate() now reads the real accounts table (auth-wiring fix) --
    mirrors get_current_user's existing archived-identity rejection (Story
    7.5 AC4) at the login boundary too: a correct password for an archived
    Account must still be refused, not just a still-valid session for one
    archived after login."""
    async with _session_factory() as session:
        account = await session.get(Account, SAM_ID)
        account.archived_at = datetime.now(timezone.utc)
        await session.commit()

    try:
        async with _client() as client:
            response = await client.post(
                "/api/auth/login",
                json={"email": "sam@sails.example.com", "password": "demo123"},
            )
            assert response.status_code == 401
            assert response.json()["message"] == "Email or password incorrect"
    finally:
        async with _session_factory() as session:
            account = await session.get(Account, SAM_ID)
            account.archived_at = None
            await session.commit()
