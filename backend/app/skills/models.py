"""SQLAlchemy ORM model for the skills module (Story 6.1, AD-11).

`Skill` is the sole table `skills/` owns. Unlike `ContentCatalog`'s
established co-location inside `app/assignments/models.py` (an existing,
still-valid AD-1 convenience for tables with no dedicated module), `Skill`
is relocated here in full -- both physically and logically -- per AD-11
point 1. `app/assignments/models.py` imports this class back in only for
the `Assignment.skill_id` FK relationship; it never queries or writes the
`skills` table directly (AD-1).
"""
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import UUID, Boolean, Column, DateTime, String, Text, false, func
from sqlalchemy.orm import relationship

from app.core.db import Base
# Whole-module import (not `from ... import ContentCatalog, Assignment`) --
# registers those classes with the shared declarative Base so this file's
# own "ContentCatalog"/"Assignment" relationship strings below always
# resolve, regardless of import order. Without this, a future entry point
# that imports app.skills.* without ever touching app.assignments.models
# (a standalone script, a narrower test) would hit an unresolved-
# relationship error at first mapper configuration -- found in code review
# (2026-09-09) by both the Edge Case Hunter and Blind Hunter passes, since
# every current caller only avoided it by transitively importing both
# modules together. Safe circular-registration idiom: a whole-module import
# never requires the other module's classes to already be defined, only
# that the module itself is (or is currently being) loaded -- mirrors
# assignments/models.py's identical `import app.skills.models` in reverse.
import app.assignments.models  # noqa: F401


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    embedding = Column(Vector(384), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    # AD-11: permanent, one-way lock enforced by skills/'s own edit/delete
    # service methods (FR-21/FR-22, Story 6.3) -- set true by assignments/
    # via skills.service.mark_ever_assigned() on first Assignment creation
    # (Story 6.4), never reset back to false. Column added by migration 004,
    # which also backfills true for every Skill already referenced by an
    # existing Assignment.
    ever_assigned = Column(Boolean, default=False, nullable=False, server_default=false())

    # Relationships are string-resolved against the shared declarative
    # registry (`app.core.db.Base`) -- ContentCatalog and Assignment stay
    # physically defined in app.assignments.models (registered above).
    content_items = relationship("ContentCatalog", back_populates="skill")
    assignments = relationship("Assignment", back_populates="skill")
