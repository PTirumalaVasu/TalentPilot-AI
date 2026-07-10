"""Pydantic request/response schemas for the progress module."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecordWatchProgressRequest(BaseModel):
    """Request to record a watch position update."""

    assignment_id: UUID = Field(..., description="Assignment ID for this progress record")
    watch_position: int = Field(..., ge=0, description="Watch position in seconds")
    event_time: datetime = Field(..., description="ISO-8601 timestamp when position was observed (client time)")
    video_url: str = Field(..., description="Video URL for server-side anti-spoofing validation")


class SkillProgressResponse(BaseModel):
    """Response with a watch progress record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Progress record ID")
    assignment_id: UUID = Field(..., description="Assignment ID")
    watch_position: int = Field(..., description="Current watch position in seconds")
    event_time: datetime = Field(..., description="Event timestamp (client time of observation)")
    verified: bool = Field(..., description="True if passed server-side anti-spoofing checks")
    updated_at: datetime = Field(..., description="Server time when record was persisted")
