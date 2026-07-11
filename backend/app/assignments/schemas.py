"""Pydantic request/response schemas for the assignments module."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.content.schemas import ContentResponse


class AssignmentStatus(str, Enum):
    """Mirrors the existing `status_enum` Postgres type (assignments/models.py's
    AssignmentOverride.override_status) — reused rather than defining a second
    enum, per Story 1.7's DuplicateObjectError lesson."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class CreateAssignmentRequest(BaseModel):
    # extra="forbid": AC3's "status/provenance are never client-supplied" must
    # be an enforced contract, not just an omission from this field list.
    model_config = ConfigDict(extra="forbid")

    employee_id: uuid.UUID
    skill_id: uuid.UUID


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    skill_id: uuid.UUID
    content_id: uuid.UUID | None
    assigned_at: datetime
    assigned_by: uuid.UUID
    status: AssignmentStatus
    # Plain string, not an enum column: Provenance has no DB representation
    # anywhere in the schema (compute-on-read only, owned by progress/ per AD-3).
    provenance: str


class AssignmentContentItem(BaseModel):
    """One row in the Employee's own Content Discovery grid (Story 2.5, FR-4).
    `content` is the live-matched recommendation (Story 2.4's
    match_content_for_skill), not a join through Assignment.content_id --
    that column is always NULL until Story 3.4/3.5 ship."""

    assignment_id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str
    content: ContentResponse | None
    watch_position: int
    status: Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETED"]
    group: Literal["TO_START", "IN_PROGRESS"]


class MyAssignmentsResponse(BaseModel):
    """Response for GET /api/assignments (Story 2.5, EMPLOYEE-only -- see
    assignments/service.py::list_my_assignments)."""

    total: int
    in_progress_count: int
    to_start_count: int
    assignments: list[AssignmentContentItem]
