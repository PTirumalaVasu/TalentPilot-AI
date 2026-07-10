"""Pydantic request/response schemas for the assignments module."""
import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


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
