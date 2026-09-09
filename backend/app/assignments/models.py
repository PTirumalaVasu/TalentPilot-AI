"""SQLAlchemy ORM models for the assignments module and related tables."""
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    UUID,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    Boolean,
    Integer,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import relationship

from app.core.db import Base
# Whole-module import, not `from app.skills.models import Skill` -- registers
# Skill with the shared declarative Base (so Assignment/ContentCatalog's
# relationship(back_populates=...) can resolve the "Skill" string below)
# without re-exposing `Skill` as an importable name on this module. Code
# review (2026-09-09) found the `from ... import Skill` form silently kept
# the pre-Story-6.1 `from app.assignments.models import Skill` path working
# for any caller, undermining the whole point of relocating it -- verified
# zero remaining call sites depended on that path before switching. Skill
# itself now lives in app.skills.models (Story 6.1); assignments/ never
# queries or writes the skills table directly (AD-1, AD-11).
import app.skills.models  # noqa: F401


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(Enum("HR_ADMIN", "EMPLOYEE", name="role_enum"), nullable=False)
    group = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    assignments = relationship("Assignment", back_populates="employee", foreign_keys="Assignment.employee_id")
    assignments_created = relationship("Assignment", back_populates="assigned_by_user", foreign_keys="Assignment.assigned_by")
    assignments_deleted = relationship("Assignment", back_populates="deleted_by_user", foreign_keys="Assignment.deleted_by")
    overrides_created = relationship("AssignmentOverride", back_populates="set_by_user", foreign_keys="AssignmentOverride.set_by")
    overrides_reversed = relationship("AssignmentOverride", back_populates="reversed_by_user", foreign_keys="AssignmentOverride.reversed_by")


class ContentCatalog(Base):
    __tablename__ = "content_catalog"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum("VIDEO", "DOCUMENT", "WEBSITE", name="content_type_enum"), nullable=False)
    url = Column(String(500), nullable=False)
    embedding = Column(Vector(384), nullable=False)
    source = Column(Enum("YOUTUBE", "MANUAL", name="content_source_enum"), nullable=False)
    ingested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    content_metadata = Column(JSON, name="metadata")

    # Relationships
    skill = relationship("Skill", back_populates="content_items")
    assignments = relationship("Assignment", back_populates="content")

    __table_args__ = (
        Index("idx_content_skill", "skill_id"),
        Index("idx_content_embedding", "embedding", postgresql_using="ivfflat"),
    )


class AdminApiKey(Base):
    """Per-Admin content-source API key (AD-10, Story 6.5).

    Personal to one HR Admin -- e.g. their own YouTube Data API key.
    Encrypted at rest via core/secrets.py before being stored in
    encrypted_key; never decrypted/returned outside content/'s own
    repository layer (AD-10). Owned by content/ (AD-1); the model lives
    here alongside ContentCatalog per this codebase's existing
    everything-in-assignments/models.py convention, not content/models.py
    (Skill itself moved out to app.skills.models in Story 6.1).
    """

    __tablename__ = "admin_api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    source = Column(String(50), nullable=False)  # "YOUTUBE" -- per-admin sources only, AD-10
    encrypted_key = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("admin_id", "source", name="uq_admin_api_keys_admin_id_source"),
    )


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False, index=True)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content_catalog.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    active = Column(Boolean, default=True, nullable=False, server_default=true())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="assignments", foreign_keys=[employee_id])
    assigned_by_user = relationship("Employee", back_populates="assignments_created", foreign_keys=[assigned_by])
    deleted_by_user = relationship("Employee", back_populates="assignments_deleted", foreign_keys=[deleted_by])
    skill = relationship("Skill", back_populates="assignments")
    content = relationship("ContentCatalog", back_populates="assignments")
    progress = relationship("SkillProgress", back_populates="assignment", uselist=False)
    overrides = relationship("AssignmentOverride", back_populates="assignment")

    __table_args__ = (
        Index("idx_assignments_employee", "employee_id"),
        Index("idx_assignments_skill", "skill_id"),
        Index("idx_assignments_active", "active"),
    )


class SkillProgress(Base):
    __tablename__ = "skill_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id"), unique=True, nullable=False)
    watch_position = Column(Integer, nullable=False)  # seconds
    event_time = Column(DateTime(timezone=True), nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    assignment = relationship("Assignment", back_populates="progress")

    __table_args__ = (
        Index("idx_progress_assignment", "assignment_id", unique=True),
        Index("idx_progress_event_time", "event_time"),
    )


class AssignmentOverride(Base):
    __tablename__ = "assignment_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id"), nullable=False)
    set_by = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    set_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reason = Column(Text)
    active = Column(Boolean, default=True, nullable=False)
    override_status = Column(Enum("NOT_STARTED", "IN_PROGRESS", "COMPLETED", name="status_enum"), nullable=False)
    reversed_at = Column(DateTime(timezone=True))
    reversed_by = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)

    # Relationships
    assignment = relationship("Assignment", back_populates="overrides")
    set_by_user = relationship("Employee", back_populates="overrides_created", foreign_keys=[set_by])
    reversed_by_user = relationship("Employee", back_populates="overrides_reversed", foreign_keys=[reversed_by])

    __table_args__ = (
        Index("idx_overrides_assignment", "assignment_id"),
        Index("idx_overrides_active", "active"),
    )
