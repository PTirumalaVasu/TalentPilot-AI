"""Add skills.ever_assigned lock flag (AD-11, Story 6.1).

Revision ID: 004
Revises: 003
Create Date: 2026-09-08

"""
from alembic import op
import sqlalchemy as sa


revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'skills',
        sa.Column('ever_assigned', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # One-time backfill: any Skill already referenced by an Assignment is
    # retroactively locked, so pre-existing assigned Skills aren't left
    # incorrectly editable/deletable post-migration (AD-11).
    op.execute(
        "UPDATE skills SET ever_assigned = true "
        "WHERE id IN (SELECT DISTINCT skill_id FROM assignments)"
    )


def downgrade() -> None:
    op.drop_column('skills', 'ever_assigned')
