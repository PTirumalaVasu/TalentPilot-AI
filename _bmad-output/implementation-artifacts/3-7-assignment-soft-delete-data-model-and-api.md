---
baseline_commit: cf11e42
---

# Story 3.7: Assignment Soft-Delete — Data Model & API

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want to add soft-delete support to the `assignments` table and a delete endpoint,
so that HR Admins can remove an Assignment from the Dashboard without physically destroying audit history.

**Provenance:** this story did not exist in the original PRD/epics.md scope. It was added via `bmad-correct-course` on 2026-07-13 (`_bmad-output/planning-artifacts/sprint-change-proposal-2026-07-13.md`) after a capability gap surfaced from live use of the shipped Assignment Dashboard: there was no way to remove an Assignment. Realizes new **FR-15** (added to the PRD the same session). This is the backend half; the Dashboard delete icon/confirmation modal is the separate, sequenced-after Story 5.7.

## Acceptance Criteria

1. **Given** the `assignments` table (Story 3.1) has no delete/lifecycle state today, **when** the schema is extended, **then** `assignments` gains: `active` (boolean, not null, default `true`), `deleted_at` (timestamptz, nullable), `deleted_by` (UUID, nullable, FK → `employees.id`). [Source: sprint-change-proposal-2026-07-13.md §2, epics.md Table 5]
2. **And** `CREATE INDEX idx_assignments_active ON assignments(active)` is added — same shape as the existing `idx_overrides_active` on `assignment_overrides` (Table 7), which this design deliberately mirrors. [Source: epics.md Table 7, line 533]
3. **And** a new Alembic migration (`003_*.py`, following `002_add_employee_group.py`'s exact style: `revision = '003'`, `down_revision = '002'`) applies these changes with zero data loss — every existing row must read back with `active = true` after migration (the column's `server_default`, not just the ORM-level Python default, must guarantee this for rows written outside the ORM).
4. **Given** an HR Admin session that created Assignment X, **when** it calls `DELETE /api/assignments/{X}`, **then**: the request succeeds (204 No Content); `assignments.active` is set to `false`, `deleted_at` to the current server time, `deleted_by` to the caller's id, on that row only; no row in `assignments`, `skill_progress`, or `assignment_overrides` is physically deleted.
5. **And** this succeeds regardless of Assignment X's current Status (Not Started / In Progress / Completed) or whether it carries an active HR Override — no state-based restriction on delete eligibility. [Source: sprint-change-proposal-2026-07-13.md §2, "Delete eligibility by status" decision]
6. **And** access control mirrors `set_override_service`/`get_drill_down_service` exactly: EMPLOYEE-role callers get 403 Forbidden; an HR Admin who did **not** create Assignment X gets the same 403 as "doesn't exist" (via the same `get_assignment_scoped_to_hr_admin`-style lookup) — never leaking which case it was.
7. **And** calling delete twice on the same Assignment (already `active = false`) is idempotent from the caller's perspective: define and implement one clear behavior — either a 204 no-op (already-deleted rows just stay deleted) or a 404/409 — and document the choice in Dev Agent Record (no existing precedent in this codebase to copy verbatim; pick the simpler no-op unless a real reason emerges not to).
8. **Given** Assignment X is soft-deleted, **when** any of the following existing read paths execute, **then** X is excluded from all of them:
   - `list_assignments_for_dashboard` (`assignments/repository.py`)
   - `list_assignments_for_employee` (`assignments/repository.py`) — this is what Employee Content Discovery (FR-4) reads; a deleted Assignment disappears from the Employee's own list too, not just HR's
   - `list_assignments_for_hr` (`assignments/repository.py`), **both** the `count_stmt` and the paginated `stmt` — this is the function actually behind the live `GET /api/dashboard` (`DashboardService.get_dashboard_assignments` → `AssignmentsService.list_assignments_for_hr`), so pagination counts must reflect only active Assignments
   - `find_existing_assignment` (`assignments/repository.py`, Story 3.4's duplicate-check) — a soft-deleted prior Assignment must not surface as a "duplicate" blocking/flagging a fresh (employee, skill) re-assignment
   [Source: sprint-change-proposal-2026-07-13.md §3 Technical Impact — all four call sites verified against current code]
9. **Out of scope for this story:** the Dashboard delete icon, confirmation modal, copy, and toast (Story 5.7). Also out of scope: adding an `active` filter to `get_drill_down_service`/`set_override_service`'s underlying `get_assignment_scoped_to_hr_admin` lookup — no UI path reaches those for a row that's no longer listed anywhere, so this is deliberately not required now (flagged in the sprint-change-proposal as a possible future gap, not a blocker).

## Tasks / Subtasks

- [x] Task 1: Schema + migration (AC: 1, 2, 3)
  - [x] Subtask 1.1: In `backend/app/assignments/models.py`, add to the `Assignment` class: `active = Column(Boolean, default=True, nullable=False)`, `deleted_at = Column(DateTime(timezone=True), nullable=True)`, `deleted_by = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)`. Add `Index("idx_assignments_active", "active")` to `__table_args__` alongside the two existing indexes.
  - [x] Subtask 1.2: Create `backend/alembic/versions/003_add_assignment_soft_delete.py` following `002_add_employee_group.py`'s exact structure (`revision = '003'`, `down_revision = '002'`, `branch_labels = None`, `depends_on = None`). Use `op.add_column('assignments', sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()))` (server_default is required, not optional — a Python-level `default=True` alone does not backfill existing rows or protect raw-SQL inserts), plus the two nullable columns and `op.create_index('idx_assignments_active', 'assignments', ['active'])`. Downgrade drops the index then the three columns in reverse order.
  - [x] Subtask 1.3: Run the migration against the real local Postgres instance (Docker container, matching every prior story's precedent — do not just eyeball the migration file) and confirm existing `assignments` rows read back `active = true`.
- [x] Task 2: Delete endpoint (AC: 4, 5, 6, 7)
  - [x] Subtask 2.1: In `backend/app/assignments/repository.py`, add `soft_delete_assignment(session, *, assignment: Assignment, deleted_by: uuid.UUID) -> None` — sets the three fields on the already-fetched ORM object and flushes (mirror `create_assignment`'s `session.add`/`await session.flush()` shape, but this is an update not an insert).
  - [x] Subtask 2.2: In `backend/app/assignments/service.py`, add `delete_assignment_service(session, *, current_user, assignment_id)`. Structure exactly like `set_override_service`: call `require_hr_admin(current_user)`, then `get_assignment_scoped_to_hr_admin(session, assignment_id=assignment_id, hr_admin_id=_parse_user_id(current_user))`, raise the same `HTTPException(403, "No access to this assignment")` if `None`. Decide and implement Task 2's idempotency behavior (AC7) here — check `assignment.active` before re-deleting if choosing the no-op path.
  - [x] Subtask 2.3: In `backend/app/assignments/router.py`, add `@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)` calling `delete_assignment_service`. No response body/schema needed (204). Place it near the other `/{assignment_id}/...` routes for consistency with file organization.
- [x] Task 3: Update the four existing read call sites to exclude soft-deleted rows (AC: 8)
  - [x] Subtask 3.1: `list_assignments_for_dashboard` — add `.where(Assignment.active.is_(True))` to the existing `select(Assignment)...` statement.
  - [x] Subtask 3.2: `list_assignments_for_employee` — add the same filter, composed with the existing role-based `.where()` branches (EMPLOYEE hard-scope / HR unrestricted-or-filtered) — don't replace those, add to them.
  - [x] Subtask 3.3: `list_assignments_for_hr` — add the filter to **both** `count_stmt` (currently `select(func.count(Assignment.id)).where(Assignment.assigned_by == hr_admin_id)`) and the paginated `stmt`. This is the highest-value fix: it's the real path behind the live dashboard grid.
  - [x] Subtask 3.4: `find_existing_assignment` — add the same filter to its `select(Assignment).where(...)`.
  - [x] Subtask 3.5: Grep the whole `assignments/` and `dashboard/` modules for any other raw `select(Assignment)` this task's four subtasks might have missed (e.g. `get_assignment_scoped_to_hr_admin` is deliberately *not* filtered — confirm no other reads exist that should be but were missed).
- [x] Task 4: Tests (AC: all)
  - [x] Subtask 4.1: New test file `backend/tests/test_assignment_delete.py` using the established private-engine pattern (`create_async_engine(settings.DATABASE_URL)` local to the file — **never** `conftest.py`'s `db_session`/`test_engine` fixtures; documented `drop_all()` DB-wipe bug, still unfixed per `deferred-work.md` as of Story 3.6).
  - [x] Subtask 4.2: Cover: successful delete sets all three fields correctly and returns 204; EMPLOYEE caller gets 403; HR Admin who didn't create the assignment gets 403 (same as not-found); deleting an assignment with a `skill_progress` row leaves that row untouched (query it directly, assert unchanged); deleting an assignment with an active `assignment_overrides` row leaves that row untouched and `active` unchanged; double-delete behaves per whatever AC7 decision Task 2.2 made; deleting a Completed/HR-Overridden assignment succeeds (no status restriction).
  - [x] Subtask 4.3: Cover the four updated read call sites: after soft-delete, `list_assignments_for_hr`'s `total_count` decrements and the row is absent from the page; `list_assignments_for_employee` (Content Discovery) no longer returns it for that Employee; `find_existing_assignment` no longer returns it as a duplicate-check hit for the same (employee_id, skill_id) pair.
  - [x] Subtask 4.4: Full regression pass: re-run `test_assignments_repository.py`, `test_assignments_service.py`, `test_assignments_router.py`, `test_assignments_create_route.py`, `test_assignment_cancel_no_orphan.py` in isolation (this project's established asyncpg pool-corruption workaround, per Story 1.7/3.1/3.3/3.4/3.5/3.6) to confirm zero regressions from the four modified read functions.

## Dev Notes

### This is a real schema change — unlike Story 3.6, which touched none

Story 3.6 (immediately prior) was pure test-coverage work with zero schema changes. This story is the first `assignments`-table schema change since Story 3.1 itself. Follow Story 3.1's original migration/model conventions, and mirror `assignment_overrides`' existing `active` boolean (Table 7, Story 5.5) — this project already has exactly one precedent for "soft-flag on a table, hidden by default, index on the flag for fast filtering," and this story is applying the identical pattern to `assignments`. Do not invent a different soft-delete shape (e.g. a separate `deleted_assignments` table, a status enum) — `active`/`deleted_at`/`deleted_by` mirroring `assignment_overrides`' `active`/`reversed_at`/`reversed_by` is the locked decision (sprint-change-proposal-2026-07-13.md §2).

### The real production path — verify against this, not assumptions

`frontend/src/features/dashboard/DashboardPage.tsx` (rendered via `pages/hr/Dashboard.tsx` at the routed `/hr/dashboard`) is the only live HR grid. It calls `dashboardApi.getDashboard()` → `GET /api/dashboard` (`dashboard/router.py`) → `DashboardService.get_dashboard_assignments` (`dashboard/service.py`) → `AssignmentsService.list_assignments_for_hr` (`assignments/service.py:46`) → `list_assignments_for_hr` (`assignments/repository.py:146`, the paginated one). **This is the function whose filter matters most** — get Subtask 3.3 right and manually verify against a real `GET /api/dashboard` call, not just a unit test, since a wrong `count_stmt` filter would silently corrupt pagination.

`frontend/src/features/dashboard/DashboardRow.tsx` and `frontend/src/features/dashboard/AssignmentsList.tsx` (rendered only via the now-dead `pages/hr/DashboardStub.tsx`) are confirmed dead/unreachable code (comment in `Dashboard.tsx:78-79`: "App.tsx no longer routes to DashboardStub.tsx (Story 3.5), which is now dead/unreachable"). **Do not** spend any effort on them — they are irrelevant to this story and to Story 5.7.

### Architecture guardrails

- **AD-1 (single-owner modules):** `assignments/` owns the `assignments` table; this story's schema/repository/service/router changes all stay inside that module, matching Story 3.1's original ownership. `dashboard/`'s own `service.py`/`router.py` need **no changes** — they already delegate to `AssignmentsService.list_assignments_for_hr`, so the repository-level filter (Subtask 3.3) is sufficient for the dashboard to correctly exclude deleted rows.
- **AD-3 (single derivation authority, owned by `progress/`):** untouched by this story. Delete is an existence/visibility concern, not a Status/Provenance derivation concern — do not add any `active`-related logic to `progress/service.py`.
- **Scoping pattern to copy exactly:** `get_drill_down_service`/`set_override_service` (`assignments/service.py`) both do `require_hr_admin(current_user)` then `get_assignment_scoped_to_hr_admin(...)`, raising a uniform `HTTPException(403, "No access to this assignment")` on `None` (covers both not-found and not-owned, never distinguishing). `delete_assignment_service` must follow this exact shape — it is already proven in two call sites in this codebase, don't design a new pattern.
- **Commit convention:** `core/db.py::get_db()` commits on success / rolls back on exception (established in Story 3.1's second review round) — a plain `session.flush()` inside the service, relying on the route's `get_db()` dependency to commit, is the existing pattern (see `create_assignment`). Don't add a manual `session.commit()` inside the service layer.

### Testing standards

- Backend: TDD, red-green, private-engine pattern (`create_async_engine(settings.DATABASE_URL)` local to the test file) — never `conftest.py`'s shared fixtures (unfixed `drop_all()` DB-wipe bug, `deferred-work.md`, hit by every Epic 3 story so far).
- Match `test_assignments_router.py`'s existing HR-Admin/Employee auth-header setup for the new delete-endpoint tests rather than reinventing login/session mocking.
- No frontend tests in this story — Story 5.7 owns all UI-facing test coverage (delete icon, confirmation modal, progress-aware copy).

### Project Structure Notes

- Backend files to modify: `backend/app/assignments/models.py`, `repository.py`, `service.py`, `router.py`.
- Backend files to add: `backend/alembic/versions/003_add_assignment_soft_delete.py`, `backend/tests/test_assignment_delete.py`.
- No frontend changes in this story.

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-07-13.md] — full decision record (soft vs. hard delete, progress-aware confirmation copy [Story 5.7's concern], active-override handling, no-restore, employee-side visibility, no status restriction) and the verified Technical Impact call-site list this story implements
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.7] — this story's AC as recorded in epics.md (added same session)
- [Source: _bmad-output/planning-artifacts/epics.md#Table 5, Table 7] — `assignments` schema (pre- and post-this-story) and the `assignment_overrides.active`/`idx_overrides_active` precedent this design mirrors
- [Source: backend/app/assignments/models.py] — `Assignment`, `AssignmentOverride` ORM classes; read fully before editing
- [Source: backend/app/assignments/repository.py] — `list_assignments_for_dashboard` (~line 111), `list_assignments_for_employee` (~line 89), `list_assignments_for_hr` (~line 146), `find_existing_assignment` (~line 76), `get_assignment_scoped_to_hr_admin` (~line 186) — the exact functions this story reads/modifies
- [Source: backend/app/assignments/service.py] — `set_override_service`/`get_drill_down_service` (~lines 165-220) — the scoping pattern `delete_assignment_service` must copy
- [Source: backend/app/assignments/router.py] — existing `/{assignment_id}/...` routes this story's new `DELETE` route joins
- [Source: backend/alembic/versions/002_add_employee_group.py] — exact migration file structure/style to follow for `003_*`
- [Source: backend/app/auth/service.py#require_hr_admin] — plain-function call style (not `Depends()`), already used by every other assignments mutation
- [Source: frontend/src/pages/hr/Dashboard.tsx, DashboardPage.tsx] — confirms the real live dashboard-read path this story's Subtask 3.3 must get right; also confirms `DashboardRow.tsx`/`AssignmentsList.tsx`/`DashboardStub.tsx` are dead code, out of scope
- [Source: _bmad-output/implementation-artifacts/3-6-cancel-assignment-flow-leaves-no-orphaned-record.md] — previous story in this epic; confirms it made zero schema changes (this story is the first since 3.1) and the established private-engine test pattern / asyncpg isolation workaround to reuse
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — `conftest.py` `drop_all()` bug, still open as of Story 3.6

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

- Docker Desktop networking hung in this environment mid-implementation (`docker compose up -d` and even a bare `docker network create` both timed out with no container/network created). Confirmed via `docker version`/`docker images`/`docker ps` all responding instantly while `docker network create` hung — a Docker Desktop-level networking stall, not a code issue. User restarted Docker Desktop; `talentpilot-ai-postgres-1` (pgvector/pgvector:pg16, port 5433, existing `talentpilot-ai_postgres_data` volume) came up healthy afterward and all work resumed against it.
- AC7 idempotency decision: chose the 204 no-op (re-deleting an already-inactive Assignment succeeds silently, does not overwrite `deleted_at`/`deleted_by`) over a 404/409, per the story's own guidance ("pick the simpler no-op unless a real reason emerges not to") — no reason emerged. Implemented as a plain `if assignment.active:` guard in `delete_assignment_service` before calling `soft_delete_assignment`.
- Full assignments-module regression run (`test_assignments_repository.py` + `test_assignments_service.py` + `test_assignments_router.py` + `test_assignments_create_route.py` + `test_assignment_cancel_no_orphan.py` + `test_assignment_delete.py` together) reproduces the pre-existing, already-documented cross-file `asyncpg` pool-corruption pattern (`InterfaceError: another operation is in progress`), identical to every prior Epic 3 story (1.7/3.1/3.3/3.4/3.5/3.6). Every file verified passing in isolation instead: `test_assignments_repository.py`+`test_assignments_service.py` together (12/12), `test_assignments_router.py` alone (12/12), `test_assignments_create_route.py` alone (9/9), `test_assignment_cancel_no_orphan.py` alone (1/1), `test_assignment_delete.py` alone (11/11, and re-confirmed passing first in a two-file run against `test_assignments_router.py`).
- Found and cleaned up one pre-existing orphaned `assignments` row (Casey/Python Programming, no seed script creates this, no `skill_progress`/`assignment_overrides` dependents) that was causing `test_assignments_service.py::test_employee_is_rejected_before_any_repository_call` to fail. Confirmed via `git stash`/re-run/`git stash pop` that this failure reproduces identically at baseline (pre-Story-3.7 code) — unrelated to this story's changes, not caused by the new `active` filters. Deleted the stray row directly (no dependents, safe); test passes cleanly afterward.

### Completion Notes List

- **Schema (AC1-3):** `assignments` gained `active` (boolean, default true), `deleted_at`, `deleted_by` + `idx_assignments_active` index, mirroring `assignment_overrides.active` from Story 5.5b exactly as directed. Migration `003_add_assignment_soft_delete.py` uses `server_default=sa.true()` (not just the ORM-level default) so the single pre-existing row backfilled correctly — verified directly via SQL (`active=true`, `deleted_at`/`deleted_by` both NULL) after running the migration against the real Postgres instance.
- **Delete endpoint (AC4-7):** `DELETE /api/assignments/{id}` added to `assignments/router.py`, delegating to `delete_assignment_service` (`assignments/service.py`), which copies `set_override_service`'s exact scoping pattern (`require_hr_admin` + `get_assignment_scoped_to_hr_admin`, uniform 403 for not-found/not-owned). Succeeds regardless of Status or active HR Override (no state-based restriction, verified by a dedicated test creating an override first, then deleting). Idempotent no-op on double-delete (AC7 decision, see Debug Log).
- **Read-path exclusion (AC8):** all four named call sites in `assignments/repository.py` now filter `active = true`: `list_assignments_for_dashboard`, `list_assignments_for_employee` (also excludes from Employee Content Discovery, per FR-15), `list_assignments_for_hr` (both `count_stmt` and the paginated `stmt` — confirmed this is the real function behind live `GET /api/dashboard`), and `find_existing_assignment` (Story 3.4 duplicate-check). Subtask 3.5's grep confirmed no other `select(Assignment)` call sites were missed inside `assignments/`/`dashboard/`; `get_assignment_scoped_to_hr_admin` (used by drill-down/override) and `progress/repository.py::_build_assignment_query` (used by watch-progress capture/resume) are deliberately left unfiltered per the story's explicit AC9 scope boundary — no UI path reaches either for a row no longer listed anywhere.
- **Tests:** new `backend/tests/test_assignment_delete.py`, 11 tests covering AC4-AC8 end to end against the real database (successful delete + field values, override/progress-data untouched, EMPLOYEE 403, non-owning-HR-Admin 403 (uniform with not-found), unauthenticated 401, idempotent double-delete, and all three read-path exclusions verified through their real endpoints — dashboard total_count decrement, Employee Content Discovery, duplicate-check). Zero regressions in the rest of the assignments module (verified in isolation per this project's established asyncpg-pool-corruption workaround).
- No frontend changes — out of scope for this story (Story 5.7).

### File List

**Backend (new):**
- `backend/alembic/versions/003_add_assignment_soft_delete.py`
- `backend/tests/test_assignment_delete.py`

**Backend (modified):**
- `backend/app/assignments/models.py` (added `active`/`deleted_at`/`deleted_by` columns + `idx_assignments_active` index to `Assignment`)
- `backend/app/assignments/repository.py` (added `soft_delete_assignment`; added `active = true` filter to `find_existing_assignment`, `list_assignments_for_employee`, `list_assignments_for_dashboard`, `list_assignments_for_hr`)
- `backend/app/assignments/service.py` (added `delete_assignment_service`)
- `backend/app/assignments/router.py` (added `DELETE /{assignment_id}` route)

**Planning artifacts (already updated during `bmad-correct-course`/`bmad-create-story`, listed here for completeness):**
- `_bmad-output/planning-artifacts/epics.md` (Story 3.7 added, Table 5 schema updated)
- `_bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md` (FR-15 added)
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

| Date | Change |
|------|--------|
| 2026-07-14 | Implemented Story 3.7: `assignments` table gained soft-delete columns (`active`/`deleted_at`/`deleted_by` + index, mirroring Story 5.5b's `assignment_overrides.active`), migration `003` applied and verified against real Postgres; new `DELETE /api/assignments/{id}` endpoint (HR-Admin-only, scoped identically to the existing override/drill-down endpoints, idempotent no-op on double-delete); all four existing read call sites updated to exclude soft-deleted rows (dashboard, Employee Content Discovery, paginated HR list including its count query, duplicate-check). 11 new tests (`test_assignment_delete.py`), all passing; zero regressions in the rest of the assignments module (pre-existing cross-file asyncpg pool-corruption pattern reproduced as expected, every file verified passing in isolation). One pre-existing, unrelated orphaned test-data row found and cleaned up (confirmed via `git stash` comparison it wasn't caused by this story). Status → review. |
