"""Tests for content module Pydantic schemas."""
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.content.schemas import (
    AttachContentRequest,
    ContentResponse,
    ContentWithEmbedding,
    EmbeddingInput,
    EmbeddingOutput,
    ManualContentCandidate,
    ManualContentEntryRequest,
)


def test_content_response_excludes_embedding():
    """ContentResponse schema should NOT include embedding field."""
    # Create a mock data dict as if from ORM
    content_data = {
        "id": uuid.uuid4(),
        "skill_id": uuid.uuid4(),
        "title": "Test Video",
        "description": "Test description",
        "type": "VIDEO",
        "url": "https://youtube.com/watch?v=test",
        "source": "YOUTUBE",
        "ingested_at": datetime.now(timezone.utc),
        "metadata": {"video_id": "test123", "duration": 600},
        "embedding": [0.1] * 384,  # This should be excluded
    }

    response = ContentResponse.model_validate(content_data)

    # Assert embedding field does NOT exist in the response
    assert not hasattr(response, "embedding")

    # Assert all expected fields are present
    assert response.id == content_data["id"]
    assert response.skill_id == content_data["skill_id"]
    assert response.title == "Test Video"
    assert response.type == "VIDEO"
    assert response.source == "YOUTUBE"
    assert response.metadata == {"video_id": "test123", "duration": 600}


def test_content_with_embedding_includes_embedding():
    """ContentWithEmbedding schema SHOULD include 384-dim embedding field."""
    content_data = {
        "id": uuid.uuid4(),
        "skill_id": uuid.uuid4(),
        "title": "Test Video",
        "description": "Test description",
        "type": "VIDEO",
        "url": "https://youtube.com/watch?v=test",
        "source": "YOUTUBE",
        "ingested_at": datetime.now(timezone.utc),
        "metadata": {"video_id": "test123"},
        "embedding": [0.1] * 384,
    }

    response = ContentWithEmbedding.model_validate(content_data)

    # Assert embedding field EXISTS and has 384 elements
    assert hasattr(response, "embedding")
    assert response.embedding is not None
    assert len(response.embedding) == 384
    assert all(isinstance(x, float) for x in response.embedding)

    # Also has all base ContentResponse fields
    assert response.title == "Test Video"
    assert response.type == "VIDEO"


def test_embedding_input_schema():
    """EmbeddingInput schema should accept text field."""
    input_data = {"text": "Data Visualization Fundamentals"}

    embedding_input = EmbeddingInput.model_validate(input_data)

    assert embedding_input.text == "Data Visualization Fundamentals"


def test_embedding_output_schema():
    """EmbeddingOutput schema should contain embedding and echo text."""
    output_data = {
        "embedding": [0.5] * 384,
        "text": "Data Visualization Fundamentals",
    }

    embedding_output = EmbeddingOutput.model_validate(output_data)

    assert len(embedding_output.embedding) == 384
    assert embedding_output.text == "Data Visualization Fundamentals"
    assert all(isinstance(x, float) for x in embedding_output.embedding)


def test_content_response_type_field_validation():
    """ContentResponse type field should only accept valid enum values."""
    valid_content = {
        "id": uuid.uuid4(),
        "skill_id": uuid.uuid4(),
        "title": "Test",
        "description": None,
        "type": "DOCUMENT",  # Valid
        "url": "https://example.com/doc.pdf",
        "source": "MANUAL",
        "ingested_at": datetime.now(timezone.utc),
        "metadata": None,
    }

    response = ContentResponse.model_validate(valid_content)
    assert response.type == "DOCUMENT"

    # Invalid type should fail validation
    invalid_content = valid_content.copy()
    invalid_content["type"] = "INVALID_TYPE"

    with pytest.raises(ValidationError):
        ContentResponse.model_validate(invalid_content)


@pytest.mark.parametrize("source", ["YOUTUBE", "UDEMY", "MANUAL"])
def test_content_response_source_field_validation(source):
    """ContentResponse source field accepts YOUTUBE, UDEMY (Story 6.8), or
    MANUAL -- and rejects anything else."""
    valid_content = {
        "id": uuid.uuid4(),
        "skill_id": uuid.uuid4(),
        "title": "Test",
        "description": None,
        "type": "VIDEO",
        "url": "https://youtube.com/watch?v=test",
        "source": source,
        "ingested_at": datetime.now(timezone.utc),
        "metadata": None,
    }

    response = ContentResponse.model_validate(valid_content)
    assert response.source == source

    # Invalid source should fail validation
    invalid_content = valid_content.copy()
    invalid_content["source"] = "VIMEO"

    with pytest.raises(ValidationError):
        ContentResponse.model_validate(invalid_content)


# ---------------------------------------------------------------------------
# Manual content entry (Story 6.7, FR-17a).
# ---------------------------------------------------------------------------


def test_manual_content_entry_request_accepts_valid_url():
    request = ManualContentEntryRequest(
        url="https://example.com/a-course", title="A Course", duration_hours=2.5
    )
    assert request.url == "https://example.com/a-course"
    assert request.title == "A Course"
    assert request.duration_hours == 2.5


def test_manual_content_entry_request_duration_hours_optional():
    request = ManualContentEntryRequest(url="https://example.com/a-course", title="A Course")
    assert request.duration_hours is None


@pytest.mark.parametrize(
    "bad_url",
    [
        "not-a-url",
        "example.com/no-scheme",
        "ftp://example.com/file",  # wrong scheme
        "https://",  # no netloc
        "",
    ],
)
def test_manual_content_entry_request_rejects_malformed_url(bad_url):
    with pytest.raises(ValidationError):
        ManualContentEntryRequest(url=bad_url, title="A Course")


def test_manual_content_entry_request_rejects_blank_title():
    with pytest.raises(ValidationError):
        ManualContentEntryRequest(url="https://example.com/a-course", title="   ")


def test_manual_content_entry_request_rejects_unknown_field():
    with pytest.raises(ValidationError):
        ManualContentEntryRequest(
            url="https://example.com/a-course", title="A Course", thumbnail_url="https://example.com/x.png"
        )


@pytest.mark.parametrize("bad_duration", [-1, -0.5, 0])
def test_manual_content_entry_request_rejects_non_positive_duration(bad_duration):
    """Code review (2026-09-10): a direct API call could submit a negative
    or zero duration_hours, which the frontend's numeric-only parser can
    never produce but the schema didn't guard against -- would echo straight
    back and render as a nonsensical negative/zero days-to-complete."""
    with pytest.raises(ValidationError):
        ManualContentEntryRequest(url="https://example.com/a-course", title="A Course", duration_hours=bad_duration)


def test_manual_content_entry_request_rejects_url_over_max_length():
    """Code review (2026-09-10): MANUAL_URL_MAX_LENGTH (2048) was defined
    but never actually tested."""
    too_long_url = "https://example.com/" + ("a" * 2048)
    with pytest.raises(ValidationError):
        ManualContentEntryRequest(url=too_long_url, title="A Course")


def test_manual_content_entry_request_accepts_url_at_max_length():
    at_limit_url = "https://example.com/" + ("a" * (2048 - len("https://example.com/")))
    assert len(at_limit_url) == 2048
    request = ManualContentEntryRequest(url=at_limit_url, title="A Course")
    assert request.url == at_limit_url


def test_manual_content_candidate_has_no_thumbnail_url_field():
    candidate = ManualContentCandidate(
        title="A Course", source="MANUAL", url="https://example.com/a-course", duration_hours=None
    )
    assert candidate.source == "MANUAL"
    assert "thumbnail_url" not in ManualContentCandidate.model_fields


# ---------------------------------------------------------------------------
# Attach content (Story 6.8, FR-18).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("source", ["YOUTUBE", "UDEMY", "MANUAL"])
def test_attach_content_request_accepts_valid_sources(source):
    request = AttachContentRequest(
        skill_id=uuid.uuid4(),
        title="A Course",
        source=source,
        url="https://example.com/a-course",
        duration_hours=2.5,
    )
    assert request.source == source
    assert request.duration_hours == 2.5


def test_attach_content_request_duration_hours_optional():
    request = AttachContentRequest(
        skill_id=uuid.uuid4(), title="A Course", source="MANUAL", url="https://example.com/a-course"
    )
    assert request.duration_hours is None


def test_attach_content_request_rejects_invalid_source():
    with pytest.raises(ValidationError):
        AttachContentRequest(
            skill_id=uuid.uuid4(), title="A Course", source="VIMEO", url="https://example.com/a-course"
        )


def test_attach_content_request_rejects_blank_title():
    with pytest.raises(ValidationError):
        AttachContentRequest(
            skill_id=uuid.uuid4(), title="   ", source="MANUAL", url="https://example.com/a-course"
        )


@pytest.mark.parametrize(
    "bad_url",
    ["not-a-url", "example.com/no-scheme", "ftp://example.com/file", "https://", ""],
)
def test_attach_content_request_rejects_malformed_url(bad_url):
    with pytest.raises(ValidationError):
        AttachContentRequest(skill_id=uuid.uuid4(), title="A Course", source="MANUAL", url=bad_url)


@pytest.mark.parametrize("bad_duration", [-1, -0.5, 0])
def test_attach_content_request_rejects_non_positive_duration(bad_duration):
    with pytest.raises(ValidationError):
        AttachContentRequest(
            skill_id=uuid.uuid4(),
            title="A Course",
            source="MANUAL",
            url="https://example.com/a-course",
            duration_hours=bad_duration,
        )


def test_attach_content_request_rejects_unknown_field():
    with pytest.raises(ValidationError):
        AttachContentRequest(
            skill_id=uuid.uuid4(),
            title="A Course",
            source="MANUAL",
            url="https://example.com/a-course",
            type="VIDEO",
        )
