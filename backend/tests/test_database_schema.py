"""Test database schema initialization and constraints."""
import pytest
from sqlalchemy import inspect, text

from app.core.db import async_session_factory, engine
from app.core.seeds import run_seeds

# app.core.db.engine is a module-level singleton whose pooled asyncpg
# connections bind to whichever event loop first touches them. Without a
# shared loop for this whole module, pytest-asyncio's default per-test
# function-scoped loop hands connection reuse across incompatible loops,
# corrupting the asyncpg connection state ("another operation in progress").
pytestmark = pytest.mark.asyncio(loop_scope="module")


def _get_columns(sync_conn, table_name):
    return {col["name"]: col for col in inspect(sync_conn).get_columns(table_name)}


def _get_foreign_keys(sync_conn, table_name):
    return inspect(sync_conn).get_foreign_keys(table_name)


def _get_indexes(sync_conn, table_name):
    return inspect(sync_conn).get_indexes(table_name)


def _get_unique_columns(sync_conn, table_name):
    """Column-level UniqueConstraint doesn't set get_columns()'s 'unique' key on
    this dialect/version — reflect via get_unique_constraints() instead.

    Only single-column constraints count: a multi-column UNIQUE(a, b) does not
    make a or b independently unique, so it must not be flattened in."""
    columns = set()
    for uc in inspect(sync_conn).get_unique_constraints(table_name):
        if len(uc["column_names"]) == 1:
            columns.add(uc["column_names"][0])
    return columns


async def test_tables_exist():
    """Verify all required tables are created."""
    async with engine.begin() as conn:
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())

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


async def test_accounts_table_schema():
    """Verify accounts table has correct columns and constraints."""
    async with engine.begin() as conn:
        columns = await conn.run_sync(_get_columns, "accounts")
        unique_columns = await conn.run_sync(_get_unique_columns, "accounts")

    expected_columns = {"id", "email", "password_hash", "role", "created_at"}
    assert expected_columns.issubset(set(columns.keys()))

    # Verify column types
    assert columns["id"]["type"].__class__.__name__ == "UUID"
    assert "VARCHAR" in columns["email"]["type"].__class__.__name__
    assert "VARCHAR" in columns["password_hash"]["type"].__class__.__name__
    assert columns["email"]["nullable"] is False
    assert "email" in unique_columns
    assert columns["password_hash"]["nullable"] is False
    assert columns["role"]["nullable"] is False


async def test_employees_table_schema():
    """Verify employees table has correct columns and constraints."""
    async with engine.begin() as conn:
        columns = await conn.run_sync(_get_columns, "employees")
        unique_columns = await conn.run_sync(_get_unique_columns, "employees")

    expected_columns = {"id", "name", "email", "role", "created_at"}
    assert expected_columns.issubset(set(columns.keys()))

    assert columns["id"]["type"].__class__.__name__ == "UUID"
    assert columns["name"]["nullable"] is False
    assert columns["email"]["nullable"] is False
    assert "email" in unique_columns
    assert columns["role"]["nullable"] is False


async def test_skills_table_schema():
    """Verify skills table has correct columns and vector extension."""
    async with engine.begin() as conn:
        columns = await conn.run_sync(_get_columns, "skills")
        unique_columns = await conn.run_sync(_get_unique_columns, "skills")

    expected_columns = {"id", "name", "description", "embedding", "created_at"}
    assert expected_columns.issubset(set(columns.keys()))

    assert columns["id"]["type"].__class__.__name__ == "UUID"
    assert columns["name"]["nullable"] is False
    assert "name" in unique_columns
    assert columns["embedding"]["nullable"] is False


async def test_content_catalog_table_schema():
    """Verify content_catalog table has correct columns and indexes."""
    async with engine.begin() as conn:
        columns = await conn.run_sync(_get_columns, "content_catalog")

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


async def test_assignments_table_schema():
    """Verify assignments table has correct columns and constraints."""
    async with engine.begin() as conn:
        columns = await conn.run_sync(_get_columns, "assignments")

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


async def test_skill_progress_table_schema():
    """Verify skill_progress table has correct columns."""
    async with engine.begin() as conn:
        columns = await conn.run_sync(_get_columns, "skill_progress")

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


async def test_assignment_overrides_table_schema():
    """Verify assignment_overrides table has correct columns."""
    async with engine.begin() as conn:
        columns = await conn.run_sync(_get_columns, "assignment_overrides")

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


async def test_foreign_keys_exist():
    """Verify foreign key constraints are created."""
    async with engine.begin() as conn:
        content_fks = await conn.run_sync(_get_foreign_keys, "content_catalog")
        assignments_fks = await conn.run_sync(_get_foreign_keys, "assignments")
        progress_fks = await conn.run_sync(_get_foreign_keys, "skill_progress")

    # Check content_catalog.skill_id → skills.id
    skill_fk = [fk for fk in content_fks if fk["constrained_columns"] == ["skill_id"]]
    assert len(skill_fk) > 0, "Foreign key content_catalog.skill_id not found"

    # Check assignments.employee_id → employees.id
    emp_fk = [fk for fk in assignments_fks if fk["constrained_columns"] == ["employee_id"]]
    assert len(emp_fk) > 0, "Foreign key assignments.employee_id not found"

    # Check assignments.skill_id → skills.id
    skill_fk = [fk for fk in assignments_fks if fk["constrained_columns"] == ["skill_id"]]
    assert len(skill_fk) > 0, "Foreign key assignments.skill_id not found"

    # Check skill_progress.assignment_id → assignments.id
    asgn_fk = [fk for fk in progress_fks if fk["constrained_columns"] == ["assignment_id"]]
    assert len(asgn_fk) > 0, "Foreign key skill_progress.assignment_id not found"


async def test_pgvector_extension_enabled():
    """Verify pgvector extension is enabled."""
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
        is_enabled = result.scalar()
        assert is_enabled, "pgvector extension not enabled"


async def test_indexes_exist():
    """Verify required indexes are created."""
    async with engine.begin() as conn:
        content_indexes = await conn.run_sync(_get_indexes, "content_catalog")
        asgn_indexes = await conn.run_sync(_get_indexes, "assignments")
        progress_indexes = await conn.run_sync(_get_indexes, "skill_progress")

    # Check content indexes
    index_names = {idx["name"] for idx in content_indexes}
    assert any("skill" in name for name in index_names), "Index on content_catalog.skill_id not found"

    # Check assignments indexes
    asgn_index_names = {idx["name"] for idx in asgn_indexes}
    assert any("employee" in name for name in asgn_index_names), "Index on assignments.employee_id not found"

    # Check skill_progress indexes
    progress_index_names = {idx["name"] for idx in progress_indexes}
    assert any("event_time" in name for name in progress_index_names), "Index on skill_progress.event_time not found"


async def test_seed_employees_exist():
    """Verify seed employees are populated."""
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM employees"))
        count = result.scalar()
        assert count >= 5, f"Expected at least 5 employees, got {count}"


async def test_seed_skills_exist():
    """Verify seed skills are populated."""
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM skills"))
        count = result.scalar()
        assert count >= 5, f"Expected at least 5 skills, got {count}"


async def test_seed_employees_have_correct_roles():
    """Verify seed employees have expected roles."""
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT role, COUNT(*) FROM employees GROUP BY role"))
        roles = dict(result.fetchall())

    assert "HR_ADMIN" in roles, "No HR_ADMIN employees found"
    assert "EMPLOYEE" in roles, "No EMPLOYEE employees found"
    assert roles["HR_ADMIN"] >= 1, "Expected at least 1 HR_ADMIN"
    assert roles["EMPLOYEE"] >= 4, "Expected at least 4 EMPLOYEE roles"


async def test_seed_script_idempotent():
    """Verify re-running the seed script produces no duplicate-key errors and no row-count growth (AC10)."""
    async with engine.begin() as conn:
        result1 = await conn.execute(text("SELECT COUNT(*) FROM employees"))
        count1 = result1.scalar()

    async with async_session_factory() as session:
        await run_seeds(session)  # actually re-run, not just re-query the same data

    async with engine.begin() as conn:
        result2 = await conn.execute(text("SELECT COUNT(*) FROM employees"))
        count2 = result2.scalar()

    assert count1 == count2, "Seed script is not idempotent"


async def test_timestamps_are_utc():
    """Verify timestamp columns use appropriate types."""
    async with engine.begin() as conn:
        all_columns = {
            table_name: await conn.run_sync(_get_columns, table_name)
            for table_name in ["accounts", "employees", "skills", "content_catalog", "assignments", "skill_progress"]
        }

    for table_name, columns in all_columns.items():
        if "created_at" in columns:
            type_str = str(columns["created_at"]["type"])
            assert "TIMESTAMP" in type_str.upper() or "DATETIME" in type_str.upper(), (
                f"Table {table_name}.created_at not a timestamp type: {type_str}"
            )
