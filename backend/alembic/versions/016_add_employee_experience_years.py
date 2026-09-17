"""Add Employee.experience_years (Story 10.4, FR-36).

Nullable numeric field alongside the existing free-text `experience` column,
which is unaffected -- both columns coexist (Story 10.4 Dev Notes: the
free-text field stays for flexible notes like "3+ years, mid-level", while
`experience_years` is the strict integer the Experience Distribution panel's
7 fixed buckets (0-4, 5-7, 8-9, 10-11, 12-14, 15-19, 20+) bucket against).
No backfill -- there is no existing column to derive a reliable integer from
(`experience` is free text, e.g. "5+ yrs"), so every pre-existing row starts
NULL and is simply excluded from every bucket until an HR Admin fills it in
via Create/Edit Employee.

Revision ID: 016
Revises: 015
Create Date: 2026-09-17

"""
from alembic import op
import sqlalchemy as sa


revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('employees', sa.Column('experience_years', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('employees', 'experience_years')
