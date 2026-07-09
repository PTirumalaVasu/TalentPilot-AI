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
    func,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(Enum("HR_ADMIN", "EMPLOYEE", name="role_enum"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    assignments = relationship("Assignment", back_populates="employee", foreign_keys="Assignment.employee_id")
    assignments_created = relationship("Assignment", back_populates="assigned_by_user", foreign_keys="Assignment.assigned_by")
    overrides_created = relationship("AssignmentOverride", back_populates="set_by_user", foreign_keys="AssignmentOverride.set_by")
    overrides_reversed = relationship("AssignmentOverride", back_populates="reversed_by_user", foreign_keys="AssignmentOverride.reversed_by")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    embedding = Column(Vector(384), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    content_items = relationship("ContentCatalog", back_populates="skill")
    assignments = relationship("Assignment", back_populates="skill")


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


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False, index=True)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content_catalog.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="assignments", foreign_keys=[employee_id])
    assigned_by_user = relationship("Employee", back_populates="assignments_created", foreign_keys=[assigned_by])
    skill = relationship("Skill", back_populates="assignments")
    content = relationship("ContentCatalog", back_populates="assignments")
    progress = relationship("SkillProgress", back_populates="assignment", uselist=False)
    overrides = relationship("AssignmentOverride", back_populates="assignment")

    __table_args__ = (
        Index("idx_assignments_employee", "employee_id"),
        Index("idx_assignments_skill", "skill_id"),
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
