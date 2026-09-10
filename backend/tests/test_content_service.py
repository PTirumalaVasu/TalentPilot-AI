"""Tests for content service layer (ORM → Pydantic conversion, cross-module API)."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import ContentCatalog
from app.auth.schemas import CurrentUser, Role
from app.core.errors import AppException
from app.core.seed_ids import CASEY_ID, RITA_ID
from app.skills.models import Skill
from app.content import repository
from app.content.service import (
    attach_content,
    get_api_keys_status,
    get_content,
    list_content_for_skill,
    remove_udemy_credential,
    remove_youtube_key,
    search_content_for_skill,
    set_udemy_credential,
    set_youtube_key,
    submit_manual_content,
)
from app.content.schemas import ContentResponse
from app.content.udemy_client import InvalidCredentialError as UdemyInvalidCredentialError
from app.content.udemy_client import RateLimitExceededError
from app.content.youtube_client import InvalidCredentialError as YoutubeInvalidCredentialError
from app.content.youtube_client import QuotaExceededError

HR_ADMIN_USER = CurrentUser(role=Role.HR_ADMIN, user_id=str(RITA_ID))
EMPLOYEE_USER = CurrentUser(role=Role.EMPLOYEE, user_id=str(CASEY_ID))


@pytest.mark.asyncio
async def test_get_content_returns_pydantic_response(db_session: AsyncSession):
    """Service get_content should return Pydantic ContentResponse (not ORM)."""
    # Create test skill and content
    unique_name = f"Service Test Skill {uuid.uuid4().hex[:8]}"
    skill = Skill(
        name=unique_name,
        description="Test skill",
        embedding=[0.1] * 384,
    )
    db_session.add(skill)
    await db_session.flush()

    content = ContentCatalog(
        skill_id=skill.id,
        title="Service Test Video",
        description="Test description",
        type="VIDEO",
        url="https://youtube.com/watch?v=service_test",
        embedding=[0.2] * 384,
        source="YOUTUBE",
        content_metadata={"video_id": "service_test", "duration": 300},
    )
    db_session.add(content)
    await db_session.flush()

    # Test service method
    result = await get_content(db_session, content.id)

    assert result is not None
    assert isinstance(result, ContentResponse)
    assert result.id == content.id
    assert result.title == "Service Test Video"
    assert result.type == "VIDEO"
    assert result.metadata == {"video_id": "service_test", "duration": 300}

    # Assert embedding is NOT included (ContentResponse excludes it)
    assert not hasattr(result, "embedding")


@pytest.mark.asyncio
async def test_get_content_returns_none_for_nonexistent(db_session: AsyncSession):
    """Service get_content should return None for non-existent ID."""
    fake_id = uuid.uuid4()

    result = await get_content(db_session, fake_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_content_for_skill_returns_list_of_pydantic(
    db_session: AsyncSession,
):
    """Service list_content_for_skill should return list of Pydantic ContentResponse."""
    # Create test skill
    unique_name = f"Service List Test Skill {uuid.uuid4().hex[:8]}"
    skill = Skill(
        name=unique_name,
        description="Test skill",
        embedding=[0.1] * 384,
    )
    db_session.add(skill)
    await db_session.flush()

    # Create multiple content items
    content1 = ContentCatalog(
        skill_id=skill.id,
        title="Service Video 1",
        description="First video",
        type="VIDEO",
        url="https://youtube.com/watch?v=svc1",
        embedding=[0.2] * 384,
        source="YOUTUBE",
        content_metadata={"video_id": "svc1"},
    )
    content2 = ContentCatalog(
        skill_id=skill.id,
        title="Service Document 1",
        description="First document",
        type="DOCUMENT",
        url="https://example.com/svc_doc1.pdf",
        embedding=[0.3] * 384,
        source="MANUAL",
        content_metadata=None,
    )
    db_session.add_all([content1, content2])
    await db_session.flush()

    # Test service method
    results = await list_content_for_skill(db_session, skill.id)

    assert len(results) == 2
    assert all(isinstance(c, ContentResponse) for c in results)
    assert all(c.skill_id == skill.id for c in results)

    titles = {c.title for c in results}
    assert "Service Video 1" in titles
    assert "Service Document 1" in titles

    # Assert embedding is NOT included in any result
    for c in results:
        assert not hasattr(c, "embedding")


@pytest.mark.asyncio
async def test_list_content_for_skill_returns_empty_list(db_session: AsyncSession):
    """Service list_content_for_skill should return empty list for skill with no content."""
    # Create skill with no content
    unique_name = f"Empty Service Skill {uuid.uuid4().hex[:8]}"
    skill = Skill(
        name=unique_name,
        description="Skill with no content",
        embedding=[0.1] * 384,
    )
    db_session.add(skill)
    await db_session.flush()

    # Test service method
    results = await list_content_for_skill(db_session, skill.id)

    assert results == []


@pytest.mark.asyncio
async def test_service_orm_to_pydantic_field_mapping(db_session: AsyncSession):
    """Service should correctly map ORM content_metadata to Pydantic metadata field."""
    # Create test skill and content with metadata
    unique_name = f"Mapping Test Skill {uuid.uuid4().hex[:8]}"
    skill = Skill(
        name=unique_name,
        description="Test skill",
        embedding=[0.1] * 384,
    )
    db_session.add(skill)
    await db_session.flush()

    content = ContentCatalog(
        skill_id=skill.id,
        title="Mapping Test Video",
        description="Test ORM field mapping",
        type="VIDEO",
        url="https://youtube.com/watch?v=mapping_test",
        embedding=[0.2] * 384,
        source="YOUTUBE",
        content_metadata={"video_id": "mapping_test", "duration": 1200, "views": 1000},
    )
    db_session.add(content)
    await db_session.flush()

    # Test service method
    result = await get_content(db_session, content.id)

    assert result is not None
    # Pydantic field is 'metadata', ORM field is 'content_metadata'
    assert result.metadata == {
        "video_id": "mapping_test",
        "duration": 1200,
        "views": 1000,
    }


# ---------------------------------------------------------------------------
# Admin/org API credential management (AD-10, Story 6.5)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_youtube_key_as_hr_admin_persists_it(db_session: AsyncSession):
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="a-real-key")

    status = await get_api_keys_status(db_session, current_user=HR_ADMIN_USER)
    assert status.youtube_configured is True


@pytest.mark.asyncio
async def test_set_youtube_key_as_employee_raises_403(db_session: AsyncSession):
    with pytest.raises(AppException) as exc_info:
        await set_youtube_key(db_session, current_user=EMPLOYEE_USER, key="a-key")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_remove_youtube_key_as_hr_admin_clears_it(db_session: AsyncSession):
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="a-key")

    await remove_youtube_key(db_session, current_user=HR_ADMIN_USER)

    status = await get_api_keys_status(db_session, current_user=HR_ADMIN_USER)
    assert status.youtube_configured is False


@pytest.mark.asyncio
async def test_remove_youtube_key_as_employee_raises_403(db_session: AsyncSession):
    with pytest.raises(AppException) as exc_info:
        await remove_youtube_key(db_session, current_user=EMPLOYEE_USER)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_set_udemy_credential_as_hr_admin_persists_it(db_session: AsyncSession):
    await set_udemy_credential(
        db_session, current_user=HR_ADMIN_USER, client_id="client-1", client_secret="secret-1"
    )

    status = await get_api_keys_status(db_session, current_user=HR_ADMIN_USER)
    assert status.udemy_configured is True
    assert status.udemy_configured_by_id == RITA_ID
    assert status.udemy_configured_at is not None


@pytest.mark.asyncio
async def test_set_udemy_credential_as_employee_raises_403(db_session: AsyncSession):
    with pytest.raises(AppException) as exc_info:
        await set_udemy_credential(
            db_session, current_user=EMPLOYEE_USER, client_id="client-1", client_secret="secret-1"
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_remove_udemy_credential_as_hr_admin_clears_it(db_session: AsyncSession):
    await set_udemy_credential(
        db_session, current_user=HR_ADMIN_USER, client_id="client-1", client_secret="secret-1"
    )

    await remove_udemy_credential(db_session, current_user=HR_ADMIN_USER)

    status = await get_api_keys_status(db_session, current_user=HR_ADMIN_USER)
    assert status.udemy_configured is False


@pytest.mark.asyncio
async def test_remove_udemy_credential_as_employee_raises_403(db_session: AsyncSession):
    with pytest.raises(AppException) as exc_info:
        await remove_udemy_credential(db_session, current_user=EMPLOYEE_USER)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_api_keys_status_as_employee_raises_403(db_session: AsyncSession):
    with pytest.raises(AppException) as exc_info:
        await get_api_keys_status(db_session, current_user=EMPLOYEE_USER)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_api_keys_status_when_nothing_configured_reports_false(db_session: AsyncSession):
    status = await get_api_keys_status(db_session, current_user=HR_ADMIN_USER)

    assert status.youtube_configured is False
    assert status.udemy_configured is False
    assert status.udemy_configured_by_id is None
    assert status.udemy_configured_at is None


# ---------------------------------------------------------------------------
# Live content lookup (Story 6.6, FR-17)
# ---------------------------------------------------------------------------


async def _create_skill(db_session: AsyncSession) -> Skill:
    skill = Skill(
        name=f"Content Lookup Skill {uuid.uuid4().hex[:8]}",
        description="Story 6.6 test skill",
        embedding=[0.1] * 384,
    )
    db_session.add(skill)
    await db_session.flush()
    return skill


def _fake_youtube_search(api_key, query, max_results):
    return [
        {
            "video_id": "yt123",
            "title": "YouTube Result",
            "description": "desc",
            "thumbnail_url": "https://img.example.com/yt123.jpg",
        }
    ]


def _fake_youtube_durations(api_key, video_ids):
    return {"yt123": "PT10M30S"}


def _fake_udemy_search(client_id, client_secret, query, max_results):
    return [
        {
            "course_id": 999,
            "title": "Udemy Result",
            "url": "/course/udemy-result/",
            "thumbnail_url": "https://img.udemy.com/999.jpg",
            "content_info": "5.5 total hours",
        }
    ]


@pytest.mark.asyncio
async def test_search_content_for_skill_happy_path_both_sources(db_session: AsyncSession, monkeypatch):
    skill = await _create_skill(db_session)
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="yt-key")
    await set_udemy_credential(db_session, current_user=HR_ADMIN_USER, client_id="cid", client_secret="csecret")
    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _fake_youtube_search)
    monkeypatch.setattr("app.content.service.youtube_client.get_video_durations", _fake_youtube_durations)
    monkeypatch.setattr("app.content.service.udemy_client.search_courses", _fake_udemy_search)
    monkeypatch.setattr("app.content.service.settings.UDEMY_ORGANIZATION_SUBDOMAIN", "sails")

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Data Visualization"
    )

    assert response.errors == []
    assert len(response.results) == 2
    by_source = {r.source: r for r in response.results}
    assert by_source["YOUTUBE"].title == "YouTube Result"
    assert by_source["YOUTUBE"].url == "https://www.youtube.com/watch?v=yt123"
    assert by_source["YOUTUBE"].duration_hours == pytest.approx(10 / 60 + 30 / 3600)
    assert by_source["UDEMY"].title == "Udemy Result"
    assert by_source["UDEMY"].url == "https://sails.udemy.com/course/udemy-result/"
    assert by_source["UDEMY"].duration_hours == pytest.approx(5.5)


@pytest.mark.asyncio
async def test_search_content_for_skill_youtube_only_configured_udemy_no_credential(
    db_session: AsyncSession, monkeypatch
):
    skill = await _create_skill(db_session)
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="yt-key")
    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _fake_youtube_search)
    monkeypatch.setattr("app.content.service.youtube_client.get_video_durations", _fake_youtube_durations)

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python"
    )

    assert len(response.results) == 1
    assert response.results[0].source == "YOUTUBE"
    assert [e.model_dump() for e in response.errors] == [{"source": "UDEMY", "error": "no_credential"}]


@pytest.mark.asyncio
async def test_search_content_for_skill_neither_configured_reports_both_no_credential(db_session: AsyncSession):
    skill = await _create_skill(db_session)

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python"
    )

    assert response.results == []
    errors_by_source = {e.source: e.error for e in response.errors}
    assert errors_by_source == {"YOUTUBE": "no_credential", "UDEMY": "no_credential"}


@pytest.mark.asyncio
async def test_search_content_for_skill_youtube_quota_does_not_block_udemy(db_session: AsyncSession, monkeypatch):
    skill = await _create_skill(db_session)
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="yt-key")
    await set_udemy_credential(db_session, current_user=HR_ADMIN_USER, client_id="cid", client_secret="csecret")

    def _raise_quota(api_key, query, max_results):
        raise QuotaExceededError("quota exhausted")

    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _raise_quota)
    monkeypatch.setattr("app.content.service.udemy_client.search_courses", _fake_udemy_search)
    monkeypatch.setattr("app.content.service.settings.UDEMY_ORGANIZATION_SUBDOMAIN", "sails")

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python"
    )

    assert len(response.results) == 1
    assert response.results[0].source == "UDEMY"
    assert [e.model_dump() for e in response.errors] == [{"source": "YOUTUBE", "error": "rate_limited"}]


@pytest.mark.asyncio
async def test_search_content_for_skill_udemy_rate_limited_does_not_block_youtube(
    db_session: AsyncSession, monkeypatch
):
    skill = await _create_skill(db_session)
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="yt-key")
    await set_udemy_credential(db_session, current_user=HR_ADMIN_USER, client_id="cid", client_secret="csecret")

    def _raise_rate_limited(client_id, client_secret, query, max_results):
        raise RateLimitExceededError("rate limited")

    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _fake_youtube_search)
    monkeypatch.setattr("app.content.service.youtube_client.get_video_durations", _fake_youtube_durations)
    monkeypatch.setattr("app.content.service.udemy_client.search_courses", _raise_rate_limited)

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python"
    )

    assert len(response.results) == 1
    assert response.results[0].source == "YOUTUBE"
    assert [e.model_dump() for e in response.errors] == [{"source": "UDEMY", "error": "rate_limited"}]


@pytest.mark.asyncio
async def test_search_content_for_skill_youtube_invalid_credential(db_session: AsyncSession, monkeypatch):
    skill = await _create_skill(db_session)
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="revoked-key")

    def _raise_invalid(api_key, query, max_results):
        raise YoutubeInvalidCredentialError("bad key")

    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _raise_invalid)

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python"
    )

    assert {"source": "YOUTUBE", "error": "invalid_credential"} in [e.model_dump() for e in response.errors]


@pytest.mark.asyncio
async def test_search_content_for_skill_udemy_invalid_credential(db_session: AsyncSession, monkeypatch):
    skill = await _create_skill(db_session)
    await set_udemy_credential(db_session, current_user=HR_ADMIN_USER, client_id="bad", client_secret="bad")

    def _raise_invalid(client_id, client_secret, query, max_results):
        raise UdemyInvalidCredentialError("bad credential")

    monkeypatch.setattr("app.content.service.udemy_client.search_courses", _raise_invalid)

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python"
    )

    assert {"source": "UDEMY", "error": "invalid_credential"} in [e.model_dump() for e in response.errors]


@pytest.mark.asyncio
async def test_search_content_for_skill_source_error_on_unexpected_exception(db_session: AsyncSession, monkeypatch):
    skill = await _create_skill(db_session)
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="yt-key")

    def _raise_generic(api_key, query, max_results):
        raise Exception("boom")

    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _raise_generic)

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python"
    )

    assert {"source": "YOUTUBE", "error": "source_error"} in [e.model_dump() for e in response.errors]


@pytest.mark.asyncio
async def test_search_content_for_skill_nonexistent_skill_raises_404(db_session: AsyncSession):
    with pytest.raises(AppException) as exc_info:
        await search_content_for_skill(
            db_session, current_user=HR_ADMIN_USER, skill_id=uuid.uuid4(), query="Python"
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "SKILL_NOT_FOUND"


@pytest.mark.asyncio
async def test_search_content_for_skill_as_employee_raises_403(db_session: AsyncSession):
    skill = await _create_skill(db_session)

    with pytest.raises(AppException) as exc_info:
        await search_content_for_skill(
            db_session, current_user=EMPLOYEE_USER, skill_id=skill.id, query="Python"
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_search_content_for_skill_never_writes_content_catalog(db_session: AsyncSession, monkeypatch):
    """Search-only (AC/Scope Note 9) -- writing only ever happens in
    Story 6.8's (not yet built) approve action."""
    from sqlalchemy import select as sa_select

    skill = await _create_skill(db_session)
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="yt-key")
    await set_udemy_credential(db_session, current_user=HR_ADMIN_USER, client_id="cid", client_secret="csecret")
    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _fake_youtube_search)
    monkeypatch.setattr("app.content.service.youtube_client.get_video_durations", _fake_youtube_durations)
    monkeypatch.setattr("app.content.service.udemy_client.search_courses", _fake_udemy_search)
    monkeypatch.setattr("app.content.service.settings.UDEMY_ORGANIZATION_SUBDOMAIN", "sails")

    await search_content_for_skill(db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python")

    result = await db_session.execute(sa_select(ContentCatalog).where(ContentCatalog.skill_id == skill.id))
    assert result.scalars().all() == []


# ---------------------------------------------------------------------------
# Manual content entry (Story 6.7, FR-17a)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_submit_manual_content_happy_path_with_duration(db_session: AsyncSession):
    skill = await _create_skill(db_session)

    candidate = await submit_manual_content(
        db_session,
        current_user=HR_ADMIN_USER,
        skill_id=skill.id,
        url="https://example.com/a-course",
        title="A Manually Curated Course",
        duration_hours=3.5,
    )

    assert candidate.title == "A Manually Curated Course"
    assert candidate.source == "MANUAL"
    assert candidate.url == "https://example.com/a-course"
    assert candidate.duration_hours == 3.5
    assert not hasattr(candidate, "thumbnail_url")


@pytest.mark.asyncio
async def test_submit_manual_content_happy_path_without_duration(db_session: AsyncSession):
    skill = await _create_skill(db_session)

    candidate = await submit_manual_content(
        db_session,
        current_user=HR_ADMIN_USER,
        skill_id=skill.id,
        url="https://example.com/a-course",
        title="A Manually Curated Course",
        duration_hours=None,
    )

    assert candidate.duration_hours is None


@pytest.mark.asyncio
async def test_submit_manual_content_nonexistent_skill_raises_404(db_session: AsyncSession):
    with pytest.raises(AppException) as exc_info:
        await submit_manual_content(
            db_session,
            current_user=HR_ADMIN_USER,
            skill_id=uuid.uuid4(),
            url="https://example.com/a-course",
            title="A Course",
            duration_hours=None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "SKILL_NOT_FOUND"


@pytest.mark.asyncio
async def test_submit_manual_content_as_employee_raises_403(db_session: AsyncSession):
    skill = await _create_skill(db_session)

    with pytest.raises(AppException) as exc_info:
        await submit_manual_content(
            db_session,
            current_user=EMPLOYEE_USER,
            skill_id=skill.id,
            url="https://example.com/a-course",
            title="A Course",
            duration_hours=None,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_submit_manual_content_never_calls_youtube_or_udemy_client(
    db_session: AsyncSession, monkeypatch
):
    """AC's own requirement -- this path must be proven to never touch
    either source client, same test-level guarantee manual_seed_content()
    already has (Story 2.3)."""
    skill = await _create_skill(db_session)

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("youtube_client/udemy_client must never be called by submit_manual_content")

    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _fail_if_called)
    monkeypatch.setattr("app.content.service.youtube_client.get_video_durations", _fail_if_called)
    monkeypatch.setattr("app.content.service.udemy_client.search_courses", _fail_if_called)

    candidate = await submit_manual_content(
        db_session,
        current_user=HR_ADMIN_USER,
        skill_id=skill.id,
        url="https://example.com/a-course",
        title="A Course",
        duration_hours=None,
    )

    assert candidate.source == "MANUAL"


@pytest.mark.asyncio
async def test_submit_manual_content_never_writes_content_catalog(db_session: AsyncSession):
    from sqlalchemy import select as sa_select

    skill = await _create_skill(db_session)

    await submit_manual_content(
        db_session,
        current_user=HR_ADMIN_USER,
        skill_id=skill.id,
        url="https://example.com/a-course",
        title="A Course",
        duration_hours=None,
    )

    result = await db_session.execute(sa_select(ContentCatalog).where(ContentCatalog.skill_id == skill.id))
    assert result.scalars().all() == []


# ---------------------------------------------------------------------------
# Code review patches (2026-09-10): credential-decrypt isolation, graceful
# duration-lookup degradation, malformed-candidate skipping.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_content_for_skill_youtube_decrypt_failure_reports_source_error_udemy_unaffected(
    db_session: AsyncSession, monkeypatch
):
    """A decrypt_secret() failure fetching the YouTube credential must be
    classified as YOUTUBE source_error, not propagate and 500 the whole
    request -- and must not block Udemy's results (NFR-RES1)."""
    skill = await _create_skill(db_session)
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="yt-key")
    await set_udemy_credential(db_session, current_user=HR_ADMIN_USER, client_id="cid", client_secret="csecret")

    async def _raise_decrypt_failure(db, *, admin_id):
        raise Exception("corrupted ciphertext")

    monkeypatch.setattr("app.content.service.repository.get_decrypted_admin_youtube_key", _raise_decrypt_failure)
    monkeypatch.setattr("app.content.service.udemy_client.search_courses", _fake_udemy_search)
    monkeypatch.setattr("app.content.service.settings.UDEMY_ORGANIZATION_SUBDOMAIN", "sails")

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python"
    )

    assert len(response.results) == 1
    assert response.results[0].source == "UDEMY"
    assert [e.model_dump() for e in response.errors] == [{"source": "YOUTUBE", "error": "source_error"}]


@pytest.mark.asyncio
async def test_search_content_for_skill_udemy_decrypt_failure_does_not_discard_youtube_results(
    db_session: AsyncSession, monkeypatch
):
    """A decrypt failure fetching the Udemy credential (evaluated *after*
    YouTube's results are already computed) must not discard the
    already-successful YOUTUBE results -- the historical bug this patch
    fixes."""
    skill = await _create_skill(db_session)
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="yt-key")
    await set_udemy_credential(db_session, current_user=HR_ADMIN_USER, client_id="cid", client_secret="csecret")
    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _fake_youtube_search)
    monkeypatch.setattr("app.content.service.youtube_client.get_video_durations", _fake_youtube_durations)

    async def _raise_decrypt_failure(db):
        raise Exception("corrupted ciphertext")

    monkeypatch.setattr("app.content.service.repository.get_decrypted_org_udemy_credential", _raise_decrypt_failure)

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python"
    )

    assert len(response.results) == 1
    assert response.results[0].source == "YOUTUBE"
    assert [e.model_dump() for e in response.errors] == [{"source": "UDEMY", "error": "source_error"}]


@pytest.mark.asyncio
async def test_search_content_for_skill_duration_lookup_failure_still_returns_search_results(
    db_session: AsyncSession, monkeypatch
):
    """A get_video_durations() failure after a successful search_videos()
    call must degrade gracefully (duration_hours=None) rather than
    discarding the already-fetched search results."""
    skill = await _create_skill(db_session)
    await set_youtube_key(db_session, current_user=HR_ADMIN_USER, key="yt-key")
    monkeypatch.setattr("app.content.service.youtube_client.search_videos", _fake_youtube_search)

    def _raise_durations_failure(api_key, video_ids):
        raise Exception("network hiccup")

    monkeypatch.setattr("app.content.service.youtube_client.get_video_durations", _raise_durations_failure)

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python"
    )

    assert [e.model_dump() for e in response.errors] == [{"source": "UDEMY", "error": "no_credential"}]
    assert len(response.results) == 1
    assert response.results[0].title == "YouTube Result"
    assert response.results[0].duration_hours is None


@pytest.mark.asyncio
async def test_search_content_for_skill_udemy_result_with_missing_url_is_skipped(
    db_session: AsyncSession, monkeypatch
):
    """A Udemy course result with a missing/None url must be skipped, not
    turned into a garbage link like 'https://sails.udemy.comNone'."""
    skill = await _create_skill(db_session)
    await set_udemy_credential(db_session, current_user=HR_ADMIN_USER, client_id="cid", client_secret="csecret")

    def _udemy_search_with_one_missing_url(client_id, client_secret, query, max_results):
        return [
            {
                "course_id": 1,
                "title": "Good Course",
                "url": "/course/good-course/",
                "thumbnail_url": None,
                "content_info": None,
            },
            {
                "course_id": 2,
                "title": "Broken Course",
                "url": None,
                "thumbnail_url": None,
                "content_info": None,
            },
        ]

    monkeypatch.setattr("app.content.service.udemy_client.search_courses", _udemy_search_with_one_missing_url)
    monkeypatch.setattr("app.content.service.settings.UDEMY_ORGANIZATION_SUBDOMAIN", "sails")

    response = await search_content_for_skill(
        db_session, current_user=HR_ADMIN_USER, skill_id=skill.id, query="Python"
    )

    assert [e.model_dump() for e in response.errors] == [{"source": "YOUTUBE", "error": "no_credential"}]
    assert len(response.results) == 1
    assert response.results[0].title == "Good Course"
    assert response.results[0].url == "https://sails.udemy.com/course/good-course/"


# ---------------------------------------------------------------------------
# Attach content (Story 6.8, FR-18/FR-19). Writes a content_catalog row --
# the actual approve action any candidate (searched or manual) needs.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("source", ["UDEMY", "MANUAL"])
async def test_attach_content_happy_path_with_duration(db_session: AsyncSession, source):
    skill = await _create_skill(db_session)

    response = await attach_content(
        db_session,
        current_user=HR_ADMIN_USER,
        skill_id=skill.id,
        title="A Great Course",
        source=source,
        url="https://example.com/a-course",
        duration_hours=3.5,
    )

    assert isinstance(response, ContentResponse)
    assert response.title == "A Great Course"
    assert response.source == source
    assert response.url == "https://example.com/a-course"
    assert response.type == "VIDEO"

    content_orm = await repository.get_content_by_id(db_session, response.id)
    assert content_orm.skill_id == skill.id
    assert content_orm.origin == "ADMIN_LOOKUP"
    assert content_orm.attached_by == RITA_ID
    # duration_hours: literal per epics AC text. duration (seconds): the key
    # ProgressRepository.parse_duration_seconds/get_video_duration (AD-3's
    # single derivation authority for dashboard Status/percent) actually
    # reads -- without it, every Assignment on this Content would be stuck
    # "In Progress" at 0% forever (review patch, 2026-09-10).
    assert content_orm.content_metadata == {"duration_hours": 3.5, "duration": 12600}
    assert content_orm.embedding is not None


@pytest.mark.asyncio
async def test_attach_content_youtube_source_includes_video_id_for_batch_dedup(db_session: AsyncSession):
    """Review patch (2026-09-10): without video_id in content_metadata,
    ingest_content_for_skill's de-dup check (content_metadata.get("video_id"))
    can't recognize an admin-attached video and would re-ingest it as a
    duplicate row on the next batch run."""
    skill = await _create_skill(db_session)

    response = await attach_content(
        db_session,
        current_user=HR_ADMIN_USER,
        skill_id=skill.id,
        title="A Great Video",
        source="YOUTUBE",
        url="https://www.youtube.com/watch?v=abc123XYZ_",
        duration_hours=1.0,
    )

    content_orm = await repository.get_content_by_id(db_session, response.id)
    assert content_orm.content_metadata == {
        "duration_hours": 1.0,
        "duration": 3600,
        "video_id": "abc123XYZ_",
    }


@pytest.mark.asyncio
async def test_attach_content_youtube_short_url_extracts_video_id(db_session: AsyncSession):
    skill = await _create_skill(db_session)

    response = await attach_content(
        db_session,
        current_user=HR_ADMIN_USER,
        skill_id=skill.id,
        title="A Great Video",
        source="YOUTUBE",
        url="https://youtu.be/abc123XYZ_",
        duration_hours=None,
    )

    content_orm = await repository.get_content_by_id(db_session, response.id)
    assert content_orm.content_metadata == {"video_id": "abc123XYZ_"}


@pytest.mark.asyncio
async def test_attach_content_youtube_unrecognized_url_omits_video_id_without_crashing(db_session: AsyncSession):
    skill = await _create_skill(db_session)

    response = await attach_content(
        db_session,
        current_user=HR_ADMIN_USER,
        skill_id=skill.id,
        title="A Great Video",
        source="YOUTUBE",
        url="https://example.com/not-actually-youtube",
        duration_hours=None,
    )

    content_orm = await repository.get_content_by_id(db_session, response.id)
    assert content_orm.content_metadata is None


@pytest.mark.asyncio
async def test_attach_content_without_duration_omits_metadata(db_session: AsyncSession):
    skill = await _create_skill(db_session)

    response = await attach_content(
        db_session,
        current_user=HR_ADMIN_USER,
        skill_id=skill.id,
        title="A Great Course",
        source="MANUAL",
        url="https://example.com/a-course",
        duration_hours=None,
    )

    content_orm = await repository.get_content_by_id(db_session, response.id)
    assert content_orm.content_metadata is None


@pytest.mark.asyncio
async def test_attach_content_nonexistent_skill_raises_404(db_session: AsyncSession):
    with pytest.raises(AppException) as exc_info:
        await attach_content(
            db_session,
            current_user=HR_ADMIN_USER,
            skill_id=uuid.uuid4(),
            title="A Course",
            source="MANUAL",
            url="https://example.com/a-course",
            duration_hours=None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "SKILL_NOT_FOUND"


@pytest.mark.asyncio
async def test_attach_content_as_employee_raises_403(db_session: AsyncSession):
    skill = await _create_skill(db_session)

    with pytest.raises(AppException) as exc_info:
        await attach_content(
            db_session,
            current_user=EMPLOYEE_USER,
            skill_id=skill.id,
            title="A Course",
            source="MANUAL",
            url="https://example.com/a-course",
            duration_hours=None,
        )

    assert exc_info.value.status_code == 403
