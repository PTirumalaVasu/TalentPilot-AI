---
baseline_commit: 5c7ce2fd
---

# Story 10.2: Employee Roster Gains First/Last Name and Expanded Grid Columns

Status: done

## Story

As an **HR Admin**,
I want the roster to capture First and Last Name separately and show Project, Location, Technologies, and Days in Talent Pool instead of Department,
So that I can scan the roster with the fields I actually need instead of a single combined name (FR-34).

## Acceptance Criteria

1. **Given** the `employees` table (currently a single `name` column)
   **When** this story's migration runs
   **Then** it adds `first_name`/`last_name` columns (both `NOT NULL` after backfill) and backfills existing rows by splitting `name` on the **last whitespace-separated token** (that token → `last_name`, everything before it → `first_name`); a name with no whitespace falls back to `first_name = name`, `last_name = "Employee"` (defensive only — no current seeded/real row hits this case)

2. **Given** `CreateEmployeeModal.tsx`/`EditEmployeeModal.tsx` and their backend schemas (`employees/schemas.py`)
   **When** an HR Admin creates or edits an Employee
   **Then** First Name and Last Name are two required fields (same requiredness tier as the current combined Name field, per FR-24) — the combined `name` field is **removed from the request body** (`CreateEmployeeRequest`/`UpdateEmployeeRequest`), and the roster's displayed **Name column** shows **"{Last Name}, {First Name}"**

3. **Given** `EmployeesPage.tsx`'s grid (Story 7.3's existing Table view)
   **When** this story ships
   **Then** it adds four columns — **Project**, **Location**, **Technologies**, **Days in Talent Pool** — sourced from the existing `project`/`location`/`technologies` fields and a newly-computed `days_in_talent_pool = (now() − employees.created_at).days`, computed on read in `employees/service.py`, not stored. **Department is removed as a grid column** in the same change — it remains a stored field and an active toolbar filter option (the existing Department filter dropdown is unaffected), just no longer displayed as its own column.

4. **Given** a roster row's Days in Talent Pool exceeds 90
   **When** the grid renders that row
   **Then** it displays a red visual flag paired with text/icon (never color-only, NFR-A2) — the fixed 90-day threshold is a single named constant (`TALENT_POOL_FLAG_DAYS`), not inlined (FR-35)

5. **And** existing FR-25 search/filter/pagination behavior is unaffected by the new columns — Project, Location, and Technologies join the existing filterable-field set on the same "blank excludes from filter, never makes the row unfindable" rule; the Department filter itself is untouched even though its column is removed from the grid

6. **Given** the acting HR Admin's own Employee record in the roster (Story 10.1's seeded identity)
   **When** the roster is viewed with no search/filter active, vs. with any search term or Department/Position filter active
   **Then** the row appears in the default, unfiltered view like any other record, but drops out of the result set the moment any filter criterion is active — Days in Talent Pool renders blank ("—"), never a guessed or flagged value; Edit and Regenerate Password stay available on this row, but Archive/Delete is replaced with a "(you)" label

## Tasks / Subtasks

- [x] Task 1: Backend — migration + model (AC: 1)
  - [x] New Alembic migration `015_split_employee_name_into_first_last.py` (`down_revision = '014'`): add `employees.first_name`/`last_name` (`String(255)`, nullable=True initially), backfill every existing row in Python (rsplit on the **last space**: `first, last = name.rsplit(' ', 1)` when a space exists, else `first, last = name, "Employee"`), then `alter_column` both to `nullable=False`. Symmetric `downgrade()` drops both columns.
  - [x] `employees/models.py::Employee`: add `first_name = Column(String(255), nullable=False)`, `last_name = Column(String(255), nullable=False)`. **Keep the existing `name` column as-is** (see Dev Notes — deliberately not dropped).
  - [x] `core/seeds.py::seed_employees`: add matching `first_name`/`last_name` values for all 5 seeded rows (see Dev Notes table), keeping `name` set to the same full string as today so a fresh-DB seed and the migration's backfill of a pre-existing DB always agree.

- [x] Task 2: Backend — schemas + service (AC: 1, 2, 3, 6)
  - [x] `employees/schemas.py::CreateEmployeeRequest`: replace `name: str` with `first_name: str = Field(min_length=1, max_length=255)` and `last_name: str = Field(min_length=1, max_length=255)`; update `@field_validator` to cover `("employee_code", "first_name", "last_name")`.
  - [x] `employees/schemas.py::UpdateEmployeeRequest`: same replacement; `@field_validator` covers `("first_name", "last_name")`.
  - [x] `employees/schemas.py::EmployeeResponse`: add `first_name: str`, `last_name: str`, `days_in_talent_pool: int = 0` (computed post-hoc, same pattern as `has_assignment_history` — never populated by a bare `model_validate`).
  - [x] `employees/service.py`: replace the four `_with_assignment_history(EmployeeResponse.model_validate(employee), has_history)` call sites (in `list_employees_service`, `create_employee_service`, `update_employee_service`, `regenerate_password_service`) with a single new helper `_build_employee_response(employee, has_history) -> EmployeeResponse` that sets both `has_assignment_history` and `days_in_talent_pool` (`(datetime.now(timezone.utc) - employee.created_at).days`) in one place.
  - [x] `create_employee_service`/`update_employee_service`: build `employee_data["name"] = f"{request.first_name} {request.last_name}"` alongside `first_name`/`last_name` in the dict passed to the repository — `name` stays a real, always-in-sync column (see Dev Notes).

- [x] Task 3: Frontend — API types (AC: 2, 3)
  - [x] `employeesApi.ts::EmployeeResponse`: add `first_name: string`, `last_name: string`, `days_in_talent_pool: number` (keep `name: string` — still returned, still auto-derived).
  - [x] `employeesApi.ts::CreateEmployeeRequest`/`UpdateEmployeeRequest`: replace `name: string` with `first_name: string; last_name: string;`.

- [x] Task 4: Frontend — Create/Edit modals (AC: 2)
  - [x] `CreateEmployeeModal.tsx`: replace the single "Name *" input with "First Name *"/"Last Name *" inputs; update `EMPTY_FIELDS`, `updateField`'s key type, `handleCreate`'s payload (`first_name`/`last_name` trimmed, both required for the submit-disabled check).
  - [x] `EditEmployeeModal.tsx`: same replacement — populate from `employee.first_name`/`employee.last_name`, update `EMPTY_FIELDS`, `updateField`, `handleSave`'s payload and disabled check.
  - [x] Leave `DeleteArchiveEmployeeModal.tsx` and `RegeneratePasswordModal.tsx` untouched — both only ever read `.name` off an already-fetched `EmployeeResponse`, which keeps working unchanged (see Dev Notes scope note).

- [x] Task 5: Frontend — grid columns + Days in Talent Pool + self-row handling (AC: 3, 4, 5, 6)
  - [x] `EmployeesPage.tsx`: add a local `displayName(e)` helper (`` `${e.last_name}, ${e.first_name}` ``) used only for the grid/card Name cell — every other existing use of `.name` in this file (aria-labels, etc.) stays as-is.
  - [x] Table `<thead>`: remove the `Department` `<th>`; add `Project`, `Location`, `Technologies`, `Days in Talent Pool` `<th>`s (ordered: ID, Name, Position, Project, Location, Technologies, Days in Talent Pool, Email, Status, Actions).
  - [x] Table `<tbody>`: remove the Department `<td>`; add Project/Location/Technologies `<td>`s (`employee.<field> ?? '—'`, matching the existing Position/Department blank-dash convention) and a Days-in-Talent-Pool cell (see next bullet).
  - [x] Add `const TALENT_POOL_FLAG_DAYS = 90;` (module-level constant, referenced — never inlined) and a small render helper that: renders `—` when the row is the acting HR Admin's own row; renders `⚠ {n}d` in red with a `title="Over 90 days in the Talent Pool"` when `days_in_talent_pool > TALENT_POOL_FLAG_DAYS`; otherwise renders `{n}d` in the existing muted-gray style. Reuse the same helper (with a fuller `"{n} days in Talent Pool"` text) in the Card view.
  - [x] Card view: replace the `position · department` sub-line with `position · project` (`?? '—'`/`'No project'` fallback, matching existing convention), add the Days-in-Talent-Pool line.
  - [x] Determine `isSelf` per row via `useAuth()` (`auth.status === 'authenticated' && employee.id === auth.userId`) — pass to `RowActions` and to the Days-in-Talent-Pool renderer.
  - [x] `RowActions`: add an `isSelf: boolean` prop. When `true`, render a `(you)` label (plain text, `data-testid` follows this file's existing kebab pattern) instead of the Delete/Archive button; Edit and Regenerate Password buttons render unchanged regardless of `isSelf`.
  - [x] `filtered` `useMemo`: when `search.trim()`, `department`, or `position` is truthy (any filter criterion active), exclude the row where `employee.id === currentUserId` — the self row still passes through untouched when no filter is active. `showArchived` is not a filter criterion for this rule (the self row is never archived).

- [x] Task 6: Backend tests — `test_employees_router.py` (57 occurrences of the removed `name` field)
  - [x] Add a small test-local helper, e.g. `_name_fields(full_name: str) -> dict` mirroring the migration's exact split strategy (`rsplit(' ', 1)`, single-word fallback to `last_name="Employee"`), and replace every inline `"name": "<value>"` payload key with `**_name_fields("<value>")` (or direct `"first_name"/"last_name"` keys where a single fixed pair reads more clearly, e.g. `_update_payload`'s literal). Every existing `assert body["name"] == "<value>"` / `entry["name"] == "<value>"` assertion is left as-is and keeps passing unchanged, because every existing literal is exactly two space-separated words and the server re-derives `name = f"{first_name} {last_name}"`.
  - [x] `test_create_employee_rejects_blank_name`: rename to `test_create_employee_rejects_blank_first_name`, payload becomes `{"employee_code": ..., "first_name": "   ", "last_name": "Blank", "email": ...}`. Add a sibling `test_create_employee_rejects_blank_last_name` (same shape, blank `last_name`) — both fields now carry the same validator, so both deserve direct coverage.
  - [x] `test_create_employee_rejects_missing_required_field`: payload becomes `{"first_name": "Missing Code And Email"}` (still missing `employee_code`/`last_name`/`email` → still 422).
  - [x] Add one new test asserting a create/list response includes `first_name`, `last_name`, and `days_in_talent_pool` (a freshly-created employee's `days_in_talent_pool` is `0`).
  - [x] **[Found during implementation, not in original scope]** Four other backend test files directly construct an `Employee(...)` ORM row or POST a `"name"` literal to `/api/admin/employees` and broke against the new `NOT NULL first_name/last_name` columns / removed `name` request field: `test_dashboard_router.py` (2 call sites), `test_db.py` (2 direct `Employee(...)` constructions), `test_admin_api_keys_router.py` (1, via its `_create_second_hr_admin` helper), `test_override_endpoint.py` (1 direct `Employee(...)`). All fixed with the same last-whitespace-token split. `test_provenance_detail.py`'s three `Employee(...)` constructions are pure in-memory objects (never `session.add`-ed) so the DB constraint never applies — left untouched.
  - [x] Full regression: `pytest` — 721 passed, 2 skipped, 0 failed (full suite, not just this file).

- [x] Task 7: Frontend tests
  - [x] `EmployeesPage.test.tsx`: added `first_name`/`last_name`/`days_in_talent_pool` to the `makeEmployee()` fixture (auto-derived from a `name` override via the same split strategy, so existing call sites needed no changes); added a `displayName()` test helper and rewired every grid-text assertion to it; updated the min-width class assertion (`min-w-[720px]` → `min-w-[1080px]`); updated the create-flow test to the new `create-emp-first-name`/`create-emp-last-name` fields; added 4 new tests for the new columns, the 90-day flag, and AC6's self-row blank/`(you)`/filter-drop-out behavior.
  - [x] `EditEmployeeModal.test.tsx`: updated the mock fixture and every field-interaction assertion from `edit-employee-name-input` to `edit-employee-first-name-input`/`edit-employee-last-name-input`.
  - [x] No `CreateEmployeeModal.test.tsx` exists — that component is only exercised via `EmployeesPage.test.tsx`, already covered above.
  - [x] Full regression: `npm run test` — 428 passed, 0 failed (41 files, up from 424/41 — net +4 for the new EmployeesPage cases); `tsc --noEmit` unchanged at the documented 31 pre-existing errors (none in files touched by this story).

### Review Findings

- [x] [Review][Decision] AC5's "filterable-field set" claim for Project/Location/Technologies isn't implemented — AC5 says these three new columns "join the existing filterable-field set," but `EmployeesPage.tsx`'s `filtered` `useMemo` only checks `search` against `e.name` plus the pre-existing Department/Position dropdowns; no search-matching or new filter dropdown was added for Project, Location, or Technologies. **Resolved (user decision):** extend the existing free-text search box to also match `project`/`location`/`technologies` (not just `name`) — the smallest interpretation of "join the filterable set," converted to a patch.

- [x] [Review][Patch] Derived `Employee.name` can exceed the 255-char DB column — `first_name`/`last_name` are each validated up to `max_length=255` independently, but `f"{first_name} {last_name}"` is written into `employees.name`, itself `String(255)`. Two near-max-length names produce a ~511-char value, failing at INSERT with an unhandled `DataError` (not `IntegrityError`, so the existing except-block doesn't catch it) instead of a clean 422 — the exact failure mode `CreateEmployeeRequest`'s own code comment says `max_length` values exist to prevent [backend/app/employees/service.py:178,271] — **Fixed:** added a shared `_reject_combined_name_too_long` helper and a `model_validator(mode="after")` on both `CreateEmployeeRequest` and `UpdateEmployeeRequest` rejecting `len(first_name) + 1 + len(last_name) > 255` with a clean 422. New tests: `test_create_employee_rejects_combined_name_over_255_chars`, `test_create_employee_allows_combined_name_at_exactly_255_chars` (boundary), `test_update_employee_rejects_combined_name_over_255_chars`.

- [x] [Review][Patch] Unused `employees_table` variable in the migration — built via `sa.table(...)` but every actual read/write goes through raw `sa.text(...)` strings instead [backend/alembic/versions/015_split_employee_name_into_first_last.py:36] — **Fixed:** removed the dead variable.

- [x] [Review][Patch] Two stacked `# last_updated:` comment lines in sprint-status.yaml — a new line was added above the existing one instead of replacing it (verified: this header field held exactly one line before this story; not an established append-only convention like the separate per-story narrative `last_updated:` fields elsewhere in the file) [_bmad-output/implementation-artifacts/sprint-status.yaml:2-3] — **Fixed:** replaced the stale line instead of stacking a new one above it.

- [x] [Review][Patch] Missing type hint on the `employee` parameter of `_build_employee_response` — the helper it replaced (`_with_assignment_history`) was fully typed [backend/app/employees/service.py:59] — **Fixed:** imported `Employee` and typed the parameter.

- [x] [Review][Patch] No test asserts the exact 90-day boundary — `flagged = days > TALENT_POOL_FLAG_DAYS` means exactly 90 days should NOT flag, but only 10 (unflagged) and 91 (flagged) are tested, leaving an off-by-one free to slip in unnoticed [frontend/src/tests/EmployeesPage.test.tsx] — **Fixed:** added `test('Story 10.2 (FR-35): does not flag Days in Talent Pool at exactly the 90-day threshold')`.

- [x] [Review][Patch] No lower-bound guard on `days_in_talent_pool` against clock skew — `(datetime.now(timezone.utc) - employee.created_at).days` renders straight to the UI; under any DB/app clock skew this could go negative and display "⚠ -3d" with no defensive handling [backend/app/employees/service.py:68] — **Fixed:** clamped with `max(0, ...)`.

- [x] [Review][Patch] Migration's `rsplit(' ', 1)` doesn't strip the result — verified in Python (`"John  Smith".rsplit(' ', 1)` → `['John ', 'Smith']`): a legacy name with an internal double space persists a trailing space in `first_name`. Real-world impact is currently zero (none of the 8 rows in the seeded/test data have double spaces), but the fix is a one-line `.strip()` [backend/alembic/versions/015_split_employee_name_into_first_last.py:72] — **Fixed:** both halves of the split are now `.strip()`-ed; re-verified in Python directly.

- [x] [Review][Patch] Stale comment still references the renamed `_with_assignment_history` helper (renamed to `_build_employee_response` by this story's Task 2) [backend/app/employees/schemas.py:116] — **Fixed:** comment updated to the current helper name.

- [x] [Review][Patch] `test_dashboard_router.py`'s two name-split literals don't follow the true "last whitespace token" strategy this story's Task 6 completion note claims was applied uniformly — `"Story 9.1 Test Employee"` was split as `first_name="Story 9.1"`/`last_name="Test Employee"` rather than the true-last-token `first_name="Story 9.1 Test"`/`last_name="Employee"` (same pattern at the second call site). Functionally harmless (both reconstruct to the original literal), but makes the Dev Agent Record's blanket claim inaccurate [backend/tests/test_dashboard_router.py:355-356,365-366] — **Fixed:** both literals realigned to a true `rsplit(' ', 1)` split.

- [x] [Review][Patch] (from the resolved AC5 decision above) Search box didn't match Project/Location/Technologies — **Fixed:** `filtered`'s search-match condition in `EmployeesPage.tsx` now also checks `project`/`location`/`technologies` (blank still just excludes that field from matching, per the existing FR-25 rule); placeholder text updated to reflect the broader scope. New test: `test('Story 10.2 AC5: the search box also matches Project, Location, and Technologies')`.

- [x] [Review][Defer] Migration's single-token fallback (`last_name="Employee"`) silently fabricates data with no logging/audit trail of which rows were auto-guessed — deferred, accepted defensive-only heuristic per AC1's own documented tradeoff; no current row hits this path except a disposable test fixture — deferred, pre-existing design tradeoff accepted by the spec, not a regression this story introduced

- [x] [Review][Defer] No standalone modal-level test for partial-blank First/Last Name states (e.g. First filled, Last blank) keeping submit disabled — deferred, the actual disabled-condition code (`!trimmedFirstName || !trimmedLastName`) was directly read and confirmed correct during implementation; existing coverage exercises the happy path only — deferred, test-depth nice-to-have, not a known defect

## Dev Notes

**Two scope decisions locked in during story creation (user-confirmed, both narrow the blast radius on purpose):**

1. **The `name` column is kept, not dropped**, and stays auto-derived (`f"{first_name} {last_name}"`) by `employees/service.py` on every create/update. `Employee.name` is read directly by several other AD-1-owned modules outside `employees/` — `assignments/service.py` (`employee_name` on Assignment responses), `dashboard/service.py` (`employee_name`), `auth/router.py` (`MeResponse.name`), `content/admin_api_keys_router.py` (`configured_by_name`) — none of which this story's AC names. Keeping `name` real and in sync means **zero changes** are needed in any of those four files or their tests. `DeleteArchiveEmployeeModal.tsx` and `RegeneratePasswordModal.tsx` both only read `.name` off the roster's own `EmployeeResponse` and therefore also need **no changes** — they keep showing the natural "First Last" order, which is fine since the AC's "{Last Name}, {First Name}" requirement is scoped to the grid's Name column (see decision 2).
2. **"{Last Name}, {First Name}" formatting applies only to `EmployeesPage.tsx`'s own grid/card Name cell** — not to every place the app happens to display a person's name. The only literal "employee picker" in the codebase is `AssignmentModal.tsx`'s employee-select dropdown, but that is fed by `assignments/repository.py`'s own independent read of the `employees` table (a different AD-1 owner) and is not named anywhere in this story's AC. It is explicitly out of scope — do not touch `AssignmentModal.tsx`, `assignments/repository.py`, or `assignments/schemas.py`.

**Split strategy for migration + seed data** (last whitespace-separated token → `last_name`):

| Seeded Employee | `first_name` | `last_name` |
| --- | --- | --- |
| Sails Admin | Sails | Admin |
| Casey the Continuer | Casey the | Continuer |
| Morgan the Motivated | Morgan the | Motivated |
| Jordan the Juggernaut | Jordan the | Juggernaut |
| Sam the Stellar | Sam the | Stellar |

**Architecture compliance (`ARCHITECTURE-SPINE.md`):** No AD is violated. `employees/` remains the sole owner of the `employees` table (AD-1) — the migration, model, schema, and service changes are all internal to this module. `days_in_talent_pool` is computed on read in `employees/service.py`, never stored, matching the AC's explicit instruction and the existing `has_assignment_history` computed-field precedent in the same file. No AD-6 (session/role gate) or AD-11 (`ever_assigned` lock) code is touched.

**`days_in_talent_pool` for a brand-new employee** (`create_employee_service`): use the same `_build_employee_response` helper as the other three call sites rather than special-casing a `0` literal — `employee.created_at` is already ~`now()` at that point, so the computed value is `0` in practice, and using one code path avoids a second place that could drift.

**Testing standard:** Backend `pytest` (async mode auto via `pytest.ini`), no DB needed for `test_employees_service.py` (untouched by this story — pure password-generation tests). Frontend `vitest`. This project's convention is a plain async `_login()` helper per test file, not a fixture — already present in `test_employees_router.py`, do not introduce a new one.

### Project Structure Notes

Backend: new migration `backend/alembic/versions/015_split_employee_name_into_first_last.py`; edits to `backend/app/employees/models.py`, `schemas.py`, `service.py`; `backend/app/core/seeds.py`. No router/repository changes needed (both are generic/pass-through). Frontend: edits to `frontend/src/lib/api/employeesApi.ts`, `frontend/src/features/admin/CreateEmployeeModal.tsx`, `EditEmployeeModal.tsx`, `frontend/src/pages/hr/EmployeesPage.tsx`. No new files on the frontend.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 10.2` (lines 2960-2989)] — canonical AC text this story implements.
- [Source: `_bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/05.1-Employees-Tab.html`] — UX mockup reference for column order, the red-flag treatment (`⚠ {n}d` / `⚠ {n} days in Talent Pool`, `title="Over {N} days..."`), and the self-row blank/exclude behavior (`e.isSelf`) — used as a visual reference only; the mockup's extra "Experience" column and single-word split-name fields (`firstName`/`lastName` already separate in mock data) are **not** part of this story's AC and are not reproduced.
- [Source: `_bmad-output/implementation-artifacts/10-1-persona-rename-and-id-only-identity-references.md`] — Story 10.1 (done) established the seeded HR Admin identity ("Sails Admin", `admin@sails.example.com`) this story's self-row logic (AC6) targets.
- [Source: `CLAUDE.md`#Invariants] AD-1 (module table ownership — this story's two scope decisions both exist to avoid crossing it).

## File List

- `backend/alembic/versions/015_split_employee_name_into_first_last.py` (new)
- `backend/app/employees/models.py`
- `backend/app/employees/schemas.py`
- `backend/app/employees/service.py`
- `backend/app/core/seeds.py`
- `backend/tests/test_employees_router.py`
- `backend/tests/test_dashboard_router.py`
- `backend/tests/test_db.py`
- `backend/tests/test_admin_api_keys_router.py`
- `backend/tests/test_override_endpoint.py`
- `frontend/src/lib/api/employeesApi.ts`
- `frontend/src/features/admin/CreateEmployeeModal.tsx`
- `frontend/src/features/admin/EditEmployeeModal.tsx`
- `frontend/src/pages/hr/EmployeesPage.tsx`
- `frontend/src/tests/EmployeesPage.test.tsx`
- `frontend/src/tests/EditEmployeeModal.test.tsx`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/deferred-work.md`

## Dev Agent Record

### Debug Log

- Applied migration 015 against the local dev DB (`alembic upgrade head`) and verified the backfill directly via `psql`: all 5 seeded rows split correctly per the Dev Notes table, plus 3 pre-existing test-fixture rows from earlier story runs — one (`name: "Test"`, no space) correctly hit the single-word fallback (`first_name="Test"`, `last_name="Employee"`).
- First full-suite run surfaced 14 backend failures, all `NotNullViolationError`/422 from other test files' pre-existing `Employee(...)` ORM constructions and `"name"` request payloads that this story's schema/column changes broke — none were anticipated in the original Task 6 scope (which only covered `test_employees_router.py`). Root-caused and fixed each (see Task 6's "Found during implementation" note); full suite is green after the fix.

### Completion Notes

- All 6 ACs implemented and verified: migration + backfill (AC1), split First/Last Name fields replacing the combined `name` request field with "{Last Name}, {First Name}" grid display (AC2), four new grid columns replacing Department (AC3), the 90-day red-flag threshold via a single named constant (AC4), unaffected search/filter/pagination (AC5), and the acting HR Admin's self-row blank/filter-drop-out/`(you)`-label behavior (AC6).
- Two scope-boundary decisions made during story creation (user-confirmed via `AskUserQuestion`) were followed exactly: `Employee.name` was kept as a real, auto-derived column rather than dropped (zero changes to `assignments/`, `dashboard/`, `auth/`, `content/`, `DeleteArchiveEmployeeModal.tsx`, `RegeneratePasswordModal.tsx`), and the "Last, First" display format was confined to `EmployeesPage.tsx`'s own grid/card Name cell (the Assignment picker in `AssignmentModal.tsx` was not touched).
- Backend: 721 passed, 2 skipped, 0 failed (full suite, pre-review). Frontend: 428 passed, 0 failed (41 files); `tsc --noEmit` unchanged at 31 pre-existing errors, none in this story's files.
- **Code review (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor):** 1 decision-needed, 9 patch, 2 defer, 5 dismissed after verification. All 6 ACs independently re-confirmed by the Acceptance Auditor as correctly implemented, and both Dev Notes scope-boundary decisions verified as actually honored in the diff. Decision resolved (user): AC5's "join the filterable-field set" phrase for Project/Location/Technologies meant extending the search box to match them too (not new dropdown filters) — implemented and tested. Patches applied: a combined `first_name`+`last_name` length guard (was previously reachable via a `DataError` → raw 500 instead of a clean 422), removed a dead variable in the migration, fixed a duplicated `sprint-status.yaml` header comment, added a missing type hint, added the 90-day boundary test, clamped `days_in_talent_pool` against clock skew, fixed the migration's double-space/trailing-space edge case, fixed a stale code comment, and corrected two test literals in `test_dashboard_router.py` to genuinely match the claimed split strategy. Deferred (pre-existing/accepted tradeoffs, not regressions): the migration's unlogged single-token fallback, and missing standalone modal-level tests for partial-blank name states (both logged in `deferred-work.md`). Dismissed as noise/false-positive after verification: row-by-row migration backfill (matches migration 011's established precedent), Days-in-Talent-Pool not excluding archived rows (matches AC3's formula verbatim), the name-splitting heuristic's permanent data-mangling (explicitly authorized by AC1), `isSelf` not excluding other HR_ADMIN rows (unreachable — `create_employee_service` hardcodes `role="EMPLOYEE"`, no UI path creates a second HR_ADMIN), and Edge Case Hunter's Department-column/filter-mismatch finding (that's AC3's explicit, intended behavior). Re-verified after patches: 724 passed backend (721 + 3 new), 430 passed frontend (428 + 2 new), `tsc --noEmit` unchanged at 31 pre-existing errors. Status → `done`.

## Change Log

- 2026-09-16: Story created via `bmad-create-story` (Amelia/dev agent), two scope-boundary decisions confirmed with user before drafting ACs/tasks.
- 2026-09-16: Story implemented via `bmad-dev-story` — migration 015, employees schema/service/model changes, Create/Edit modal split fields, EmployeesPage grid/self-row rework, and test updates across 6 backend files + 2 frontend files (4 of the backend files were fixed as fallout not in the original Task 6 scope — see Dev Agent Record). Full regression green on both stacks. Status set to `review`.
- 2026-09-16: Code-reviewed via `bmad-code-review` — 1 decision resolved (AC5 search-box extension), 9 patches applied, 2 deferred, 5 dismissed after verification. Full regression re-verified green on both stacks (724 backend, 430 frontend). Status → `done`.
