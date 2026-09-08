"""Add admin_api_keys table (AD-10, Story 6.5).

Revision ID: 005
Revises: 004
Create Date: 2026-09-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'admin_api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_foreign_key(
        'fk_admin_api_keys_admin_id_employees', 'admin_api_keys', 'employees', ['admin_id'], ['id']
    )
    op.create_unique_constraint(
        'uq_admin_api_keys_admin_id_source', 'admin_api_keys', ['admin_id', 'source']
    )


def downgrade() -> None:
    op.drop_constraint('uq_admin_api_keys_admin_id_source', 'admin_api_keys', type_='unique')
    op.drop_constraint('fk_admin_api_keys_admin_id_employees', 'admin_api_keys', type_='foreignkey')
    op.drop_table('admin_api_keys')
