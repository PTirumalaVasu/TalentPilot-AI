"""SQLAlchemy ORM models for the auth module."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, UUID, func
from sqlalchemy.types import Enum

from app.core.db import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("HR_ADMIN", "EMPLOYEE", name="role_enum"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
