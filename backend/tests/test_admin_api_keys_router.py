"""Router-level tests for content/admin_api_keys_router.py (Story 6.5, FR-16,
AD-10): GET/PUT/DELETE /api/admin/api-keys/*.

Uses the real `app.main.app` via ASGITransport plus a *private*
engine/session for cleanup, mirroring test_skills_router.py's established
pattern exactly (a plain async helper called explicitly at the start of each
test, never an async pytest fixture -- an autouse async fixture here was
found to corrupt this module's private engine's connection under
loop_scope="module", "another operation is in progress"; explicit
sequential calls avoid it, matching every other router test file's style).
"""
import json
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.assignments.models import AdminApiKey, Employee, OrgApiCredential
from app.auth.repository import _MOCK_ACCOUNTS
from app.core.config import settings
from app.core.secrets import decrypt_secret
from app.core.seed_ids import RITA_ID
from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="module")

_engine = create_async_engine(settings.DATABASE_URL)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _login(client: AsyncClient, email: str = "rita@sails.example.com") -> None:
    response = await client.post("/api/auth/login", json={"email": email, "password": "demo123"})
    assert response.status_code == 200
    set_cookie_header = response.headers.get("set-cookie", "")
    prefix = f"{settings.SESSION_COOKIE_NAME}="
    token = set_cookie_header.split(";", 1)[0][len(prefix) :]
    client.cookies.clear()
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)


async def _create_second_hr_admin(email: str, name: str) -> uuid.UUID:
    """Creates a genuine second HR_ADMIN identity (code review, 2026-09-10)
    -- Rita is the only seeded HR_ADMIN in this demo roster, so proving
    AC4's "regardless of which Admin configured it before me" through a
    real authenticated HTTP session (not just two raw UUIDs at the
    repository layer) requires a second real admin to log in as.

    Login in this codebase is NOT DB-backed (Story 1.4: "mock credential
    store... hardcoded, not DB-backed", `app.auth.repository._MOCK_ACCOUNTS`)
    -- a DB `accounts` row alone would never let this identity log in. This
    adds a real `employees` row (needed for the `configured_by` FK and for
    `get_employee_by_id_service` to resolve the display name) AND a
    temporary entry in the in-memory `_MOCK_ACCOUNTS` dict (needed for
    `POST /api/auth/login` to accept it) -- both cleaned up by
    `_delete_second_hr_admin`."""
    employee_id = uuid.uuid4()
    async with _session_factory() as session:
        session.add(Employee(id=employee_id, name=name, email=email, role="HR_ADMIN"))
        await session.commit()
    _MOCK_ACCOUNTS[email] = {"password": "demo123", "role": "HR_ADMIN", "user_id": str(employee_id)}
    return employee_id


async def _delete_second_hr_admin(email: str, employee_id: uuid.UUID) -> None:
    _MOCK_ACCOUNTS.pop(email, None)
    async with _session_factory() as session:
        await session.execute(delete(Employee).where(Employee.id == employee_id))
        await session.commit()


async def _clear_credentials() -> None:
    async with _session_factory() as session:
        await session.execute(delete(AdminApiKey).where(AdminApiKey.source == "YOUTUBE"))
        await session.execute(delete(OrgApiCredential).where(OrgApiCredential.source == "UDEMY"))
        await session.commit()


async def _get_admin_api_key_row() -> AdminApiKey:
    async with _session_factory() as session:
        result = await session.execute(
            select(AdminApiKey).where(AdminApiKey.admin_id == RITA_ID, AdminApiKey.source == "YOUTUBE")
        )
        return result.scalar_one()


async def _get_org_api_credential_row() -> OrgApiCredential:
    async with _session_factory() as session:
        result = await session.execute(select(OrgApiCredential).where(OrgApiCredential.source == "UDEMY"))
        return result.scalar_one()


# ---------------------------------------------------------------------------
# GET /api/admin/api-keys
# ---------------------------------------------------------------------------


async def test_get_status_when_nothing_configured():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.get("/api/admin/api-keys")

        assert response.status_code == 200
        body = response.json()
        assert body == {
            "youtube": {"configured": False},
            "udemy": {"configured": False, "configured_by": None, "configured_at": None},
        }


async def test_get_status_requires_authentication():
    await _clear_credentials()
    async with _client() as client:
        response = await client.get("/api/admin/api-keys")
        assert response.status_code == 401


async def test_get_status_as_employee_returns_403():
    await _clear_credentials()
    async with _client() as client:
        await _login(client, email="casey@sails.example.com")
        response = await client.get("/api/admin/api-keys")
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# PUT/DELETE /api/admin/api-keys/youtube
# ---------------------------------------------------------------------------


async def test_youtube_save_status_remove_round_trip():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)

        save = await client.put("/api/admin/api-keys/youtube", json={"key": "AIzaSy-fake-key"})
        assert save.status_code == 204
        assert save.text == ""

        status_response = await client.get("/api/admin/api-keys")
        assert status_response.json()["youtube"] == {"configured": True}

        remove = await client.delete("/api/admin/api-keys/youtube")
        assert remove.status_code == 204

        status_after = await client.get("/api/admin/api-keys")
        assert status_after.json()["youtube"] == {"configured": False}


async def test_youtube_save_never_echoes_the_key_value_anywhere():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)

        save = await client.put("/api/admin/api-keys/youtube", json={"key": "super-secret-value"})
        status_response = await client.get("/api/admin/api-keys")

        assert "super-secret-value" not in save.text
        assert "super-secret-value" not in status_response.text


async def test_youtube_save_encrypts_the_stored_value():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        await client.put("/api/admin/api-keys/youtube", json={"key": "plain-text-key"})

    row = await _get_admin_api_key_row()
    assert row.encrypted_key != "plain-text-key"
    assert decrypt_secret(row.encrypted_key) == "plain-text-key"


async def test_youtube_save_rejects_blank_key():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.put("/api/admin/api-keys/youtube", json={"key": "   "})
        assert response.status_code == 422


async def test_youtube_save_rejects_missing_key():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.put("/api/admin/api-keys/youtube", json={})
        assert response.status_code == 422


async def test_youtube_save_rejects_unknown_field():
    # extra="forbid" enforcement (code review, 2026-09-10) -- matches the
    # established precedent in test_skills_router.py's identical test.
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.put("/api/admin/api-keys/youtube", json={"key": "a-key", "admin_id": "hacked"})
        assert response.status_code == 422


async def test_youtube_save_rejects_key_over_max_length():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.put("/api/admin/api-keys/youtube", json={"key": "x" * 4097})
        assert response.status_code == 422


async def test_youtube_save_as_employee_returns_403():
    await _clear_credentials()
    async with _client() as client:
        await _login(client, email="casey@sails.example.com")
        response = await client.put("/api/admin/api-keys/youtube", json={"key": "a-key"})
        assert response.status_code == 403


async def test_youtube_save_requires_authentication():
    await _clear_credentials()
    async with _client() as client:
        response = await client.put("/api/admin/api-keys/youtube", json={"key": "a-key"})
        assert response.status_code == 401


async def test_youtube_remove_as_employee_returns_403():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        await client.put("/api/admin/api-keys/youtube", json={"key": "a-key"})

        await _login(client, email="casey@sails.example.com")
        response = await client.delete("/api/admin/api-keys/youtube")
        assert response.status_code == 403


async def test_youtube_remove_requires_authentication():
    await _clear_credentials()
    async with _client() as client:
        response = await client.delete("/api/admin/api-keys/youtube")
        assert response.status_code == 401


async def test_youtube_remove_when_nothing_configured_still_returns_204():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.delete("/api/admin/api-keys/youtube")
        assert response.status_code == 204


# ---------------------------------------------------------------------------
# PUT/DELETE /api/admin/api-keys/udemy
# ---------------------------------------------------------------------------


async def test_udemy_save_status_remove_round_trip():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)

        save = await client.put(
            "/api/admin/api-keys/udemy", json={"client_id": "client-abc", "client_secret": "secret-xyz"}
        )
        assert save.status_code == 204

        status_response = await client.get("/api/admin/api-keys")
        udemy = status_response.json()["udemy"]
        assert udemy["configured"] is True
        assert udemy["configured_by"] == "Rita the Recommender"
        assert udemy["configured_at"] is not None

        remove = await client.delete("/api/admin/api-keys/udemy")
        assert remove.status_code == 204

        status_after = await client.get("/api/admin/api-keys")
        assert status_after.json()["udemy"] == {"configured": False, "configured_by": None, "configured_at": None}


async def test_udemy_save_never_echoes_client_id_or_secret_anywhere():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)

        save = await client.put(
            "/api/admin/api-keys/udemy",
            json={"client_id": "very-unique-id-123", "client_secret": "very-unique-secret-456"},
        )
        status_response = await client.get("/api/admin/api-keys")

        assert "very-unique-id-123" not in save.text
        assert "very-unique-secret-456" not in save.text
        assert "very-unique-id-123" not in status_response.text
        assert "very-unique-secret-456" not in status_response.text


async def test_udemy_save_encrypts_both_fields_into_one_blob():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        await client.put("/api/admin/api-keys/udemy", json={"client_id": "cid", "client_secret": "csecret"})

    row = await _get_org_api_credential_row()
    decrypted = json.loads(decrypt_secret(row.encrypted_key))
    assert decrypted == {"client_id": "cid", "client_secret": "csecret"}


async def test_udemy_save_by_second_admin_replaces_configured_by():
    await _clear_credentials()
    second_admin_email = f"second-admin-{uuid.uuid4().hex[:8]}@sails.example.com"
    second_admin_id = await _create_second_hr_admin(second_admin_email, "Sandy the Second Admin")
    try:
        async with _client() as client:
            await _login(client)
            await client.put(
                "/api/admin/api-keys/udemy", json={"client_id": "first", "client_secret": "first-secret"}
            )

            first_status = await client.get("/api/admin/api-keys")
            assert first_status.json()["udemy"]["configured_by"] == "Rita the Recommender"

            # A genuine second HR_ADMIN identity (code review, 2026-09-10) --
            # the previous version of this test re-logged in as Rita twice,
            # which would have passed even if configured_by were never
            # updated at all.
            await _login(client, email=second_admin_email)
            await client.put(
                "/api/admin/api-keys/udemy", json={"client_id": "second", "client_secret": "second-secret"}
            )
            second_status = await client.get("/api/admin/api-keys")
            assert second_status.json()["udemy"]["configured_by"] == "Sandy the Second Admin"
    finally:
        await _delete_second_hr_admin(second_admin_email, second_admin_id)


async def test_udemy_save_rejects_blank_client_id():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.put(
            "/api/admin/api-keys/udemy", json={"client_id": "   ", "client_secret": "secret"}
        )
        assert response.status_code == 422


async def test_udemy_save_rejects_blank_client_secret():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.put(
            "/api/admin/api-keys/udemy", json={"client_id": "cid", "client_secret": "   "}
        )
        assert response.status_code == 422


async def test_udemy_save_rejects_unknown_field():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.put(
            "/api/admin/api-keys/udemy",
            json={"client_id": "cid", "client_secret": "secret", "configured_by": "hacked"},
        )
        assert response.status_code == 422


async def test_udemy_save_rejects_client_id_over_max_length():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.put(
            "/api/admin/api-keys/udemy", json={"client_id": "x" * 4097, "client_secret": "secret"}
        )
        assert response.status_code == 422


async def test_udemy_save_rejects_client_secret_over_max_length():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.put(
            "/api/admin/api-keys/udemy", json={"client_id": "cid", "client_secret": "x" * 4097}
        )
        assert response.status_code == 422


async def test_udemy_save_as_employee_returns_403():
    await _clear_credentials()
    async with _client() as client:
        await _login(client, email="casey@sails.example.com")
        response = await client.put(
            "/api/admin/api-keys/udemy", json={"client_id": "cid", "client_secret": "secret"}
        )
        assert response.status_code == 403


async def test_udemy_save_requires_authentication():
    await _clear_credentials()
    async with _client() as client:
        response = await client.put(
            "/api/admin/api-keys/udemy", json={"client_id": "cid", "client_secret": "secret"}
        )
        assert response.status_code == 401


async def test_udemy_remove_as_employee_returns_403():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        await client.put("/api/admin/api-keys/udemy", json={"client_id": "cid", "client_secret": "secret"})

        await _login(client, email="casey@sails.example.com")
        response = await client.delete("/api/admin/api-keys/udemy")
        assert response.status_code == 403


async def test_udemy_remove_requires_authentication():
    await _clear_credentials()
    async with _client() as client:
        response = await client.delete("/api/admin/api-keys/udemy")
        assert response.status_code == 401


async def test_udemy_remove_when_nothing_configured_still_returns_204():
    await _clear_credentials()
    async with _client() as client:
        await _login(client)
        response = await client.delete("/api/admin/api-keys/udemy")
        assert response.status_code == 204
