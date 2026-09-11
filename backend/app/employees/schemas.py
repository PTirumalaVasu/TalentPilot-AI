"""Pydantic request/response schemas for the employees module.

Story 7.2 (create, FR-24) adds the first real contracts here. Story 7.3
(view/list), 7.4 (edit), and 7.6 (regenerate password) extend this file.
`EmployeeResponse` is deliberately reused across all of those -- it never
carries a password field, since the plaintext password only ever exists in
`EmployeeCreatedResponse`/its future regenerate-password counterpart
(Story 7.2 Dev Notes).
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _reject_blank(value: str) -> str:
    # Mirrors skills/schemas.py::_reject_blank -- Field(min_length=1) alone
    # would accept a whitespace-only value.
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped


class CreateEmployeeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # max_length values match the corresponding employees.<column> String
    # length -- without them, an over-limit value passes validation and
    # fails at insert time with an unhandled DB error instead of a clean 422
    # (same reasoning as skills/schemas.py::CreateSkillRequest.name).
    employee_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=255)

    phone: str | None = Field(default=None, max_length=50)
    experience: str | None = Field(default=None, max_length=255)
    technologies: str | None = Field(default=None, max_length=500)
    position: str | None = Field(default=None, max_length=255)
    project: str | None = Field(default=None, max_length=255)
    manager_name: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=255)

    @field_validator("employee_code", "name")
    @classmethod
    def required_fields_must_not_be_blank(cls, value: str) -> str:
        return _reject_blank(value)


class EmployeeResponse(BaseModel):
    """Default public API response for an Employee -- never carries a
    password field (the plaintext only ever exists in
    EmployeeCreatedResponse, and password_hash lives on Account, a
    different table entirely). Reused as-is by Stories 7.3/7.4/7.6."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_code: str
    name: str
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


class EmployeeCreatedResponse(EmployeeResponse):
    """Story 7.2 AC1: the plaintext password is returned exactly once, only
    in the direct response to the create request -- never persisted in
    plaintext, never retrievable via any other endpoint. Extends
    EmployeeResponse rather than wrapping it, so a single
    `EmployeeCreatedResponse.model_validate(employee, ...)` call still works
    against the ORM object; `generated_password` is set separately since it
    isn't a column on Employee."""

    generated_password: str
