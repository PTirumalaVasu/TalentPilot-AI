"""Pydantic request/response schemas for the skills module.

Story 6.2 (create, FR-20) adds the first real contracts here. Story 6.3
(edit/delete, FR-21/22) adds UpdateSkillRequest. Deliberately independent
of assignments/schemas.py::SkillResponse (the Step 2 combobox's own,
narrower schema, Story 3.4) -- per-module response schemas are this
codebase's established convention (content/schemas.py::ContentResponse is
not shared with any other module either), and this story's SkillResponse
needs `ever_assigned`, which the combobox schema doesn't carry.
"""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _reject_blank(value: str) -> str:
    # Field(min_length=1) alone would accept a whitespace-only name -- the
    # ACs' "non-empty" requirement means non-blank, not just non-zero-length.
    stripped = value.strip()
    if not stripped:
        raise ValueError("name must not be blank")
    return stripped


class CreateSkillRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # max_length=255 matches skills.name's String(255) column -- without it,
    # an over-limit name passes validation and fails at insert time with an
    # unhandled DB error instead of a clean 422 (code review, 2026-09-09).
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        return _reject_blank(value)


class UpdateSkillRequest(BaseModel):
    """PATCH body (Story 6.3 AC1) -- both fields optional, partial-update
    semantics. Service reads `model_dump(exclude_unset=True)` so an omitted
    field leaves the current value untouched, distinct from an explicitly
    provided `description: null` (which clears it)."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_null_or_blank(cls, value: str | None) -> str:
        # `name` is a required Skill-identity field (NOT NULL in the DB) --
        # unlike `description`, an explicit `{"name": null}` is never valid,
        # only *omitting* the field is (pydantic skips this validator
        # entirely for an omitted/defaulted field, so this only runs when
        # the caller actually provided a value).
        if value is None:
            raise ValueError("name must not be null")
        return _reject_blank(value)


class SkillResponse(BaseModel):
    """Default public API response for a Skill (excludes the raw embedding
    vector -- same convention as content/schemas.py::ContentResponse)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    ever_assigned: bool
