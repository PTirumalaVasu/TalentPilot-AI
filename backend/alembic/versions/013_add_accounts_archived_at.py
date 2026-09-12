"""Add accounts.archived_at (Story 7.5, FR-27/AR-25).

Revision ID: 013
Revises: 012
Create Date: 2026-09-12

"""
from alembic import op
import sqlalchemy as sa


revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Mirrors employees.archived_at (migration 011) on the Account table
    # (Account.id == Employee.id, AR-24). Kept in sync by
    # employees/service.py's delete/archive service in the same transaction
    # that sets employees.archived_at -- deliberately NOT read by importing
    # app.employees.models.Employee into auth/service.py (that would create
    # a circular import, since employees/service.py already imports
    # auth.service/auth.repository). auth/service.py::get_current_user
    # checks this column directly to reject an archived identity's still-valid
    # session on its next protected request (AC4/AR-25), without any
    # cross-module model dependency.
    op.add_column('accounts', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('accounts', 'archived_at')
