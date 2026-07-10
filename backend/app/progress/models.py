"""SQLAlchemy ORM models for the progress module.

Note: SkillProgress model is defined in app.assignments.models (shared ownership per AD-1 module pattern).
This module re-exports it for convenience and owns only the repository/service business logic.
"""
from app.assignments.models import SkillProgress

__all__ = ["SkillProgress"]
