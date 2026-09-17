"""Split Employee.name into first_name/last_name (Story 10.2, FR-34).

`name` itself is NOT dropped -- employees/service.py keeps writing it
(f"{first_name} {last_name}") on every create/update going forward, since
several other modules (assignments/, dashboard/, auth/, content/) read
Employee.name directly and are out of this story's scope.

Revision ID: 015
Revises: 014
Create Date: 2026-09-16

"""
from alembic import op
import sqlalchemy as sa


revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('employees', sa.Column('first_name', sa.String(length=255), nullable=True))
    op.add_column('employees', sa.Column('last_name', sa.String(length=255), nullable=True))

    # Backfill every existing row by splitting `name` on the last
    # whitespace-separated token (that token -> last_name, everything before
    # it -> first_name) -- there is no existing column boundary to split on,
    # so this is a one-time, best-effort heuristic (Story 10.2 Dev Notes).
    # Done in Python, not SQL, to keep the exact same split logic as
    # core/seeds.py::seed_employees uses for a fresh database, so the two
    # never disagree (mirrors migration 011's identical reasoning for
    # employee_code).
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, name FROM employees")).fetchall()
    for row in rows:
        name = (row.name or '').strip()
        if ' ' in name:
            # .strip() guards against an internal double space (e.g.
            # "John  Smith") leaving a trailing space on first_name --
            # rsplit only trims at the split point, not the rest of the
            # string.
            first_name, last_name = (part.strip() for part in name.rsplit(' ', 1))
        else:
            # Defensive only -- no current seeded/real row hits this path.
            first_name, last_name = name, 'Employee'
        connection.execute(
            sa.text("UPDATE employees SET first_name = :first_name, last_name = :last_name WHERE id = :id"),
            {"first_name": first_name, "last_name": last_name, "id": row.id},
        )

    op.alter_column('employees', 'first_name', nullable=False)
    op.alter_column('employees', 'last_name', nullable=False)


def downgrade() -> None:
    op.drop_column('employees', 'last_name')
    op.drop_column('employees', 'first_name')
