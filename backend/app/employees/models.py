"""SQLAlchemy ORM model for the employees module (Story 7.1, AR-24).

`Employee` is the sole table `employees/` owns. It is relocated here in full
-- both physically and logically -- out of `app/assignments/models.py`,
mirroring `skills/`'s identical relocation of `Skill` in Story 6.1 (AD-11).
`app/assignments/models.py` imports this class back in only for the
`Assignment`/`AssignmentOverride` FK relationships; it never queries or
writes the `employees` table directly (AD-1).
"""
import uuid

from sqlalchemy import UUID, Column, DateTime, Enum, String, func
from sqlalchemy.orm import relationship

from app.core.db import Base
# Whole-module import (not `from ... import Assignment, AssignmentOverride`)
# -- registers those classes with the shared declarative Base so this
# file's own "Assignment"/"AssignmentOverride" relationship strings below
# always resolve, regardless of import order. Mirrors
# assignments/models.py's identical `import app.employees.models` in
# reverse, and skills/models.py's established precedent for this exact
# circular-registration idiom (Story 6.1 code review, 2026-09-09).
import app.assignments.models  # noqa: F401


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(Enum("HR_ADMIN", "EMPLOYEE", name="role_enum"), nullable=False)
    group = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # --- Story 7.1: Employee Roster Management profile fields (FR-24) ---
    # `employee_code` is HR-assigned and distinct from `id` (the internal
    # UUID) -- required, unique. The 5 pre-existing seeded rows are
    # backfilled with EMP-0001..EMP-0005 by migration 011 (ordered by
    # core/seed_ids.py's declared UUID order, not created_at -- see that
    # migration's own comment for why).
    employee_code = Column(String(50), unique=True, nullable=False)  # DB-level: migration 011's uq_employees_employee_code
    phone = Column(String(50), nullable=True)
    experience = Column(String(255), nullable=True)
    technologies = Column(String(500), nullable=True)
    position = Column(String(255), nullable=True)
    project = Column(String(255), nullable=True)
    manager_name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    # `department` is a new, distinct column -- NOT a reuse of the
    # pre-existing `group` column above. Deliberate decision (Story 7.1 Dev
    # Notes): `group`'s existing semantics/usage were never established as
    # "department," and silently repurposing it risks colliding with
    # whatever it already means to other code paths. `group` stays as-is,
    # untouched by Employee Roster Management.
    department = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    # FR-27: null = active, non-null = archived. Soft-delete flag -- an
    # Employee with any Assignment history is archived, never hard-deleted
    # (mirrors `assignments.active`/`assignment_overrides.active`'s
    # existing soft-delete convention in this codebase).
    archived_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships are string-resolved against the shared declarative
    # registry (`app.core.db.Base`) -- Assignment and AssignmentOverride
    # stay physically defined in app.assignments.models (registered above).
    assignments = relationship("Assignment", back_populates="employee", foreign_keys="Assignment.employee_id")
    assignments_created = relationship("Assignment", back_populates="assigned_by_user", foreign_keys="Assignment.assigned_by")
    assignments_deleted = relationship("Assignment", back_populates="deleted_by_user", foreign_keys="Assignment.deleted_by")
    overrides_created = relationship("AssignmentOverride", back_populates="set_by_user", foreign_keys="AssignmentOverride.set_by")
    overrides_reversed = relationship("AssignmentOverride", back_populates="reversed_by_user", foreign_keys="AssignmentOverride.reversed_by")
