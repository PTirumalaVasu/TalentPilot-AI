"""Pydantic request/response schemas for the auth module."""

from enum import Enum

from pydantic import BaseModel


class Role(str, Enum):
    HR_ADMIN = "HR_ADMIN"
    EMPLOYEE = "EMPLOYEE"


class CurrentUser(BaseModel):
    role: Role
    user_id: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    role: Role
    user_id: str


class MeResponse(BaseModel):
    """Response for GET /api/auth/me -- the session's own display identity.
    name/email live on the Employee row (assignments module, AD-1), so the
    route resolves them via app.assignments.service.get_employee_by_id_service
    rather than this module querying the employees table directly."""

    user_id: str
    role: Role
    name: str
    email: str
