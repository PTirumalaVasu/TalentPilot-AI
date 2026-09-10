"""Tests for content service layer (ORM → Pydantic conversion, cross-module API)."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import ContentCatalog
from app.auth.schemas import CurrentUser, Role
from app.core.errors import AppException
from app.core.seed_ids import CASEY_ID, RITA_ID
from app.skills.models import Skill
from app.content.service import (
    get_api_keys_status,
    get_content,
    list_content_for_skill,
    remove_udemy_credential,
    remove_youtube_key,
    set_udemy_credential,
    set_youtube_key,
)
from app.content.schemas import ContentResponse

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
