---
baseline_commit: adf1c2a
---

# Story 2.1: Content Catalog Data Model & Schema

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want to define the Content Catalog data model and API schemas,
so that content records can be stored and matched to Skills.

## Scope Notes (read before starting)

1. **The `content_catalog` table ALREADY EXISTS** — Story 1.7 created all 7 database tables including `ContentCatalog` ORM model in `backend/app/assignments/models.py` lines 55-76. This story does NOT create the table schema again. What's missing: Pydantic schemas (`content/schemas.py`), repository layer (`content/repository.py`), service layer (`content/service.py`), and tests verifying the data model works.

2. **This is Epic 2 Story 1 — the foundation for the entire content module.** Stories 2.2 (embedding model), 2.3 (batch ingestion), and 2.4 (semantic matching) all depend on the Pydantic schemas and repository/service patterns established here. Get the API contract and layering right now.

3. **Architecture AD-1 single-owner enforcement starts here.** The `content/` module is the ONLY code that queries or writes `content_catalog`. Even though the ORM model lives in `assignments/models.py` (due to SQLAlchemy relationship requirements), only `content/repository.py` may import and query it. No other module (assignments, progress, dashboard) touches `content_catalog` directly — they must call `content/service.py` methods.

4. **Embedding vector is NEVER exposed in API responses unless explicitly requested for debug.** The acceptance criteria specifies "without the raw embedding vector, unless explicitly requested for admin/debug purposes." Default `ContentResponse` excludes the 384-dim embedding array — it's 1.5KB per record and serves no client purpose. Only include it in a separate `ContentWithEmbedding` schema for Story 2.3's ingestion debugging.

5. **The `metadata` field name collision was already resolved in Story 1.7.** The SQLAlchemy column is named `content_metadata` in Python but maps to `metadata` in the database via `name="metadata"` — this avoids conflicting with SQLAlchemy's reserved `.metadata` attribute. Use `content_metadata` everywhere in repository/service code.

## Acceptance Criteria

### AC1 — Pydantic schemas for Content responses (without embedding by default)

**Given** the architecture requirement for semantic matching  
**When** I define response schemas in `content/schemas.py`  
**Then** I create:
- `ContentResponse` (default public API response):
  - `id` (UUID)
  - `skill_id` (UUID)
  - `title` (str)
  - `description` (str | None)
  - `type` (Literal["VIDEO", "DOCUMENT", "WEBSITE"])
  - `url` (str)
  - `source` (Literal["YOUTUBE", "MANUAL"])
  - `ingested_at` (datetime)
  - `metadata` (dict[str, Any] | None) — the JSONB field
  - **EXCLUDES** `embedding` field (per scope note 4)

**And** a separate `ContentWithEmbedding` schema:
- Inherits from `ContentResponse`
- Adds `embedding` field (list[float], 384-dim)
- Used ONLY for admin/debug purposes (Story 2.3 ingestion verification)

### AC2 — Internal schema for embedding computation (Story 2.2 will use this)

**Given** Story 2.2 will need to compute embeddings  
**When** I define internal schemas  
**Then** I create:
- `EmbeddingInput`:
  - `text` (str) — the concatenated skill name + description
- `EmbeddingOutput`:
  - `embedding` (list[float], 384-dim)
  - `text` (str) — echo back for verification

**And** these schemas are marked as internal-only (not exposed via any router endpoint in this story)

### AC3 — Repository layer with single-owner enforcement

**Given** AD-1 single-owner data module pattern  
**When** I implement `content/repository.py`  
**Then** it provides:
- `get_content_by_id(db: AsyncSession, content_id: UUID) -> ContentCatalog | None`
- `list_content_by_skill(db: AsyncSession, skill_id: UUID) -> list[ContentCatalog]`
- `create_content(db: AsyncSession, content_data: dict) -> ContentCatalog`

**And** this repository is the ONLY code that queries `content_catalog` (AD-1)  
**And** it imports `ContentCatalog` from `app.assignments.models` (where Story 1.7 defined it)  
**And** all methods use async SQLAlchemy 2.0 patterns (async session, `select()`, `result.scalars()`)

### AC4 — Service layer exposing public API

**Given** AD-1 cross-module access via Service API  
**When** I implement `content/service.py`  
**Then** it provides:
- `get_content(db: AsyncSession, content_id: UUID) -> ContentResponse | None`
- `list_content_for_skill(db: AsyncSession, skill_id: UUID) -> list[ContentResponse]`

**And** service methods return Pydantic `ContentResponse` (ORM → Pydantic conversion)  
**And** service methods call repository methods (never query the DB directly)  
**And** this service layer is how other modules (Story 3.x assignments, Story 5.x dashboard) will access content data

### AC5 — Tests verifying data model and API contracts

**Given** the schemas and repository/service are implemented  
**When** I write tests  
**Then** I verify:
- `ContentResponse` schema correctly serializes a `ContentCatalog` ORM instance (excludes embedding)
- `ContentWithEmbedding` schema includes the 384-dim embedding array
- Repository `get_content_by_id` returns None for non-existent ID
- Repository `list_content_by_skill` returns empty list for skill with no content
- Repository `create_content` persists a record and returns the ORM instance
- Service layer converts ORM to Pydantic correctly (spot-check field mapping)

**And** tests use the existing live database (Docker Compose Postgres on port 5433)  
**And** tests follow pytest + async patterns from Story 1.7

## Tasks / Subtasks

- [x] Task 1: Pydantic schemas (AC: #1, #2)
  - [x] `content/schemas.py`: define `ContentResponse` (no embedding field)
  - [x] `content/schemas.py`: define `ContentWithEmbedding(ContentResponse)` (adds embedding field)
  - [x] `content/schemas.py`: define `EmbeddingInput` and `EmbeddingOutput` (internal, for Story 2.2)
  - [x] Add `from pydantic import Field` for field metadata if needed
  - [x] Use `Literal["VIDEO", "DOCUMENT", "WEBSITE"]` for type field (matches ORM enum)
  - [x] Use `Literal["YOUTUBE", "MANUAL"]` for source field (matches ORM enum)
  
- [x] Task 2: Repository layer (AC: #3)
  - [x] `content/repository.py`: import `ContentCatalog` from `app.assignments.models`
  - [x] `content/repository.py`: import `AsyncSession`, `select`, `UUID` from sqlalchemy/typing
  - [x] `content/repository.py`: implement `get_content_by_id` (async, returns ORM or None)
  - [x] `content/repository.py`: implement `list_content_by_skill` (async, filters by skill_id, returns list of ORM)
  - [x] `content/repository.py`: implement `create_content` (async, takes dict, adds to session, flushes, returns ORM)
  - [x] Follow async SQLAlchemy 2.0 pattern: `result = await db.execute(select(...))`, `result.scalar_one_or_none()` or `result.scalars().all()`

- [x] Task 3: Service layer (AC: #4)
  - [x] `content/service.py`: import repository methods
  - [x] `content/service.py`: import `ContentResponse` from `content/schemas`
  - [x] `content/service.py`: implement `get_content` (calls repo, converts ORM to Pydantic)
  - [x] `content/service.py`: implement `list_content_for_skill` (calls repo, converts list of ORMs to list of Pydantic)
  - [x] Use Pydantic `.model_validate()` for ORM → Pydantic conversion (SQLAlchemy 2.0 ORM instances are dict-compatible)

- [x] Task 4: Tests (AC: #5)
  - [x] `tests/test_content_schemas.py`: test `ContentResponse` excludes embedding
  - [x] `tests/test_content_schemas.py`: test `ContentWithEmbedding` includes embedding (384 elements)
  - [x] `tests/test_content_repository.py`: test `get_content_by_id` with existing and non-existent ID
  - [x] `tests/test_content_repository.py`: test `list_content_by_skill` with skill that has content and skill with no content
  - [x] `tests/test_content_repository.py`: test `create_content` persists and returns ORM
  - [x] `tests/test_content_service.py`: test service layer ORM → Pydantic conversion
  - [x] Use existing database connection from `conftest.py` (Story 1.7 already set up async session fixture)
  - [ ] ~~Use existing seed data (Story 1.7 seeded 5 skills with embeddings)~~ — **correction (code review):** tests actually create fresh, randomly-named `Skill` rows per test rather than referencing the pre-seeded skills. Functionally fine (tests pass, no coupling to seed-data drift), but this checkbox was inaccurately marked done.

### Review Findings

- [x] [Review][Patch] `test_engine`'s scope change (session→function) plus unchanged `Base.metadata.create_all()`/`drop_all()` against the real shared `settings.DATABASE_URL` wiped the entire dev database after every single test using `db_session` — 3 independent review layers converged on this, and it was already confirmed live by 3 downstream stories (2.2, 2.4, 3.3) that each hit the wipe and logged it in `deferred-work.md` as "CRITICAL, blocks the full test suite." [backend/tests/conftest.py] **Resolved (user decision):** dropped `create_all`/`drop_all` entirely (schema is already provisioned by Alembic per Story 1.7); test isolation now relies on `db_session`'s existing `await session.rollback()`, matching the pattern every other live-DB test file in this codebase already uses. `test_content_repository.py`/`test_content_service.py` updated to `flush()` instead of `commit()` so their rows are actually rollback-able.
- [x] [Review][Patch] `ContentResponse.metadata` is typed `Optional` but has no `default=None` on its `Field(alias=...)`, making it a *required* field in Pydantic v2 despite the type hint (verified empirically against the installed pydantic 2.13) [backend/app/content/schemas.py:22] — fixed, `default=None` added.
- [x] [Review][Patch] `test_content_response_type_field_validation`/`test_content_response_source_field_validation` assert the overly broad `pytest.raises(Exception)` instead of `pydantic.ValidationError` for invalid enum values [backend/tests/test_content_schemas.py] — fixed.
- [x] [Review][Patch] Dead import: `datetime, timezone` imported but never used [backend/tests/test_content_repository.py:3] — fixed, import removed.
- [x] [Review][Patch] Task 4 checklist and Testing Requirements both claim tests "use existing seed data (Story 1.7 seeded 5 skills)" — every test instead creates a fresh randomly-named `Skill`; none reference the pre-seeded skills. Functionally harmless, but the completion record is inaccurate. — corrected below.
- [x] [Review][Defer] `list_content_by_skill` has no `LIMIT`/pagination or explicit `ORDER BY` [backend/app/content/repository.py] — deferred, pre-existing gap, not reachable until a router endpoint exposes it (Story 2.4/2.5)
- [x] [Review][Defer] `create_content` takes a bare `dict` with no request-side validation schema [backend/app/content/repository.py] — deferred, not reachable today (no caller/route yet); Story 2.3's batch-ingestion job should define validated input before wiring this up
- [x] [Review][Defer] The `Literal["...", "WEBSITE"]` branch is never exercised end-to-end by any test (only VIDEO/DOCUMENT are used) [backend/tests/test_content_schemas.py, test_content_repository.py, test_content_service.py] — deferred, minor coverage gap, satisfies AC5's literal "spot-check" bar as written

## Dev Notes

### Why This Story Exists Even Though The Table Exists

Story 1.7 created all database tables (including `content_catalog`) and seed data to prove the schema worked. But it deliberately did NOT create Pydantic schemas, repository, or service layers — those are module-specific concerns that belong with the owning module, not in a database-init story. This story completes the `content/` module foundation that Stories 2.2-2.6 will build on.

### The embedding field exclusion is a performance decision, not arbitrary

A 384-dim float embedding serialized to JSON is ~1.5KB per content item. For a list of 20 recommendations, that's 30KB of data the client cannot use (embeddings are server-side-only for cosine similarity queries). The AC's "without the raw embedding vector, unless explicitly requested" phrasing comes from the architecture spine's API schema convention: storage shape must not leak into the contract. The embedding is a storage/indexing detail, not API surface.

### ORM model location vs repository location

The `ContentCatalog` ORM model lives in `assignments/models.py` (not `content/models.py`) because SQLAlchemy relationships require all related models in one file to avoid circular imports. This is a known SQLAlchemy limitation. **However**, AD-1 enforcement still applies: only `content/repository.py` queries it. The physical file location doesn't override the logical ownership boundary.

### Service layer is the cross-module contract

Other modules (assignments, dashboard) will never import `content/repository.py` or `ContentCatalog`. They will call `content/service.py` methods and receive Pydantic `ContentResponse` objects. This enforces AD-1 (single-owner) and keeps the ORM as an internal implementation detail.

### Test against the live database, not mocks

Story 1.7 proved the database schema works and seeded real data. These tests should use the same live Postgres instance (Docker Compose on port 5433) via the async session fixture already in `conftest.py`. Don't mock the database or ORM — test against real SQLAlchemy queries hitting real Postgres.

### The metadata field naming quirk

In Python code, access the field as `content.content_metadata` (not `content.metadata`). In SQL and API schemas, it's `metadata`. This is Story 1.7's resolution of the SQLAlchemy reserved-attribute conflict. The Pydantic `ContentResponse` will have a `metadata` field (matching the database column name), but the ORM access is `content.content_metadata`.

### No router endpoints in this story

This story establishes schemas, repository, and service — but does NOT create any FastAPI routes. Stories 2.3 (ingestion) and 2.4 (matching) will add the actual HTTP endpoints. This story's service methods are called internally, not exposed as REST resources yet.

## Project Structure Notes

Changes land in:
- `backend/app/content/schemas.py` (NEW: Pydantic schemas)
- `backend/app/content/repository.py` (NEW: repository layer, currently 1-line stub)
- `backend/app/content/service.py` (NEW: service layer, currently 1-line stub)
- `backend/tests/test_content_schemas.py` (NEW: schema tests)
- `backend/tests/test_content_repository.py` (NEW: repository tests)
- `backend/tests/test_content_service.py` (NEW: service tests)

No changes to:
- `backend/app/assignments/models.py` (ContentCatalog model already exists from Story 1.7)
- `backend/app/content/router.py` (no HTTP endpoints in this story)
- `backend/app/main.py` (content router already mounted from Story 1.1, currently empty)

## Library/Framework Requirements

- **Pydantic 2.13.4** (already installed) — for schemas, `.model_validate()` ORM conversion
- **SQLAlchemy 2.0.51 async** (already installed) — for ORM querying, `select()`, `AsyncSession`
- **asyncpg 0.31.0** (already installed) — PostgreSQL async driver
- **pytest + pytest-asyncio** (already installed) — for async test execution
- **pgvector 0.3.0** (already installed from Story 1.7) — Vector type in ORM model

**No new dependencies.** All required libraries were installed in Stories 1.1 and 1.7.

## Testing Requirements

- Test framework: `pytest` + `pytest-asyncio` (existing)
- Database: Live PostgreSQL 16 in Docker Compose on port 5433 (existing)
- Async session fixture: `conftest.py` already has `async_session` fixture from Story 1.7
- Seed data: Story 1.7 seeded 5 skills with embeddings — use these for `list_content_by_skill` tests
- Pattern: Follow Story 1.7's `tests/test_schema_definitions.py` for ORM-level tests; add repository/service tests at integration level

Test coverage expectations:
- Schema serialization (Pydantic)
- Repository CRUD operations (against live DB)
- Service layer ORM → Pydantic conversion
- Edge cases: non-existent IDs, empty lists

## Previous Story Intelligence

From Story 1.7 (`backend/app/assignments/models.py`, status `done`):
- **ContentCatalog ORM model already exists** (lines 55-76)
- Table has all required columns: id, skill_id, title, description, type, url, embedding (Vector 384), source, ingested_at, content_metadata
- Enums defined: `content_type_enum` (VIDEO, DOCUMENT, WEBSITE), `content_source_enum` (YOUTUBE, MANUAL)
- Indexes created: `idx_content_skill` (skill_id), `idx_content_embedding` (pgvector ivfflat)
- Relationships: `skill` (many-to-one to Skill), `assignments` (one-to-many to Assignment)
- **Known quirk**: `content_metadata` field in Python maps to `metadata` column in DB via `name="metadata"`

From Story 1.5 (`1-5-sign-out-and-session-invalidation.md`, status `done`):
- Established pattern: service layer methods take `AsyncSession` as first parameter
- Established pattern: tests against real `app` object for route-level, test-file-local app for dependency-only tests
- Established pattern: Pydantic schemas separate from ORM models (no mixing storage shape with API contract)

From Story 1.1 (`1-1-project-structure-and-core-dependencies.md`, status `done`):
- Module structure: each feature has `router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py`
- Router already mounted at `/api/content` in `main.py` (currently empty APIRouter)
- All async, FastAPI + SQLAlchemy 2.0 async + asyncpg

## Architecture Compliance

**AD-1 — Single-owner data modules:**
- `content/` module is the sole owner of `content_catalog` table
- Only `content/repository.py` queries this table
- Other modules must call `content/service.py` for access
- ✅ This story establishes that boundary

**AD-7 — Content ingestion is batch-only:**
- This story does NOT implement ingestion (that's Story 2.3)
- Repository `create_content` method will be used by Story 2.3's batch job
- No live per-request YouTube search (deferred to Story 2.3)

**AD-8 — Module dependency direction:**
- `content/` depends on `core/` for DB session, config
- `content/` does NOT depend on `assignments/`, `progress/`, or `dashboard/`
- Other modules MAY depend on `content/service.py` (read-only access)
- ✅ Layering preserved

**Stack compliance:**
- Python 3.12+ (this environment has 3.14.0, accepted per Story 1.1)
- SQLAlchemy 2.0.51 async + asyncpg 0.31.0 (installed)
- Pydantic 2.13.4 (installed)
- PostgreSQL 16 + pgvector (running in Docker)
- sentence-transformers for embeddings (Story 2.2 will install this)

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1] — full AC text
- [Source: backend/app/assignments/models.py:55-76] — existing ContentCatalog ORM model (Story 1.7)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-1] — single-owner data module pattern
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-7] — content ingestion batch-only rule
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#Stack] — sentence-transformers embedding model (384-dim)
- [Source: backend/app/core/db.py] — async session management (Story 1.1)
- [Source: tests/conftest.py] — async_session fixture (Story 1.7)

## Git Intelligence

Recent commits show:
- Story 1.7 database migration merged to main (commit `1c99463`)
- All Epic 1 stories (1.1-1.5) complete and merged
- Current branch: `Epic2-stories` (created for Epic 2 work)
- Pattern: feature branches merged via PR, then next story starts

Expected workflow for this story:
1. Implement on `Epic2-stories` branch (or create `feature/story2.1` if needed)
2. TDD: write failing tests first, then implement
3. Run tests: `pytest backend/tests/test_content_*.py -v`
4. Mark story status: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`
5. Merge via PR when code review passes

## Completion Checklist

- [x] Pydantic schemas created (`ContentResponse`, `ContentWithEmbedding`, `EmbeddingInput`, `EmbeddingOutput`)
- [x] Repository layer implemented (3 methods: get by ID, list by skill, create)
- [x] Service layer implemented (2 methods: get, list)
- [x] Tests written and passing (schema, repository, service)
- [x] All tests pass: `pytest backend/tests/test_content_*.py -v` — 16/16 passed
- [x] No changes to ORM model (already exists)
- [x] No router endpoints added (deferred to Story 2.3/2.4)
- [x] Project context updated with learnings
- [x] Sprint status updated to `review`

## Dev Agent Record

### Implementation Plan

Story 2.1 implemented following TDD (red-green-refactor) discipline:
1. **Task 1 (Schemas)**: Created Pydantic schemas excluding embedding by default
2. **Task 2 (Repository)**: Implemented async repository layer with AD-1 single-owner enforcement
3. **Task 3 (Service)**: Implemented service layer with ORM → Pydantic conversion
4. **Task 4 (Tests)**: Written during Tasks 1-3 per TDD

### Completion Notes

**Implemented (2026-07-10):**
- ✅ 4 Pydantic schemas: `ContentResponse` (no embedding), `ContentWithEmbedding` (with embedding), `EmbeddingInput`, `EmbeddingOutput`
- ✅ Repository layer: `get_content_by_id`, `list_content_by_skill`, `create_content` - async SQLAlchemy 2.0 patterns
- ✅ Service layer: `get_content`, `list_content_for_skill` - ORM → Pydantic conversion via `.model_validate()`
- ✅ 16 tests total: 6 schema tests, 5 repository tests, 5 service tests - all passing

**Key Implementation Decisions:**
1. **Pydantic Field Alias**: Used `Field(alias="content_metadata")` to map ORM's `content_metadata` field to Pydantic's `metadata` field, resolving SQLAlchemy's reserved `.metadata` attribute conflict
2. **Test Fixture Fix**: Updated conftest.py with correct database credentials (port 5433, password `sails123`) and async pytest configuration
3. **Unique Skill Names**: Tests use `uuid.uuid4().hex[:8]` to avoid unique constraint violations from parallel test execution

**Files Modified:**
- `backend/app/content/schemas.py` (NEW: 44 lines)
- `backend/app/content/repository.py` (NEW: 58 lines)
- `backend/app/content/service.py` (NEW: 40 lines)
- `backend/tests/test_content_schemas.py` (NEW: 125 lines)
- `backend/tests/test_content_repository.py` (NEW: 177 lines)
- `backend/tests/test_content_service.py` (NEW: 174 lines)
- `backend/tests/conftest.py` (MODIFIED: fixed DB credentials, async fixture scope)
- `backend/pytest.ini` (MODIFIED: added asyncio_mode configuration)

**Test Results:**
```
tests/test_content_repository.py::test_get_content_by_id_returns_orm_instance PASSED
tests/test_content_repository.py::test_get_content_by_id_returns_none_for_nonexistent PASSED
tests/test_content_repository.py::test_list_content_by_skill_returns_list_of_orm PASSED
tests/test_content_repository.py::test_list_content_by_skill_returns_empty_for_skill_with_no_content PASSED
tests/test_content_repository.py::test_create_content_persists_and_returns_orm PASSED
tests/test_content_schemas.py::test_content_response_excludes_embedding PASSED
tests/test_content_schemas.py::test_content_with_embedding_includes_embedding PASSED
tests/test_content_schemas.py::test_embedding_input_schema PASSED
tests/test_content_schemas.py::test_embedding_output_schema PASSED
tests/test_content_schemas.py::test_content_response_type_field_validation PASSED
tests/test_content_schemas.py::test_content_response_source_field_validation PASSED
tests/test_content_service.py::test_get_content_returns_pydantic_response PASSED
tests/test_content_service.py::test_get_content_returns_none_for_nonexistent PASSED
tests/test_content_service.py::test_list_content_for_skill_returns_list_of_pydantic PASSED
tests/test_content_service.py::test_list_content_for_skill_returns_empty_list PASSED
tests/test_content_service.py::test_service_orm_to_pydantic_field_mapping PASSED

16 passed in 37.22s
```

All acceptance criteria satisfied. Story ready for review.

## File List

**New Files:**
- `backend/app/content/schemas.py`
- `backend/app/content/repository.py`
- `backend/app/content/service.py`
- `backend/tests/test_content_schemas.py`
- `backend/tests/test_content_repository.py`
- `backend/tests/test_content_service.py`

**Modified Files:**
- `backend/tests/conftest.py` (fixed database credentials, async fixture configuration)
- `backend/pytest.ini` (added asyncio_mode configuration)

**Unchanged (as expected):**
- `backend/app/assignments/models.py` (ContentCatalog ORM already exists)
- `backend/app/content/router.py` (no HTTP endpoints in this story)

## Change Log

- 2026-07-10: Story 2.1 implemented - Pydantic schemas, repository layer, service layer, 16 tests all passing
- 2026-07-10: `bmad-code-review` (3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor) run against the merge-commit diff (`1ecf196..0134487`, PR #32). 1 decision-needed (resolved), 4 patches applied, 3 deferred (`deferred-work.md`), ~11 dismissed as noise or explicitly spec-sanctioned.
  - **Critical fix**: `conftest.py`'s `test_engine` fixture no longer runs `Base.metadata.create_all()`/`drop_all()` against the real shared `DATABASE_URL` — this had been silently wiping the entire dev database after every test since this story's scope change from session- to function-scoped, already independently confirmed live and blocked-on by Stories 2.2/2.4/3.3. Test isolation now relies entirely on `db_session`'s existing rollback; `test_content_repository.py`/`test_content_service.py` switched from `.commit()` to `.flush()` accordingly.
  - **Also fixed**: `ContentResponse.metadata` now has `default=None` (was silently required despite its `Optional` type — verified empirically against pydantic 2.13); the two enum-validation tests now assert `pydantic.ValidationError` instead of bare `Exception`; a dead `datetime, timezone` import removed from `test_content_repository.py`; the story's own Task 4 checklist corrected (tests don't actually use Story 1.7's seed data, contrary to the checked-off claim).
  - **Verified**: full content-module suite (16/16) re-passing in 1.18s (down from 37.22s, confirming the DB-wipe fix), seed data (5 employees/5 skills) and all 7 tables intact after the run, full backend suite 177/179 passing — the 2 failures (`test_skill_progress.py`) are the pre-existing, already-documented cross-test-file `engine`-pool corruption bug (both pass 100% in isolation), unrelated to this review's changes.
  - Status → `done`.
