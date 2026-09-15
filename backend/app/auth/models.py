"""SQLAlchemy ORM models for the auth module."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UUID, func
from sqlalchemy.types import Enum

from app.core.db import Base
# Whole-module import -- registers Employee with the shared declarative
# Base so this file's `employees.id` string FK target below always resolves
# (a plain Column FK, not an ORM relationship(), so this is a lighter
# dependency than skills/models.py's or employees/models.py's mirrored
# relationship-registration imports, but the module still needs to be
# loaded for the FK's target table to exist when Alembic/SQLAlchemy
# resolves it).
import app.employees.models  # noqa: F401


class Account(Base):
    """Local auth credential store.

    Story 7.1 (AR-24) introduced this table as the real credential store,
    replacing the plaintext `_MOCK_ACCOUNTS` dict that previously lived in
    `auth/repository.py`. `authenticate()` (`auth/service.py`) now reads
    this table for every login, HR_ADMIN and EMPLOYEE alike -- the epic-8
    retro's top-priority gap (sprint-status.yaml), closed by wiring
    `authenticate()` to `get_account_by_email_ci` + bcrypt verification
    instead of the hardcoded dict.

    `id` MUST always equal the corresponding `employees.id` -- this is the
    identity link the rest of the app relies on (`auth/repository.py`'s own
    comment: "user_id values are the same UUIDs as the real seeded Employee
    rows... CurrentUser.user_id [must be] a real Employee UUID"). No
    `Account` row should ever be created with an `id` that isn't an
    existing `Employee.id`.
    """

    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("HR_ADMIN", "EMPLOYEE", name="role_enum"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    # Story 7.5 (FR-27/AR-25): mirrors employees.archived_at, kept in sync by
    # employees/service.py's delete/archive service in the same transaction.
    # Checked by get_current_user to reject an archived identity's still-valid
    # session -- deliberately duplicated here rather than read via a cross-
    # module Employee import, which would create a circular import with
    # employees/service.py (which already imports this module).
    archived_at = Column(DateTime(timezone=True), nullable=True)
