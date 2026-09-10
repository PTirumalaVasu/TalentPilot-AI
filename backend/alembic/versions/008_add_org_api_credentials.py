"""Add org_api_credentials table (AD-10, Story 6.5).

Revision ID: 008
Revises: 007
Create Date: 2026-09-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'org_api_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('configured_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_foreign_key(
        'fk_org_api_credentials_configured_by_employees', 'org_api_credentials', 'employees', ['configured_by'], ['id'],
        ondelete='SET NULL',
    )
    op.create_unique_constraint(
        'uq_org_api_credentials_source', 'org_api_credentials', ['source']
    )


def downgrade() -> None:
    op.drop_constraint('uq_org_api_credentials_source', 'org_api_credentials', type_='unique')
    op.drop_constraint('fk_org_api_credentials_configured_by_employees', 'org_api_credentials', type_='foreignkey')
    op.drop_table('org_api_credentials')
