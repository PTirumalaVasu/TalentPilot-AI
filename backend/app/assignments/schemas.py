"""Pydantic request/response schemas for the assignments module."""
import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class AssignmentStatus(str, Enum):
    """Mirrors the existing `status_enum` Postgres type (assignments/models.py's
    AssignmentOverride.override_status) — reused rather than defining a second
    enum, per Story 1.7's DuplicateObjectError lesson.

    CAUTION: shares the literal value "NOT_STARTED" with ProvenanceLabel.NOT_STARTED
    below. Because both are `str, Enum`, they compare equal and hash equal
    across the two types (`AssignmentStatus.NOT_STARTED == ProvenanceLabel.NOT_STARTED`
    is `True`) — never rely on `==`/set/dict membership to distinguish which
    axis a value came from; check the type explicitly instead."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ProvenanceLabel(str, Enum):
    """Provenance axis (AD-3: a conceptually separate axis from AssignmentStatus,
    intended to never be merged into one display value — see CAUTION below for
    a real gap in that guarantee). Story 5.3 defines this enum and derives
    NOT_STARTED/SELF_REPORTED/NEEDS_ATTENTION from self-reported staleness
    (see progress/service.py::derive_self_reported_provenance). VERIFIED
    (Story 5.2, video-signal case) and HR_OVERRIDE (Story 5.5,
    AssignmentOverride-backed case) are intentionally not yet members here —
    add them to this same enum when those stories build their derivations,
    rather than introducing a second, competing Provenance type.

    CAUTION: NOT_STARTED shares its literal value with AssignmentStatus.NOT_STARTED
    above — as a `str, Enum`, this member compares equal and hashes equal to
    that one across the two types. The type system does not enforce the
    "orthogonal, never merged" intent by itself; a naive `==`/set/dict check
    mixing the two enums would silently conflate them (confirmed via direct
    Python check, code review of Story 5.3, 2026-07-11)."""

    NOT_STARTED = "NOT_STARTED"
    SELF_REPORTED = "SELF_REPORTED"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    role: str


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None


class CreateAssignmentRequest(BaseModel):
    # extra="forbid": AC3's "status/provenance are never client-supplied" must
    # be an enforced contract, not just an omission from this field list.
    model_config = ConfigDict(extra="forbid")

    employee_id: uuid.UUID
    skill_id: uuid.UUID
    # Optional: the AI-matched content id from Step 3's content review
    # (Story 3.4). None when no content matched or [Assign without content]
    # was used (AC6) — never required.
    content_id: uuid.UUID | None = None


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


class DashboardAssignmentRow(BaseModel):
    """A single Assignment row for the HR dashboard list (Story 3.5).

    `status`/`progress_percent`/`provenance` are derived per-row from real
    `skill_progress` data (via `ProgressService.derive_dashboard_status_and_percent`,
    AD-3: `progress/` is the sole derivation authority) — not the earlier
    hardcoded placeholder. Real per-assignment Status derivation was pulled
    forward from Epic 5/Story 5.1 at the user's request to visually match
    the WDS prototype's dashboard; this is still not the final grid (no
    Provenance drill-down, no Needs-Attention staleness threshold, no live
    10-15s auto-polling — those remain Story 5.2/5.3/5.4's job). Distinct
    from AssignmentResponse because this is a display-oriented read model
    (adds employee_name/skill_name/progress_percent), not a mutation-response
    echo — AssignmentResponse intentionally carries only ids, matching what
    Story 3.4's create/duplicate-check callers need.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    employee_name: str
    skill_id: uuid.UUID
    skill_name: str
    assigned_at: datetime
    status: AssignmentStatus
    progress_percent: int
    provenance: str
