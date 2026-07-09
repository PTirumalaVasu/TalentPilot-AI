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
