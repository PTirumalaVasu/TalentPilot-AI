"""Add assignment soft-delete columns.

Revision ID: 003
Revises: 002
Create Date: 2026-07-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('assignments', sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('assignments', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('assignments', sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_assignments_deleted_by_employees', 'assignments', 'employees', ['deleted_by'], ['id']
    )
    op.create_index('idx_assignments_active', 'assignments', ['active'])


def downgrade() -> None:
    op.drop_index('idx_assignments_active', table_name='assignments')
    op.drop_constraint('fk_assignments_deleted_by_employees', 'assignments', type_='foreignkey')
    op.drop_column('assignments', 'deleted_by')
    op.drop_column('assignments', 'deleted_at')
    op.drop_column('assignments', 'active')
