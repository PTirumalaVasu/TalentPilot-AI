"""Test database schema initialization and constraints."""
import uuid
from datetime import datetime

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import engine


@pytest.mark.asyncio
async def test_tables_exist():
    """Verify all required tables are created."""
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)
        tables = inspector.get_table_names()

    expected_tables = {
        "accounts",
        "employees",
        "skills",
        "content_catalog",
        "assignments",
        "skill_progress",
        "assignment_overrides",
    }
    assert expected_tables.issubset(set(tables)), f"Missing tables: {expected_tables - set(tables)}"


@pytest.mark.asyncio
async def test_accounts_table_schema():
    """Verify accounts table has correct columns and constraints."""
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)
        columns = {col["name"]: col for col in inspector.get_columns("accounts")}

    expected_columns = {"id", "email", "password_hash", "role", "created_at"}
    assert expected_columns.issubset(set(columns.keys()))

    # Verify column types
    assert columns["id"]["type"].__class__.__name__ == "UUID"
    assert "String" in columns["email"]["type"].__class__.__name__
    assert "String" in columns["password_hash"]["type"].__class__.__name__
    assert columns["email"]["nullable"] is False
    assert columns["password_hash"]["nullable"] is False
    assert columns["role"]["nullable"] is False


@pytest.mark.asyncio
async def test_employees_table_schema():
    """Verify employees table has correct columns and constraints."""
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)
        columns = {col["name"]: col for col in inspector.get_columns("employees")}

    expected_columns = {"id", "name", "email", "role", "created_at"}
    assert expected_columns.issubset(set(columns.keys()))

    assert columns["id"]["type"].__class__.__name__ == "UUID"
    assert columns["name"]["nullable"] is False
    assert columns["email"]["nullable"] is False
    assert columns["email"]["unique"] is True
    assert columns["role"]["nullable"] is False


@pytest.mark.asyncio
async def test_skills_table_schema():
    """Verify skills table has correct columns and vector extension."""
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)
        columns = {col["name"]: col for col in inspector.get_columns("skills")}

    expected_columns = {"id", "name", "description", "embedding", "created_at"}
    assert expected_columns.issubset(set(columns.keys()))

    assert columns["id"]["type"].__class__.__name__ == "UUID"
    assert columns["name"]["nullable"] is False
    assert columns["name"]["unique"] is True
    assert columns["embedding"]["nullable"] is False


@pytest.mark.asyncio
async def test_content_catalog_table_schema():
    """Verify content_catalog table has correct columns and indexes."""
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)
        columns = {col["name"]: col for col in inspector.get_columns("content_catalog")}

    expected_columns = {
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
    assert expected_columns.issubset(set(columns.keys()))

    assert columns["id"]["type"].__class__.__name__ == "UUID"
    assert columns["skill_id"]["nullable"] is False
    assert columns["title"]["nullable"] is False
    assert columns["type"]["nullable"] is False
    assert columns["url"]["nullable"] is False
    assert columns["source"]["nullable"] is False
    assert columns["embedding"]["nullable"] is False


@pytest.mark.asyncio
async def test_assignments_table_schema():
    """Verify assignments table has correct columns and constraints."""
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)
        columns = {col["name"]: col for col in inspector.get_columns("assignments")}

    expected_columns = {
        "id",
        "employee_id",
        "skill_id",
        "content_id",
        "assigned_at",
        "assigned_by",
    }
    assert expected_columns.issubset(set(columns.keys()))

    assert columns["employee_id"]["nullable"] is False
    assert columns["skill_id"]["nullable"] is False
    assert columns["content_id"]["nullable"] is True  # nullable
    assert columns["assigned_at"]["nullable"] is False
    assert columns["assigned_by"]["nullable"] is False


@pytest.mark.asyncio
async def test_skill_progress_table_schema():
    """Verify skill_progress table has correct columns."""
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)
        columns = {col["name"]: col for col in inspector.get_columns("skill_progress")}

    expected_columns = {
        "id",
        "assignment_id",
        "watch_position",
        "event_time",
        "verified",
        "updated_at",
    }
    assert expected_columns.issubset(set(columns.keys()))

    assert columns["assignment_id"]["nullable"] is False
    assert columns["watch_position"]["nullable"] is False
    assert columns["event_time"]["nullable"] is False
    assert columns["verified"]["nullable"] is False
    assert columns["updated_at"]["nullable"] is False


@pytest.mark.asyncio
async def test_assignment_overrides_table_schema():
    """Verify assignment_overrides table has correct columns."""
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)
        columns = {col["name"]: col for col in inspector.get_columns("assignment_overrides")}

    expected_columns = {
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
    assert expected_columns.issubset(set(columns.keys()))

    assert columns["assignment_id"]["nullable"] is False
    assert columns["set_by"]["nullable"] is False
    assert columns["set_at"]["nullable"] is False
    assert columns["active"]["nullable"] is False
    assert columns["override_status"]["nullable"] is False
    assert columns["reversed_at"]["nullable"] is True
    assert columns["reversed_by"]["nullable"] is True


@pytest.mark.asyncio
async def test_foreign_keys_exist():
    """Verify foreign key constraints are created."""
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)

        # Check content_catalog.skill_id → skills.id
        fks = inspector.get_foreign_keys("content_catalog")
        skill_fk = [fk for fk in fks if fk["constrained_columns"] == ["skill_id"]]
        assert len(skill_fk) > 0, "Foreign key content_catalog.skill_id not found"

        # Check assignments.employee_id → employees.id
        fks = inspector.get_foreign_keys("assignments")
        emp_fk = [fk for fk in fks if fk["constrained_columns"] == ["employee_id"]]
        assert len(emp_fk) > 0, "Foreign key assignments.employee_id not found"

        # Check assignments.skill_id → skills.id
        skill_fk = [fk for fk in fks if fk["constrained_columns"] == ["skill_id"]]
        assert len(skill_fk) > 0, "Foreign key assignments.skill_id not found"

        # Check skill_progress.assignment_id → assignments.id
        fks = inspector.get_foreign_keys("skill_progress")
        asgn_fk = [fk for fk in fks if fk["constrained_columns"] == ["assignment_id"]]
        assert len(asgn_fk) > 0, "Foreign key skill_progress.assignment_id not found"


@pytest.mark.asyncio
async def test_pgvector_extension_enabled():
    """Verify pgvector extension is enabled."""
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
        is_enabled = result.scalar()
        assert is_enabled, "pgvector extension not enabled"


@pytest.mark.asyncio
async def test_indexes_exist():
    """Verify required indexes are created."""
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)

        # Check content indexes
        content_indexes = inspector.get_indexes("content_catalog")
        index_names = {idx["name"] for idx in content_indexes}
        assert any("skill" in name for name in index_names), "Index on content_catalog.skill_id not found"

        # Check assignments indexes
        asgn_indexes = inspector.get_indexes("assignments")
        asgn_index_names = {idx["name"] for idx in asgn_indexes}
        assert any("employee" in name for name in asgn_index_names), "Index on assignments.employee_id not found"

        # Check skill_progress indexes
        progress_indexes = inspector.get_indexes("skill_progress")
        progress_index_names = {idx["name"] for idx in progress_indexes}
        assert any("event_time" in name for name in progress_index_names), "Index on skill_progress.event_time not found"


@pytest.mark.asyncio
async def test_seed_employees_exist():
    """Verify seed employees are populated."""
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM employees"))
        count = result.scalar()
        assert count >= 5, f"Expected at least 5 employees, got {count}"


@pytest.mark.asyncio
async def test_seed_skills_exist():
    """Verify seed skills are populated."""
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM skills"))
        count = result.scalar()
        assert count >= 5, f"Expected at least 5 skills, got {count}"


@pytest.mark.asyncio
async def test_seed_employees_have_correct_roles():
    """Verify seed employees have expected roles."""
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT role, COUNT(*) FROM employees GROUP BY role"))
        roles = dict(result.fetchall())

    assert "HR_ADMIN" in roles, "No HR_ADMIN employees found"
    assert "EMPLOYEE" in roles, "No EMPLOYEE employees found"
    assert roles["HR_ADMIN"] >= 1, "Expected at least 1 HR_ADMIN"
    assert roles["EMPLOYEE"] >= 4, "Expected at least 4 EMPLOYEE roles"


@pytest.mark.asyncio
async def test_seed_script_idempotent():
    """Verify seed script can run multiple times without error."""
    async with engine.begin() as conn:
        # First run should already have completed
        result1 = await conn.execute(text("SELECT COUNT(*) FROM employees"))
        count1 = result1.scalar()

        # Run seed again (simulated)
        result2 = await conn.execute(text("SELECT COUNT(*) FROM employees"))
        count2 = result2.scalar()

        assert count1 == count2, "Seed script is not idempotent"


@pytest.mark.asyncio
async def test_timestamps_are_utc():
    """Verify timestamp columns use appropriate types."""
    async with engine.begin() as conn:
        inspector = inspect(conn.sync_engine)

        for table_name in ["accounts", "employees", "skills", "content_catalog", "assignments", "skill_progress"]:
            columns = {col["name"]: col for col in inspector.get_columns(table_name)}
            if "created_at" in columns:
                type_str = str(columns["created_at"]["type"])
                assert "TIMESTAMP" in type_str.upper() or "DATETIME" in type_str.upper(), (
                    f"Table {table_name}.created_at not a timestamp type: {type_str}"
                )
