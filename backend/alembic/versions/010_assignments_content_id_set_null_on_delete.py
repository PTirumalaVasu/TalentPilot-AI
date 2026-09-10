"""assignments.content_id FK gains ON DELETE SET NULL (Story 6.9, FR-23).

Revision ID: 010
Revises: 009
Create Date: 2026-09-10

"""
from alembic import op


revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Story 6.9 AC6: hard-rejecting a content_catalog row (DELETE
    # /api/admin/content/{id}/reject) must succeed with 204 even when an
    # Assignment's content_id currently points at that exact row -- a real,
    # reachable state (match_content_for_skill, Story 2.4, can pick an
    # admin-attached row as an Assignment's best match at creation time).
    # Without this migration, assignments_content_id_fkey's default
    # NO ACTION referential action raises a Postgres IntegrityError on that
    # DELETE instead of the clean 204 the story promises. assignments.
    # content_id is already nullable=True and every reader of it (dashboard,
    # Content Discovery) already handles None -- it starts None whenever
    # match_content_for_skill finds nothing -- so SET NULL is a safe,
    # already-supported degradation. Same drop/recreate-named-constraint
    # shape as migration 007's identical precedent for
    # content_catalog_skill_id_fkey -> skills.id.
    op.drop_constraint('assignments_content_id_fkey', 'assignments', type_='foreignkey')
    op.create_foreign_key(
        'assignments_content_id_fkey',
        'assignments',
        'content_catalog',
        ['content_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    # Reverts the FK's referential action back to NO ACTION -- schema-only.
    # Any Assignment.content_id already nulled out by a live reject while
    # this migration was active is not restorable; same accepted one-way
    # migration characteristic as migration 007's own downgrade docstring.
    op.drop_constraint('assignments_content_id_fkey', 'assignments', type_='foreignkey')
    op.create_foreign_key(
        'assignments_content_id_fkey',
        'assignments',
        'content_catalog',
        ['content_id'],
        ['id'],
    )
