# Story 2.1a: Create the `integration_api_keys` Table

Status: ready-for-dev

**This is a real backend implementation story** — unlike every other story file in this project so far (which document the interactive HTML prototype under `design-artifacts/`), this one is for actual `backend/` code: a real Alembic migration and a real SQLAlchemy model. Nothing here has been built yet.

**Parent story**: `_bmad-output/planning-artifacts/epics/epic-automated-content-discovery.md` Story 1 ("Configure a Shared API Key Per Integration...") specifies this table but is itself framed around the *UI/gate* acceptance criteria. This story splits out just the database piece so a backend developer can implement it independently of — and as a prerequisite for — the UI work in `sprint-status.yaml`'s `2-1-configure-shared-api-key-per-integration`.

---

## Story

As a **Backend Developer**,
I want **a database migration and ORM model that create the `integration_api_keys` table**,
so that **the API Keys screen (Story 2-1) has real, persistent, encrypted storage to read from and write to, instead of the prototype's in-memory placeholder**.

## Acceptance Criteria

1. A new Alembic migration creates a table named `integration_api_keys` with columns: `id` (UUID, primary key), `provider` (enum-like string, `UNIQUE`), `encrypted_key` (text, not null), `updated_by` (UUID, FK to `employees.id`, not null), `created_at` (timestamptz, default now), `updated_at` (timestamptz, default now).
2. Inserting two rows with the same `provider` value fails (`UNIQUE` constraint enforced) — matches the epic's "one row per provider, organization-wide" design.
3. Inserting a row whose `updated_by` doesn't match a real `employees.id` fails (FK constraint enforced).
4. A corresponding `IntegrationApiKey` SQLAlchemy model exists in `backend/app/assignments/models.py` (co-located with `Employee`/`Skill`/`ContentCatalog` — this codebase keeps its core domain models in one file, not split by feature module; see Dev Notes if a separate module is preferred instead), importable and usable by the eventual `POST/GET /api/integration-keys` service layer (out of scope for this story — see epic Story 1's AC for that work).
5. `encrypted_key` is genuinely encrypted before being written — this story does NOT include the encryption implementation itself (that's a separate concern, likely a shared utility used by whatever service writes to this table), but the column must never be written to with a plaintext value even during this story's own testing/seeding.
6. Migration is reversible (`downgrade()` drops the table cleanly) and follows this repo's existing numbering (`alembic/versions/00N_*.py`, sequential `revision`/`down_revision`).

## Tasks / Subtasks

- [ ] Task 1: Write the Alembic migration (AC: #1, #2, #3, #6)
  - [ ] Subtask 1.1: Determine the next sequential revision number (`004` as of this story's authoring — confirm against `backend/alembic/versions/` at implementation time in case other migrations landed first)
  - [ ] Subtask 1.2: `upgrade()` — create table with all 6 columns, `UNIQUE` on `provider`, FK on `updated_by` → `employees.id`
  - [ ] Subtask 1.3: `downgrade()` — drop the table
- [ ] Task 2: Add the `IntegrationApiKey` model (AC: #4)
  - [ ] Subtask 2.1: Add class to `backend/app/assignments/models.py`, matching existing style (`Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`, etc.)
  - [ ] Subtask 2.2: Decide `provider` as a real `Enum(...)` (matching `ContentCatalog.source`'s `content_source_enum` pattern) vs. plain `String` — recommend `Enum` for consistency with the rest of this file, see Dev Notes
- [ ] Task 3: Verify (AC: #1, #2, #3)
  - [ ] Subtask 3.1: Run the migration against a real/test database, confirm the table + constraints exist
  - [ ] Subtask 3.2: Write a focused test (matching this repo's existing test style — see `backend/tests/`) asserting the `UNIQUE(provider)` and FK constraints actually reject bad inserts, not just that the migration runs without error

## Dev Notes

- **Migration tooling confirmed, not assumed**: this codebase uses Alembic (`backend/alembic.ini`, `backend/alembic/versions/`), currently at `003_add_assignment_soft_delete.py`. Reference that file directly for the exact style (plain `op.*` calls, named constraints like `fk_assignments_deleted_by_employees`, no ORM-level `Base.metadata.create_all` shortcuts).
- **Models file confirmed, not assumed**: `backend/app/assignments/models.py` is where `Employee`, `Skill`, `ContentCatalog`, `Assignment`, `SkillProgress`, `AssignmentOverride` all live — despite the file's name, it's this codebase's single home for core domain models, not split per-module. `backend/app/content/models.py` exists but is an empty stub (just a docstring) — don't be misled by the module name into thinking content-adjacent models belong there; they don't, today.
- **Enum convention**: existing enums in this file follow `Enum("VAL1", "VAL2", name="some_enum")` (e.g. `role_enum`, `content_source_enum`, `content_type_enum`). Recommend `Enum("YOUTUBE", "UDEMY", name="api_key_provider_enum")` for `provider`, consistent with that pattern — a plain `String` would also satisfy the AC's `UNIQUE` requirement but breaks from this file's existing convention without a strong reason to.
- **Reference implementation** (for a developer to adapt, not copy-paste blindly — verify column/constraint details against the live schema at implementation time):

  ```python
  # backend/alembic/versions/004_add_integration_api_keys.py
  """Add integration_api_keys table.

  Revision ID: 004
  Revises: 003
  Create Date: 2026-09-08

  """
  from alembic import op
  import sqlalchemy as sa
  from sqlalchemy.dialects import postgresql

  revision = '004'
  down_revision = '003'
  branch_labels = None
  depends_on = None


  def upgrade() -> None:
      op.create_table(
          'integration_api_keys',
          sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
          sa.Column('provider', sa.Enum('YOUTUBE', 'UDEMY', name='api_key_provider_enum'), nullable=False),
          sa.Column('encrypted_key', sa.Text(), nullable=False),
          sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=False),
          sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
          sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
      )
      op.create_unique_constraint('uq_integration_api_keys_provider', 'integration_api_keys', ['provider'])
      op.create_foreign_key(
          'fk_integration_api_keys_updated_by_employees',
          'integration_api_keys', 'employees', ['updated_by'], ['id'],
      )


  def downgrade() -> None:
      op.drop_constraint('fk_integration_api_keys_updated_by_employees', 'integration_api_keys', type_='foreignkey')
      op.drop_constraint('uq_integration_api_keys_provider', 'integration_api_keys', type_='unique')
      op.drop_table('integration_api_keys')
      sa.Enum(name='api_key_provider_enum').drop(op.get_bind(), checkfirst=True)
  ```

  ```python
  # backend/app/assignments/models.py — add alongside the existing classes
  class IntegrationApiKey(Base):
      __tablename__ = "integration_api_keys"

      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      provider = Column(Enum("YOUTUBE", "UDEMY", name="api_key_provider_enum"), nullable=False, unique=True)
      encrypted_key = Column(Text, nullable=False)
      updated_by = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
      created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
      updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

      # Relationship
      updated_by_user = relationship("Employee")
  ```

### Project Structure Notes

- No conflicts detected — `app/assignments/models.py` and `alembic/versions/` are established, unambiguous locations; this story doesn't introduce a new module.
- **Open question for the developer, not resolved here**: `provider` as `Enum` requires a Postgres `CREATE TYPE`, which the migration's `downgrade()` must explicitly drop (included above) — Postgres doesn't auto-drop enum types when the table using them is dropped, unlike columns. Double-check this against how `role_enum`/`content_source_enum` are (or aren't) cleaned up in their own migrations' `downgrade()` before assuming the pattern above is exactly right — not verified against those migrations' `downgrade()` bodies as part of this story.

### References

- [Source: backend/alembic/versions/003_add_assignment_soft_delete.py] — migration style reference
- [Source: backend/app/assignments/models.py#L26-L79] — model style reference (Employee, Skill, ContentCatalog)
- [Source: _bmad-output/planning-artifacts/epics/epic-automated-content-discovery.md#Story 1] — the table's origin/design rationale, security notes (encryption at rest, write-only API surface) not repeated in this story
- [Source: design-artifacts/E-Development/01-Assign-New-Skill-Prototype/stories/HR-Dashboard.12-api-keys-view.md] — the prototype UI this table will eventually back

## Dev Agent Record

### Agent Model Used

(fill in at implementation time)

### Debug Log References

### Completion Notes List

### File List
