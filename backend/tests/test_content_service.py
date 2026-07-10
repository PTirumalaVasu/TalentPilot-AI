"""Tests for content service layer (ORM → Pydantic conversion, cross-module API)."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import ContentCatalog, Skill
from app.content.service import get_content, list_content_for_skill
from app.content.schemas import ContentResponse


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
    await db_session.commit()

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
    await db_session.commit()

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
    await db_session.commit()

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
    await db_session.commit()

    # Test service method
    result = await get_content(db_session, content.id)

    assert result is not None
    # Pydantic field is 'metadata', ORM field is 'content_metadata'
    assert result.metadata == {
        "video_id": "mapping_test",
        "duration": 1200,
        "views": 1000,
    }
