"""Case-insensitive unique index on skills.name (Story 6.2 code review).

Revision ID: 006
Revises: 005
Create Date: 2026-09-09

"""
from alembic import op


revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # skills.name already has a plain (case-sensitive) UNIQUE constraint
    # (Story 1.7) -- left untouched. This adds a functional unique index on
    # lower(name) as a DB-level backstop closing the race the app-layer
    # case-insensitive pre-check (skills/repository.py::get_skill_by_name_ci)
    # can't fully guarantee on its own: two concurrent creates with
    # different-case names (e.g. "Python" vs "PYTHON") could otherwise both
    # pass the pre-check before either commits, since neither collides with
    # the case-sensitive constraint. This index makes that impossible at the
    # DB level -- the second insert now fails with IntegrityError, which
    # skills/service.py::create_skill_service catches and converts to a
    # clean 409 (same code path as the existing exact-name race).
    op.execute(
        "CREATE UNIQUE INDEX ix_skills_name_lower ON skills (lower(name))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX ix_skills_name_lower")
