"""Add Employee Roster Management profile fields + Account/Employee FK (Story 7.1, FR-24-29, AR-24).

Revision ID: 011
Revises: 010
Create Date: 2026-09-11

"""
from alembic import op
import sqlalchemy as sa
import bcrypt


revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # New Employee Roster Management profile fields (PRD FR-24). All
    # nullable except employee_code, added nullable first and backfilled
    # below before the NOT NULL/UNIQUE constraint is applied, so this
    # migration doesn't fail against the 5 already-seeded rows.
    op.add_column('employees', sa.Column('employee_code', sa.String(length=50), nullable=True))
    op.add_column('employees', sa.Column('phone', sa.String(length=50), nullable=True))
    op.add_column('employees', sa.Column('experience', sa.String(length=255), nullable=True))
    op.add_column('employees', sa.Column('technologies', sa.String(length=500), nullable=True))
    op.add_column('employees', sa.Column('position', sa.String(length=255), nullable=True))
    op.add_column('employees', sa.Column('project', sa.String(length=255), nullable=True))
    op.add_column('employees', sa.Column('manager_name', sa.String(length=255), nullable=True))
    op.add_column('employees', sa.Column('location', sa.String(length=255), nullable=True))
    # `department` is a new, distinct column -- deliberately NOT a reuse of
    # the pre-existing `employees.group` column (addendum.md flagged this
    # as an open implementation call; Story 7.1 resolves it: group's
    # existing semantics were never established as "department," so
    # repurposing it risked colliding with whatever it already means to
    # other code. `group` is untouched by this migration.)
    op.add_column('employees', sa.Column('department', sa.String(length=255), nullable=True))
    op.add_column(
        'employees',
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    # FR-27: null = active, non-null = archived (soft-delete flag).
    op.add_column('employees', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))

    # Backfill employee_code for the 5 pre-existing seeded Employees.
    # Ordered by core/seed_ids.py's declared UUID order (RITA, CASEY,
    # MORGAN, JORDAN, SAM) -- NOT by created_at, since all 5 rows share one
    # insert/flush and created_at isn't guaranteed distinct across them.
    # Values match core/seeds.py::seed_employees's own employee_code
    # assignments, so a fresh-DB seed run and this migration's backfill of
    # a pre-011 database always agree.
    op.execute("UPDATE employees SET employee_code = 'EMP-0001' WHERE id = '550e8400-e29b-41d4-a716-446655440001'")
    op.execute("UPDATE employees SET employee_code = 'EMP-0002' WHERE id = '550e8400-e29b-41d4-a716-446655440002'")
    op.execute("UPDATE employees SET employee_code = 'EMP-0003' WHERE id = '550e8400-e29b-41d4-a716-446655440003'")
    op.execute("UPDATE employees SET employee_code = 'EMP-0004' WHERE id = '550e8400-e29b-41d4-a716-446655440004'")
    op.execute("UPDATE employees SET employee_code = 'EMP-0005' WHERE id = '550e8400-e29b-41d4-a716-446655440005'")
    # Any other pre-existing Employee row (not one of the 5 demo seeds --
    # shouldn't exist in this pilot's data, but defensive against an
    # unknown local dev DB state) gets a random unique fallback code rather
    # than leaving the NOT NULL constraint below to fail.
    op.execute(
        "UPDATE employees SET employee_code = 'EMP-' || substr(id::text, 1, 8) "
        "WHERE employee_code IS NULL"
    )

    op.alter_column('employees', 'employee_code', nullable=False)
    op.create_unique_constraint('uq_employees_employee_code', 'employees', ['employee_code'])

    # AR-24: formalize the Account.id == Employee.id identity link the
    # existing seed data already assumes (core/seeds.py::create_default_accounts
    # seeds Account rows with the same UUIDs as the corresponding Employee
    # rows) as a real, declared FK constraint.
    op.create_foreign_key(
        'accounts_id_fkey',
        'accounts',
        'employees',
        ['id'],
        ['id'],
    )

    # Data fix: any pre-existing `accounts` rows (from core/seeds.py::
    # create_default_accounts, which is idempotent and won't re-run against
    # an already-seeded DB) may still hold the old placeholder
    # password_hash value, which has valid bcrypt *shape* but does not
    # actually validate against "demo123" (verified via bcrypt.checkpw
    # during Story 7.1's authoring). Replace it with a real hash so
    # Account-backed login works once a future story wires authenticate()
    # to check this table. Scoped to exactly the known placeholder value
    # (not a blanket rewrite) so a real, already-changed password on any
    # other environment is never touched.
    connection = op.get_bind()
    real_hash = bcrypt.hashpw(b"demo123", bcrypt.gensalt()).decode("utf-8")
    connection.execute(
        sa.text(
            "UPDATE accounts SET password_hash = :new_hash "
            "WHERE password_hash = :placeholder"
        ),
        {
            "new_hash": real_hash,
            "placeholder": "$2b$12$Ej1cKPsyxQqFWK/8PHT0d.c0yoIbR1Z2r.uV5XvDWMmr.B8xN3RBG",
        },
    )


def downgrade() -> None:
    op.drop_constraint('accounts_id_fkey', 'accounts', type_='foreignkey')
    op.drop_constraint('uq_employees_employee_code', 'employees', type_='unique')
    op.drop_column('employees', 'archived_at')
    op.drop_column('employees', 'updated_at')
    op.drop_column('employees', 'department')
    op.drop_column('employees', 'location')
    op.drop_column('employees', 'manager_name')
    op.drop_column('employees', 'project')
    op.drop_column('employees', 'position')
    op.drop_column('employees', 'technologies')
    op.drop_column('employees', 'experience')
    op.drop_column('employees', 'phone')
    op.drop_column('employees', 'employee_code')
