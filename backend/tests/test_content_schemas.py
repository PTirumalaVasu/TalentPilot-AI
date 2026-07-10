"""Tests for content module Pydantic schemas."""
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.content.schemas import (
    ContentResponse,
    ContentWithEmbedding,
    EmbeddingInput,
    EmbeddingOutput,
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


def test_content_response_source_field_validation():
    """ContentResponse source field should only accept YOUTUBE or MANUAL."""
    valid_content = {
        "id": uuid.uuid4(),
        "skill_id": uuid.uuid4(),
        "title": "Test",
        "description": None,
        "type": "VIDEO",
        "url": "https://youtube.com/watch?v=test",
        "source": "MANUAL",  # Valid
        "ingested_at": datetime.now(timezone.utc),
        "metadata": None,
    }

    response = ContentResponse.model_validate(valid_content)
    assert response.source == "MANUAL"

    # Invalid source should fail validation
    invalid_content = valid_content.copy()
    invalid_content["source"] = "VIMEO"

    with pytest.raises(ValidationError):
        ContentResponse.model_validate(invalid_content)
