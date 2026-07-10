"""Pydantic request/response schemas for the content module."""
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContentResponse(BaseModel):
    """Default public API response for content (excludes embedding for performance)."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    skill_id: UUID
    title: str
    description: str | None
    type: Literal["VIDEO", "DOCUMENT", "WEBSITE"]
    url: str
    source: Literal["YOUTUBE", "MANUAL"]
    ingested_at: datetime
    metadata: dict[str, Any] | None = Field(alias="content_metadata")


class ContentWithEmbedding(ContentResponse):
    """Content response WITH 384-dim embedding (debug/admin only, not default)."""

    embedding: list[float]


class EmbeddingInput(BaseModel):
    """Input schema for embedding computation (internal use, Story 2.2)."""

    text: str


class EmbeddingOutput(BaseModel):
    """Output schema for embedding computation (internal use, Story 2.2)."""

    embedding: list[float]
    text: str  # Echo back for verification


class ManualContentCreate(BaseModel):
    """Input schema for manual content seeding via the CLI (Story 2.3, AC5).
    Bypasses youtube_client entirely -- no YouTube API call is ever made
    for this path. `source` is pinned to "MANUAL" (not caller-configurable):
    manual_seed_content always writes content_metadata=None, so a row
    claiming source="YOUTUBE" here would have no video_id and be invisible
    to ingest_content_for_skill's de-dup check, risking a future duplicate
    insert of the same video by a real ingestion run."""

    skill_id: UUID
    title: str
    url: str
    type: Literal["VIDEO", "DOCUMENT", "WEBSITE"]
    description: str | None = None
    source: Literal["MANUAL"] = "MANUAL"
