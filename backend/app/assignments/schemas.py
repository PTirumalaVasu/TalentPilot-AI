"""Pydantic request/response schemas for the assignments module."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.content.schemas import ContentResponse


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
    a real gap in that guarantee). Story 5.3 defined this enum and derives
    NOT_STARTED/SELF_REPORTED/NEEDS_ATTENTION from self-reported staleness
    (see progress/service.py::derive_self_reported_provenance). Story 5.2 adds
    VERIFIED (video-signal case, see progress/service.py::get_provenance_detail).
    HR_OVERRIDE (Story 5.5, AssignmentOverride-backed case) is intentionally
    not yet a member here — Story 5.2's HR-Override display branch keys off
    AssignmentOverride.active directly rather than adding a member for a
    record type this story only reads, never creates; add HR_OVERRIDE when
    Story 5.5 builds the create/reverse mutation path.

    CAUTION: NOT_STARTED shares its literal value with AssignmentStatus.NOT_STARTED
    above — as a `str, Enum`, this member compares equal and hashes equal to
    that one across the two types. The type system does not enforce the
    "orthogonal, never merged" intent by itself; a naive `==`/set/dict check
    mixing the two enums would silently conflate them (confirmed via direct
    Python check, code review of Story 5.3, 2026-07-11)."""

    NOT_STARTED = "NOT_STARTED"
    SELF_REPORTED = "SELF_REPORTED"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    VERIFIED = "VERIFIED"


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


class SetOverrideRequest(BaseModel):
    """Request for POST /api/assignments/{assignment_id}/override (Story 5.5,
    AC3/AC6). No status field: override_status is always server-derived
    (COMPLETED) -- the request contract has no way for HR to pick a
    different one."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["set", "unset"]
    reason: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _reason_only_valid_for_set(self) -> "SetOverrideRequest":
        """A reversal (`unset`) has no column to persist a reason against
        (Table 7's `reversed_at`/`reversed_by` carry no `reversed_reason`) --
        code review finding, Story 5.5: reject rather than silently drop a
        caller-supplied reason on this action."""
        if self.action == "unset" and self.reason is not None and self.reason.strip():
            raise ValueError("reason is not supported for action='unset'")
        return self


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


class DrillDownResponse(BaseModel):
    """Response for GET /api/assignments/{assignment_id}/progress/drill-down
    (Story 5.2, HR_ADMIN-only). Flat shape with optional fields rather than a
    discriminated union -- the frontend renders conditionally per `provenance`
    (mirrors this codebase's existing style, e.g. SkillProgressResponseResume's
    nullable-fields approach). `status`/`provenance`/`last_updated` come from
    the same `ProgressService.get_provenance_detail` call the dashboard grid
    uses (AR-3), so a row's grid badge and its drill-down detail can never
    disagree on Status or Provenance -- the actual AR-3 consolidation goal.

    CAUTION: this guarantee does NOT extend to `status_percentage` specifically.
    The dashboard grid (`AssignmentRowResponse.status_percentage`) nulls it
    unless `status == "In Progress"` (Story 5.1's own display convention);
    this endpoint passes `get_provenance_detail`'s raw percentage through
    unguarded, since AC4 requires the Verified branch to always show "Watch
    Progress: {pct}%" (including 100% for Completed). A Completed/Verified
    assignment can therefore legitimately show `status_percentage: null` on
    the grid and `100` here for the same assignment -- by design, not drift
    (code review finding, Story 5-2)."""

    model_config = ConfigDict(from_attributes=True)

    assignment_id: uuid.UUID
    employee_name: str
    skill_name: str
    status: AssignmentStatus
    status_percentage: int | None
    provenance: Literal["Not Started", "Verified", "Self-reported", "Needs Attention", "HR Override"]
    last_updated: datetime

    # HR Override case only (provenance == "HR Override")
    override_set_by_name: str | None = None
    override_reason: str | None = None
    override_set_at: datetime | None = None

    # Populated only alongside an active HR Override -- the non-override
    # signal that would otherwise apply (AR-4: never erased by the override).
    underlying_provenance: Literal["Not Started", "Verified", "Self-reported", "Needs Attention"] | None = None
    underlying_status: AssignmentStatus | None = None
    underlying_status_percentage: int | None = None
