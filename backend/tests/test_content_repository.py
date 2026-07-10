"""Tests for content repository layer (AD-1 single-owner enforcement)."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import ContentCatalog, Skill
from app.content.repository import (
    get_content_by_id,
    list_content_by_skill,
    create_content,
)


@pytest.mark.asyncio
async def test_get_content_by_id_returns_orm_instance(db_session: AsyncSession):
    """get_content_by_id should return ContentCatalog ORM instance for existing ID."""
    # Create a test skill first with unique name
    unique_name = f"Test Skill for Content {uuid.uuid4().hex[:8]}"
    skill = Skill(
        name=unique_name,
        description="Test skill",
        embedding=[0.1] * 384,
    )
    db_session.add(skill)
    await db_session.flush()

    # Create a test content
    content = ContentCatalog(
        skill_id=skill.id,
        title="Test Video Content",
        description="Test description",
        type="VIDEO",
        url="https://youtube.com/watch?v=test123",
        embedding=[0.2] * 384,
        source="YOUTUBE",
        content_metadata={"video_id": "test123", "duration": 600},
    )
    db_session.add(content)
    await db_session.flush()

    # Test repository method
    result = await get_content_by_id(db_session, content.id)

    assert result is not None
    assert isinstance(result, ContentCatalog)
    assert result.id == content.id
    assert result.title == "Test Video Content"
    assert result.type == "VIDEO"
    assert result.source == "YOUTUBE"


@pytest.mark.asyncio
async def test_get_content_by_id_returns_none_for_nonexistent(
    db_session: AsyncSession,
):
    """get_content_by_id should return None for non-existent ID."""
    fake_id = uuid.uuid4()

    result = await get_content_by_id(db_session, fake_id)

    assert result is None


@pytest.mark.asyncio
async def test_list_content_by_skill_returns_list_of_orm(db_session: AsyncSession):
    """list_content_by_skill should return list of ContentCatalog for matching skill."""
    # Create test skill with unique name
    unique_name = f"Data Visualization Test {uuid.uuid4().hex[:8]}"
    skill = Skill(
        name=unique_name,
        description="Test skill",
        embedding=[0.1] * 384,
    )
    db_session.add(skill)
    await db_session.flush()

    # Create multiple content items for this skill
    content1 = ContentCatalog(
        skill_id=skill.id,
        title="Video 1",
        description="First video",
        type="VIDEO",
        url="https://youtube.com/watch?v=vid1",
        embedding=[0.2] * 384,
        source="YOUTUBE",
        content_metadata={"video_id": "vid1"},
    )
    content2 = ContentCatalog(
        skill_id=skill.id,
        title="Document 1",
        description="First document",
        type="DOCUMENT",
        url="https://example.com/doc1.pdf",
        embedding=[0.3] * 384,
        source="MANUAL",
        content_metadata=None,
    )
    db_session.add_all([content1, content2])
    await db_session.flush()

    # Test repository method
    results = await list_content_by_skill(db_session, skill.id)

    assert len(results) == 2
    assert all(isinstance(c, ContentCatalog) for c in results)
    assert all(c.skill_id == skill.id for c in results)

    titles = {c.title for c in results}
    assert "Video 1" in titles
    assert "Document 1" in titles


@pytest.mark.asyncio
async def test_list_content_by_skill_returns_empty_for_skill_with_no_content(
    db_session: AsyncSession,
):
    """list_content_by_skill should return empty list for skill with no content."""
    # Create skill with no content and unique name
    unique_name = f"Empty Skill {uuid.uuid4().hex[:8]}"
    skill = Skill(
        name=unique_name,
        description="Skill with no content",
        embedding=[0.1] * 384,
    )
    db_session.add(skill)
    await db_session.flush()

    # Test repository method
    results = await list_content_by_skill(db_session, skill.id)

    assert results == []


@pytest.mark.asyncio
async def test_create_content_persists_and_returns_orm(db_session: AsyncSession):
    """create_content should persist content to DB and return ORM instance."""
    # Create test skill with unique name
    unique_name = f"Python Programming Test {uuid.uuid4().hex[:8]}"
    skill = Skill(
        name=unique_name,
        description="Python skill",
        embedding=[0.1] * 384,
    )
    db_session.add(skill)
    await db_session.flush()

    # Prepare content data
    content_data = {
        "skill_id": skill.id,
        "title": "Python Tutorial Video",
        "description": "Learn Python basics",
        "type": "VIDEO",
        "url": "https://youtube.com/watch?v=python101",
        "embedding": [0.4] * 384,
        "source": "YOUTUBE",
        "content_metadata": {"video_id": "python101", "duration": 1200},
    }

    # Test repository method
    result = await create_content(db_session, content_data)

    assert result is not None
    assert isinstance(result, ContentCatalog)
    assert result.id is not None  # UUID assigned
    assert result.title == "Python Tutorial Video"
    assert result.skill_id == skill.id
    assert result.type == "VIDEO"
    assert result.source == "YOUTUBE"
    assert result.content_metadata == {"video_id": "python101", "duration": 1200}
    assert len(result.embedding) == 384

    # Verify it was actually persisted
    await db_session.refresh(result)
    assert result.id is not None
