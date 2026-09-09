"""Pydantic request/response schemas for the skills module.

Story 6.2 (create, FR-20) adds the first real contracts here. Deliberately
independent of assignments/schemas.py::SkillResponse (the Step 2 combobox's
own, narrower schema, Story 3.4) -- per-module response schemas are this
codebase's established convention (content/schemas.py::ContentResponse is
not shared with any other module either), and this story's SkillResponse
needs `ever_assigned`, which the combobox schema doesn't carry.
"""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
        # min_length=1 alone would accept a whitespace-only name -- the AC's
        # "non-empty" requirement means non-blank, not just non-zero-length.
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank")
        return stripped


class SkillResponse(BaseModel):
    """Default public API response for a Skill (excludes the raw embedding
    vector -- same convention as content/schemas.py::ContentResponse)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    ever_assigned: bool
