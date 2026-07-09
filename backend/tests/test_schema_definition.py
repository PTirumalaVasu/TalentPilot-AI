"""Test that ORM models define the correct schema structure."""
import uuid

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import class_mapper

# Import models to register them
from app.auth.models import Account
from app.assignments.models import (
    Assignment,
    AssignmentOverride,
    ContentCatalog,
    Employee,
    Skill,
    SkillProgress,
)
from app.core.db import Base


def test_all_tables_defined():
    """Verify all 7 required tables are defined in the ORM."""
    expected_tables = {
        "accounts",
        "employees",
        "skills",
        "content_catalog",
        "assignments",
        "skill_progress",
        "assignment_overrides",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables == actual_tables, f"Table mismatch. Expected: {expected_tables}, Got: {actual_tables}"


def test_accounts_table_structure():
    """Verify Account model defines correct columns."""
    mapper = class_mapper(Account)
    columns = {col.name for col in mapper.columns}

    expected = {"id", "email", "password_hash", "role", "created_at"}
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_employees_table_structure():
    """Verify Employee model defines correct columns."""
    mapper = class_mapper(Employee)
    columns = {col.name for col in mapper.columns}

    expected = {"id", "name", "email", "role", "created_at"}
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_skills_table_structure():
    """Verify Skill model defines correct columns."""
    mapper = class_mapper(Skill)
    columns = {col.name for col in mapper.columns}

    expected = {"id", "name", "description", "embedding", "created_at"}
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_content_catalog_table_structure():
    """Verify ContentCatalog model defines correct columns."""
    mapper = class_mapper(ContentCatalog)
    columns = {col.name for col in mapper.columns}

    expected = {
        "id",
        "skill_id",
        "title",
        "description",
        "type",
        "url",
        "embedding",
        "source",
        "ingested_at",
        "metadata",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_assignments_table_structure():
    """Verify Assignment model defines correct columns."""
    mapper = class_mapper(Assignment)
    columns = {col.name for col in mapper.columns}

    expected = {"id", "employee_id", "skill_id", "content_id", "assigned_at", "assigned_by"}
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_skill_progress_table_structure():
    """Verify SkillProgress model defines correct columns."""
    mapper = class_mapper(SkillProgress)
    columns = {col.name for col in mapper.columns}

    expected = {"id", "assignment_id", "watch_position", "event_time", "verified", "updated_at"}
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_assignment_overrides_table_structure():
    """Verify AssignmentOverride model defines correct columns."""
    mapper = class_mapper(AssignmentOverride)
    columns = {col.name for col in mapper.columns}

    expected = {
        "id",
        "assignment_id",
        "set_by",
        "set_at",
        "reason",
        "active",
        "override_status",
        "reversed_at",
        "reversed_by",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_foreign_keys_defined():
    """Verify foreign key relationships are defined via SQLAlchemy relationships."""
    # Check relationships exist (these are what matter for data integrity)
    assert hasattr(Assignment, "employee")
    assert hasattr(Assignment, "skill")
    assert hasattr(Assignment, "assigned_by_user")
    assert hasattr(SkillProgress, "assignment")
    assert hasattr(ContentCatalog, "skill")

    # Check that the relationship properties can be accessed
    assignment_mapper = class_mapper(Assignment)
    relationships = {rel.key for rel in assignment_mapper.relationships}
    assert "employee" in relationships
    assert "skill" in relationships


def test_unique_constraints_defined():
    """Verify unique constraints are defined."""
    # Email fields should be unique
    account_mapper = class_mapper(Account)
    account_email_col = account_mapper.columns["email"]
    assert account_email_col.unique is True, "Account.email should be unique"

    employee_mapper = class_mapper(Employee)
    employee_email_col = employee_mapper.columns["email"]
    assert employee_email_col.unique is True, "Employee.email should be unique"

    skill_mapper = class_mapper(Skill)
    skill_name_col = skill_mapper.columns["name"]
    assert skill_name_col.unique is True, "Skill.name should be unique"


def test_nullable_constraints():
    """Verify nullable constraints match the spec."""
    # content_id in assignments should be nullable
    assignment_mapper = class_mapper(Assignment)
    content_id_col = assignment_mapper.columns["content_id"]
    assert content_id_col.nullable is True, "Assignment.content_id should be nullable"

    # reversed_at in overrides should be nullable
    override_mapper = class_mapper(AssignmentOverride)
    reversed_at_col = override_mapper.columns["reversed_at"]
    assert reversed_at_col.nullable is True, "AssignmentOverride.reversed_at should be nullable"


def test_enum_types_defined():
    """Verify enum columns are properly defined."""
    account_mapper = class_mapper(Account)
    role_col = account_mapper.columns["role"]
    assert role_col.type.__class__.__name__ == "Enum", "Account.role should be Enum type"

    content_mapper = class_mapper(ContentCatalog)
    type_col = content_mapper.columns["type"]
    assert type_col.type.__class__.__name__ == "Enum", "ContentCatalog.type should be Enum type"


def test_vector_types_defined():
    """Verify pgvector embedding columns are properly defined."""
    skill_mapper = class_mapper(Skill)
    embedding_col = skill_mapper.columns["embedding"]
    # pgvector uses VECTOR type (uppercase) or Vector
    assert "VECTOR" in embedding_col.type.__class__.__name__.upper(), "Skill.embedding should be Vector type"

    content_mapper = class_mapper(ContentCatalog)
    embedding_col = content_mapper.columns["embedding"]
    assert "VECTOR" in embedding_col.type.__class__.__name__.upper(), "ContentCatalog.embedding should be Vector type"


def test_table_args_indexes():
    """Verify indexes are defined in __table_args__."""
    # Assignment should have indexes on employee_id and skill_id
    assert hasattr(Assignment, "__table_args__")
    table_args = Assignment.__table_args__
    assert isinstance(table_args, tuple), "Assignment.__table_args__ should be a tuple"
    # At least one index should be defined
    indexes = [arg for arg in table_args if hasattr(arg, "name") and "idx_" in str(arg)]
    assert len(indexes) > 0, "Assignment should have at least one index defined"
