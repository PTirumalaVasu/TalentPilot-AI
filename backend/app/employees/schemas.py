"""Pydantic request/response schemas for the employees module.

Story 7.2 (create, FR-24) adds the first real contracts here. Story 7.3
(view/list), 7.4 (edit), and 7.6 (regenerate password) extend this file.
`EmployeeResponse` is deliberately reused across all of those -- it never
carries a password field, since the plaintext password only ever exists in
`EmployeeCreatedResponse`/its future regenerate-password counterpart
(Story 7.2 Dev Notes).
"""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


def _reject_blank(value: str) -> str:
    # Mirrors skills/schemas.py::_reject_blank -- Field(min_length=1) alone
    # would accept a whitespace-only value.
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped


# employees.name (the derived f"{first_name} {last_name}" column -- Story
# 10.2 Dev Notes) is String(255). first_name/last_name are each independently
# capped at max_length=255, so without this check two near-max-length values
# combine into a >255-char `name` that fails at INSERT with an unhandled
# DataError instead of a clean 422 -- the exact failure mode max_length
# values exist to prevent (see the comment on CreateEmployeeRequest below).
def _reject_combined_name_too_long(first_name: str, last_name: str) -> None:
    if len(first_name) + 1 + len(last_name) > 255:
        raise ValueError("first_name and last_name combined must not exceed 255 characters")


class CreateEmployeeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # max_length values match the corresponding employees.<column> String
    # length -- without them, an over-limit value passes validation and
    # fails at insert time with an unhandled DB error instead of a clean 422
    # (same reasoning as skills/schemas.py::CreateSkillRequest.name).
    employee_code: str = Field(min_length=1, max_length=50)
    # Story 10.2 (FR-34): the combined `name` field is removed from the
    # request body -- First/Last Name are two required fields instead, same
    # requiredness tier as the old combined field.
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=255)

    phone: str | None = Field(default=None, max_length=50)
    experience: str | None = Field(default=None, max_length=255)
    technologies: str | None = Field(default=None, max_length=500)
    position: str | None = Field(default=None, max_length=255)
    project: str | None = Field(default=None, max_length=255)
    manager_name: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=255)

    @field_validator("employee_code", "first_name", "last_name")
    @classmethod
    def required_fields_must_not_be_blank(cls, value: str) -> str:
        return _reject_blank(value)

    @model_validator(mode="after")
    def combined_name_must_not_be_too_long(self) -> "CreateEmployeeRequest":
        _reject_combined_name_too_long(self.first_name, self.last_name)
        return self


class UpdateEmployeeRequest(BaseModel):
    """Story 7.4 (edit, FR-26): the same editable field set as
    CreateEmployeeRequest minus employee_code, which is immutable once set
    (UX-DR39) -- deliberately never declared here, so a client that sends it
    fails fast with a 422 via extra="forbid" rather than silently dropping
    it. The Edit panel always submits the complete field set (a full
    replace), not a partial/JSON-merge-patch body."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=255)

    phone: str | None = Field(default=None, max_length=50)
    experience: str | None = Field(default=None, max_length=255)
    technologies: str | None = Field(default=None, max_length=500)
    position: str | None = Field(default=None, max_length=255)
    project: str | None = Field(default=None, max_length=255)
    manager_name: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=255)

    @field_validator("first_name", "last_name")
    @classmethod
    def required_fields_must_not_be_blank(cls, value: str) -> str:
        return _reject_blank(value)

    @model_validator(mode="after")
    def combined_name_must_not_be_too_long(self) -> "UpdateEmployeeRequest":
        _reject_combined_name_too_long(self.first_name, self.last_name)
        return self


class EmployeeResponse(BaseModel):
    """Default public API response for an Employee -- never carries a
    password field (the plaintext only ever exists in
    EmployeeCreatedResponse, and password_hash lives on Account, a
    different table entirely). Reused as-is by Stories 7.3/7.4/7.6."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_code: str
    name: str
    first_name: str
    last_name: str
    email: str
    role: str
    phone: str | None
    experience: str | None
    technologies: str | None
    position: str | None
    project: str | None
    manager_name: str | None
    location: str | None
    department: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    # Story 7.5 (FR-27): whether this employee has ever had an Assignment
    # created for them (active or soft-deleted) -- drives the Delete/Archive
    # confirmation dialog's copy (UX-DR38). Not a real ORM column, so it is
    # never populated by a bare `EmployeeResponse.model_validate(employee)`
    # call -- the service layer must set it explicitly on the returned
    # object afterward (see employees/service.py's `_build_employee_response`
    # helper). Defaults to False so a fresh EmployeeCreatedResponse (a
    # brand-new employee, always zero Assignments by construction) needs no
    # extra query.
    has_assignment_history: bool = False

    # Story 10.2 (FR-34/FR-35): whole days since `created_at`, computed on
    # read in employees/service.py -- not a real ORM column, so (like
    # has_assignment_history above) it is never populated by a bare
    # `EmployeeResponse.model_validate(employee)` call.
    days_in_talent_pool: int = 0


class DeleteEmployeeResponse(BaseModel):
    """Story 7.5 (FR-27): response for DELETE /api/admin/employees/{id}.
    Deliberately carries a body (unlike skills/'s `deleteSkill`'s bodyless
    204) because the frontend's success-toast copy depends on which action
    actually occurred -- which the confirmation dialog's own prediction may
    not match in a race (see the story's Scope Note 4)."""

    action: Literal["deleted", "archived"]


class EmployeeCreatedResponse(EmployeeResponse):
    """Story 7.2 AC1: the plaintext password is returned exactly once, only
    in the direct response to the create request -- never persisted in
    plaintext, never retrievable via any other endpoint. Extends
    EmployeeResponse rather than wrapping it, so a single
    `EmployeeCreatedResponse.model_validate(employee, ...)` call still works
    against the ORM object; `generated_password` is set separately since it
    isn't a column on Employee."""

    generated_password: str
