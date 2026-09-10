"""Tests for content repository layer (AD-1 single-owner enforcement)."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import ContentCatalog
from app.core.seed_ids import CASEY_ID, RITA_ID
from app.skills.models import Skill
from app.content.repository import (
    get_content_by_id,
    list_content_by_skill,
    create_content,
    delete_admin_api_key,
    delete_org_api_credential,
    get_admin_api_key,
    get_decrypted_admin_youtube_key,
    get_decrypted_org_udemy_credential,
    get_org_api_credential,
    upsert_admin_api_key,
    upsert_org_api_credential,
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


# ---------------------------------------------------------------------------
# Admin/org API credential storage (AD-10, Story 6.5)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_admin_api_key_then_get_round_trips(db_session: AsyncSession):
    await upsert_admin_api_key(db_session, admin_id=RITA_ID, source="YOUTUBE", plaintext_key="my-yt-key")

    row = await get_admin_api_key(db_session, admin_id=RITA_ID, source="YOUTUBE")

    assert row is not None
    assert row.admin_id == RITA_ID
    assert row.source == "YOUTUBE"
    # Never stored in plaintext.
    assert row.encrypted_key != "my-yt-key"


@pytest.mark.asyncio
async def test_upsert_admin_api_key_twice_replaces_not_duplicates(db_session: AsyncSession):
    await upsert_admin_api_key(db_session, admin_id=RITA_ID, source="YOUTUBE", plaintext_key="first-key")
    await upsert_admin_api_key(db_session, admin_id=RITA_ID, source="YOUTUBE", plaintext_key="second-key")

    row = await get_admin_api_key(db_session, admin_id=RITA_ID, source="YOUTUBE")

    from app.core.secrets import decrypt_secret

    assert decrypt_secret(row.encrypted_key) == "second-key"


@pytest.mark.asyncio
async def test_get_admin_api_key_returns_none_when_not_configured(db_session: AsyncSession):
    row = await get_admin_api_key(db_session, admin_id=CASEY_ID, source="YOUTUBE")
    assert row is None


@pytest.mark.asyncio
async def test_delete_admin_api_key_removes_the_row(db_session: AsyncSession):
    await upsert_admin_api_key(db_session, admin_id=RITA_ID, source="YOUTUBE", plaintext_key="a-key")

    await delete_admin_api_key(db_session, admin_id=RITA_ID, source="YOUTUBE")

    assert await get_admin_api_key(db_session, admin_id=RITA_ID, source="YOUTUBE") is None


@pytest.mark.asyncio
async def test_delete_admin_api_key_for_nonexistent_row_does_not_raise(db_session: AsyncSession):
    await delete_admin_api_key(db_session, admin_id=RITA_ID, source="YOUTUBE")


@pytest.mark.asyncio
async def test_upsert_org_api_credential_then_get_round_trips(db_session: AsyncSession):
    await upsert_org_api_credential(
        db_session, source="UDEMY", client_id="client-abc", client_secret="secret-xyz", configured_by=RITA_ID
    )

    row = await get_org_api_credential(db_session, source="UDEMY")

    assert row is not None
    assert row.source == "UDEMY"
    assert row.configured_by == RITA_ID
    assert row.encrypted_key != "client-abc"
    assert row.encrypted_key != "secret-xyz"


@pytest.mark.asyncio
async def test_upsert_org_api_credential_packs_both_fields_into_one_encrypted_blob(db_session: AsyncSession):
    import json

    from app.core.secrets import decrypt_secret

    await upsert_org_api_credential(
        db_session, source="UDEMY", client_id="client-abc", client_secret="secret-xyz", configured_by=RITA_ID
    )

    row = await get_org_api_credential(db_session, source="UDEMY")
    decrypted = json.loads(decrypt_secret(row.encrypted_key))

    assert decrypted == {"client_id": "client-abc", "client_secret": "secret-xyz"}


@pytest.mark.asyncio
async def test_upsert_org_api_credential_replaces_regardless_of_who_configured_it_before(db_session: AsyncSession):
    await upsert_org_api_credential(
        db_session, source="UDEMY", client_id="first-id", client_secret="first-secret", configured_by=RITA_ID
    )
    # A different admin (Casey -- role doesn't matter at the repository
    # layer, only the FK) replaces the same org-wide row.
    await upsert_org_api_credential(
        db_session, source="UDEMY", client_id="second-id", client_secret="second-secret", configured_by=CASEY_ID
    )

    row = await get_org_api_credential(db_session, source="UDEMY")

    assert row.configured_by == CASEY_ID


@pytest.mark.asyncio
async def test_get_org_api_credential_returns_none_when_not_configured(db_session: AsyncSession):
    row = await get_org_api_credential(db_session, source="UDEMY")
    assert row is None


@pytest.mark.asyncio
async def test_delete_org_api_credential_removes_the_row(db_session: AsyncSession):
    await upsert_org_api_credential(
        db_session, source="UDEMY", client_id="id", client_secret="secret", configured_by=RITA_ID
    )

    await delete_org_api_credential(db_session, source="UDEMY")

    assert await get_org_api_credential(db_session, source="UDEMY") is None


@pytest.mark.asyncio
async def test_delete_org_api_credential_for_nonexistent_row_does_not_raise(db_session: AsyncSession):
    await delete_org_api_credential(db_session, source="UDEMY")


# ---------------------------------------------------------------------------
# Story 6.6: decrypt-and-return credential functions -- the first callers
# in this codebase to call decrypt_secret() in a live code path (Story 6.5
# Dev Notes' explicit forward note).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_decrypted_admin_youtube_key_returns_plaintext_when_configured(db_session: AsyncSession):
    await upsert_admin_api_key(db_session, admin_id=RITA_ID, source="YOUTUBE", plaintext_key="my-real-yt-key")

    key = await get_decrypted_admin_youtube_key(db_session, admin_id=RITA_ID)

    assert key == "my-real-yt-key"


@pytest.mark.asyncio
async def test_get_decrypted_admin_youtube_key_returns_none_when_not_configured(db_session: AsyncSession):
    key = await get_decrypted_admin_youtube_key(db_session, admin_id=CASEY_ID)

    assert key is None


@pytest.mark.asyncio
async def test_get_decrypted_org_udemy_credential_returns_both_fields_when_configured(db_session: AsyncSession):
    await upsert_org_api_credential(
        db_session, source="UDEMY", client_id="real-client-id", client_secret="real-client-secret", configured_by=RITA_ID
    )

    credential = await get_decrypted_org_udemy_credential(db_session)

    assert credential == {"client_id": "real-client-id", "client_secret": "real-client-secret"}


@pytest.mark.asyncio
async def test_get_decrypted_org_udemy_credential_returns_none_when_not_configured(db_session: AsyncSession):
    credential = await get_decrypted_org_udemy_credential(db_session)

    assert credential is None
