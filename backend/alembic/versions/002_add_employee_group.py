"""Add employee group column.

Revision ID: 002
Revises: 001
Create Date: 2026-07-13

"""
from alembic import op
import sqlalchemy as sa


revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('employees', sa.Column('group', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('employees', 'group')
