"""content_catalog.skill_id FK gains ON DELETE CASCADE (Story 6.3, FR-22).

Revision ID: 007
Revises: 006
Create Date: 2026-09-09

"""
from alembic import op


revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Story 6.3 AC4: deleting an unassigned Skill must also delete its
    # attached content_catalog rows, atomically ("both succeed or both
    # roll back together"). skills/ must not depend on content/ (AD-8) and
    # must not query content_catalog directly (AD-1 -- that table is
    # content/'s), so this is enforced at the DB level instead of a
    # cross-module service call: the FK's referential action does the
    # cascade, and skills/repository.py::delete_skill() only ever issues a
    # single DELETE against the skills table.
    #
    # Safe in practice: a Skill can only reach this DELETE while
    # ever_assigned = false, which (per AD-11) means it has never had an
    # Assignment -- assignments.skill_id's own FK (still RESTRICT, left
    # untouched) is never at risk of firing here.
    op.drop_constraint('content_catalog_skill_id_fkey', 'content_catalog', type_='foreignkey')
    op.create_foreign_key(
        'content_catalog_skill_id_fkey',
        'content_catalog',
        'skills',
        ['skill_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    # Reverts the FK's referential action back to RESTRICT -- schema-only.
    # Any content_catalog rows already cascade-deleted by a Skill delete
    # while this migration was live are gone permanently; this downgrade
    # cannot and does not restore them.
    op.drop_constraint('content_catalog_skill_id_fkey', 'content_catalog', type_='foreignkey')
    op.create_foreign_key(
        'content_catalog_skill_id_fkey',
        'content_catalog',
        'skills',
        ['skill_id'],
        ['id'],
    )
