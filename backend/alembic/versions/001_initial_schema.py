"""Initial schema setup with all 7 tables.

Revision ID: 001
Revises:
Create Date: 2026-07-09

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create role enums.
    # IMPORTANT: every column below that reuses one of these type names MUST
    # use sqlalchemy.dialects.postgresql.ENUM(..., create_type=False) (PGEnum
    # below) — not sa.Enum(..., create_type=False). The generic sa.Enum
    # silently drops that kwarg (it isn't a real parameter on that class), so
    # SQLAlchemy's DDL compiler auto-issues a second CREATE TYPE on first
    # table use, colliding with the explicit CREATE TYPE below and raising
    # asyncpg.exceptions.DuplicateObjectError.
    op.execute("CREATE TYPE role_enum AS ENUM ('HR_ADMIN', 'EMPLOYEE')")
    op.execute("CREATE TYPE content_type_enum AS ENUM ('VIDEO', 'DOCUMENT', 'WEBSITE')")
    op.execute("CREATE TYPE content_source_enum AS ENUM ('YOUTUBE', 'MANUAL')")
    op.execute("CREATE TYPE status_enum AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED')")

    # Create accounts table
    op.create_table(
        'accounts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', PGEnum('HR_ADMIN', 'EMPLOYEE', name='role_enum', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_accounts_email', 'accounts', ['email'])

    # Create employees table
    op.create_table(
        'employees',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', PGEnum('HR_ADMIN', 'EMPLOYEE', name='role_enum', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_employees_email', 'employees', ['email'])

    # Create skills table
    op.create_table(
        'skills',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('embedding', Vector(384), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # Create content_catalog table
    op.create_table(
        'content_catalog',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('skill_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', PGEnum('VIDEO', 'DOCUMENT', 'WEBSITE', name='content_type_enum', create_type=False), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('embedding', Vector(384), nullable=False),
        sa.Column('source', PGEnum('YOUTUBE', 'MANUAL', name='content_source_enum', create_type=False), nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_content_skill', 'content_catalog', ['skill_id'])
    op.create_index('idx_content_embedding', 'content_catalog', ['embedding'], postgresql_using='ivfflat')

    # Create assignments table
    op.create_table(
        'assignments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('employee_id', sa.UUID(), nullable=False),
        sa.Column('skill_id', sa.UUID(), nullable=False),
        sa.Column('content_id', sa.UUID(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('assigned_by', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['content_id'], ['content_catalog.id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_assignments_employee', 'assignments', ['employee_id'])
    op.create_index('idx_assignments_skill', 'assignments', ['skill_id'])

    # Create skill_progress table
    op.create_table(
        'skill_progress',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('assignment_id', sa.UUID(), nullable=False),
        sa.Column('watch_position', sa.Integer(), nullable=False),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.literal(False)),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id'),
    )
    op.create_index('idx_progress_assignment', 'skill_progress', ['assignment_id'], unique=True)
    op.create_index('idx_progress_event_time', 'skill_progress', ['event_time'])

    # Create assignment_overrides table
    op.create_table(
        'assignment_overrides',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('assignment_id', sa.UUID(), nullable=False),
        sa.Column('set_by', sa.UUID(), nullable=False),
        sa.Column('set_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.literal(True)),
        sa.Column('override_status', PGEnum('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', name='status_enum', create_type=False), nullable=False),
        sa.Column('reversed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reversed_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ),
        sa.ForeignKeyConstraint(['reversed_by'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['set_by'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_overrides_assignment', 'assignment_overrides', ['assignment_id'])
    op.create_index('idx_overrides_active', 'assignment_overrides', ['active'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_overrides_active', table_name='assignment_overrides')
    op.drop_index('idx_overrides_assignment', table_name='assignment_overrides')
    op.drop_table('assignment_overrides')

    op.drop_index('idx_progress_event_time', table_name='skill_progress')
    op.drop_index('idx_progress_assignment', table_name='skill_progress')
    op.drop_table('skill_progress')

    op.drop_index('idx_assignments_skill', table_name='assignments')
    op.drop_index('idx_assignments_employee', table_name='assignments')
    op.drop_table('assignments')

    op.drop_index('idx_content_embedding', table_name='content_catalog')
    op.drop_index('idx_content_skill', table_name='content_catalog')
    op.drop_table('content_catalog')

    op.drop_table('skills')
    op.drop_index('ix_employees_email', table_name='employees')
    op.drop_table('employees')

    op.drop_index('ix_accounts_email', table_name='accounts')
    op.drop_table('accounts')

    # Drop enums
    op.execute('DROP TYPE status_enum')
    op.execute('DROP TYPE content_source_enum')
    op.execute('DROP TYPE content_type_enum')
    op.execute('DROP TYPE role_enum')
