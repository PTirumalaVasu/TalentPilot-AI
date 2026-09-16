"""Backfill seeded HR Admin identity rename on already-seeded databases (Story 10.1).

Revision ID: 014
Revises: 013
Create Date: 2026-09-16

"""
from alembic import op
import sqlalchemy as sa


revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None

RITA_ID = '550e8400-e29b-41d4-a716-446655440001'
OLD_EMAIL = 'rita@sails.example.com'
OLD_NAME = 'Rita the Recommender'
NEW_EMAIL = 'admin@sails.example.com'
NEW_NAME = 'Sails Admin'


def upgrade() -> None:
    # core/seeds.py::seed_employees/create_default_accounts are idempotent
    # (insert-once, skip-if-exists) -- they never touch an already-seeded
    # row's fields, so Story 10.1's rita@sails.example.com/"Rita the
    # Recommender" -> admin@sails.example.com/"Sails Admin" rename only
    # takes effect on a brand-new database. This one-time backfill carries
    # the rename to any database seeded before this migration.
    #
    # Scoped to exactly the known old values (not a blanket rewrite of the
    # RITA_ID row), mirroring migration 011's own password_hash backfill
    # precedent -- if this identity was ever manually changed to something
    # else on a given environment, that value is left alone rather than
    # silently overwritten.
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE employees SET name = :new_name, email = :new_email "
            "WHERE id = :id AND name = :old_name AND email = :old_email"
        ),
        {
            "id": RITA_ID,
            "old_name": OLD_NAME,
            "old_email": OLD_EMAIL,
            "new_name": NEW_NAME,
            "new_email": NEW_EMAIL,
        },
    )
    connection.execute(
        sa.text("UPDATE accounts SET email = :new_email WHERE id = :id AND email = :old_email"),
        {"id": RITA_ID, "old_email": OLD_EMAIL, "new_email": NEW_EMAIL},
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE employees SET name = :old_name, email = :old_email "
            "WHERE id = :id AND name = :new_name AND email = :new_email"
        ),
        {
            "id": RITA_ID,
            "old_name": OLD_NAME,
            "old_email": OLD_EMAIL,
            "new_name": NEW_NAME,
            "new_email": NEW_EMAIL,
        },
    )
    connection.execute(
        sa.text("UPDATE accounts SET email = :old_email WHERE id = :id AND email = :new_email"),
        {"id": RITA_ID, "old_email": OLD_EMAIL, "new_email": NEW_EMAIL},
    )
