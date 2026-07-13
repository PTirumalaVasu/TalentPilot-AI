"""Pydantic request/response schemas for the dashboard module."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class StatusEnum(str, Enum):
    """Assignment status derived from watch progress or HR override."""

    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class ProvenanceEnum(str, Enum):
    """Signal provenance: what data backs the Status badge (AD-3)."""

    NOT_STARTED = "Not Started"  # No signal at all yet (Story 5.2 consolidation)
    VERIFIED = "Verified"  # Auto-captured from video (verified watch progress)
    SELF_REPORTED = "Self-reported"  # Non-video data, ≤7 days old
    NEEDS_ATTENTION = "Needs Attention"  # Self-reported, >7 days stale
    HR_OVERRIDE = "HR Override"  # Manually set by HR Admin


class AssignmentRowResponse(BaseModel):
    """Single row in the dashboard grid."""

    model_config = ConfigDict(from_attributes=True)

    assignment_id: uuid.UUID
    employee_id: uuid.UUID
    employee_name: str
    employee_group: str | None
    skill_id: uuid.UUID
    skill_name: str
    status: Literal["Not Started", "In Progress", "Completed"]
    status_percentage: int | None  # e.g., 45 for "In Progress (45%)"
    provenance: Literal["Not Started", "Verified", "Self-reported", "Needs Attention", "HR Override"]
    last_updated: datetime  # ISO-8601, server-side; frontend converts to relative
    assignment_created_at: datetime  # ISO-8601, for sorting/pagination


class DashboardResponse(BaseModel):
    """Response for GET /api/dashboard — HR Admin's full assignment dashboard."""

    assignments: list[AssignmentRowResponse]
    total_count: int
    page: int
    page_size: int
