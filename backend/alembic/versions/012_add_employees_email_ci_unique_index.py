"""Case-insensitive unique index on employees.email (Story 7.2, FR-24 AC2).

Revision ID: 012
Revises: 011
Create Date: 2026-09-11

"""
from alembic import op


revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # employees.email already has a plain (case-sensitive) UNIQUE constraint
    # -- left untouched. This adds a functional unique index on lower(email)
    # as a DB-level backstop, mirroring migration 006's identical fix for
    # skills.name: the app-layer case-insensitive pre-check
    # (employees/repository.py::get_employee_by_email_ci) can't fully
    # guarantee uniqueness on its own -- two concurrent creates with
    # different-case emails (e.g. "New@x.com" vs "new@x.com") could otherwise
    # both pass the pre-check before either commits, since neither collides
    # with the case-sensitive constraint. This index makes that impossible at
    # the DB level -- the second insert now fails with IntegrityError, which
    # employees/service.py::create_employee_service catches and converts to a
    # clean 409 (same code path as the existing exact-employee_code race).
    op.execute(
        "CREATE UNIQUE INDEX ix_employees_email_lower ON employees (lower(email))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX ix_employees_email_lower")
