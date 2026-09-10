"""content_catalog gains attached_by/origin; source enum extended to UDEMY (Story 6.8).

Revision ID: 009
Revises: 008
Create Date: 2026-09-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Story 6.8 AC1: purely additive, no data loss to existing rows.
    op.add_column('content_catalog', sa.Column('attached_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'content_catalog_attached_by_fkey', 'content_catalog', 'employees', ['attached_by'], ['id'],
    )
    # server_default='BATCH' backfills every pre-existing row correctly --
    # they all came from the batch ingestion job, not an Admin -- with no
    # explicit UPDATE statement needed.
    op.add_column('content_catalog', sa.Column('origin', sa.Text(), nullable=False, server_default='BATCH'))

    # content_source_enum is a native Postgres enum (not a CHECK constraint),
    # so extending it means ALTER TYPE ... ADD VALUE, not a column rewrite.
    # Safe inside Alembic's default transactional DDL on PG12+ (this project
    # runs PG16) as long as the new value is never used in the same
    # transaction -- this migration only adds it, nothing else.
    op.execute("ALTER TYPE content_source_enum ADD VALUE 'UDEMY'")


def downgrade() -> None:
    # Schema-only revert of the two new columns. Postgres has no
    # `ALTER TYPE ... DROP VALUE` -- the 'UDEMY' enum value cannot be
    # removed by this downgrade. Any content_catalog row already written
    # with source='UDEMY' while this migration was live is untouched by
    # this downgrade (same "cannot restore/revert data" category as
    # migration 007's downgrade note).
    op.drop_constraint('content_catalog_attached_by_fkey', 'content_catalog', type_='foreignkey')
    op.drop_column('content_catalog', 'attached_by')
    op.drop_column('content_catalog', 'origin')
