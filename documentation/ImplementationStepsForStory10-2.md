# Implementation Steps for Story 10-2: Employee Roster Gains First/Last Name and Expanded Grid Columns

**Story Key:** 10-2-employee-grid-columns-first-last-name-and-days-in-talent-pool
**Epic:** 10 (Post-MVP Admin & Roster Refinements) — 2 of 16 stories, epic remains in-progress
**Status:** ✅ DONE (code-reviewed; not yet committed to git)
**Completed Date:** 2026-09-16

---

## Overview

Story 10.2 splits the Employee roster's single combined `name` field into separate First Name/Last Name capture, and replaces the roster grid's Department column with four new columns — Project, Location, Technologies, and a newly-computed Days in Talent Pool (with a fixed 90-day red-flag threshold). The user's request was explicit: "start implementation for both API and UI for the story 10-2-... if required refer the UX design." As with Story 10.1, no story file existed yet — `sprint-status.yaml` listed this story as `backlog`, with an explicit note that Epic 10 stories were approved via the 2026-09-15 Sprint Change Proposal but not yet authored into individual story files. This session ran `bmad-create-story`, then `bmad-dev-story`, then `bmad-code-review`, all in one continuous pass.

Unlike Story 10.1 (a narrow, mechanical rename), this story touches identity display across the app — splitting `name` into `first_name`/`last_name` is the kind of change that naturally wants to ripple into every module that reads `Employee.name` (`assignments/`, `dashboard/`, `auth/`, `content/`) and every UI surface that shows a person's name (the Assignment picker, confirmation modals). Two scope-boundary judgment calls were surfaced to the user via `AskUserQuestion` before any code was written, rather than resolved silently either way:

1. **Whether to drop the `name` column or keep it auto-derived.** `Employee.name` is read directly by four other AD-1-owned modules outside `employees/`, none of which this story's AC names. **User chose to keep `name` real and auto-derived** (`f"{first_name} {last_name}"`, written by `employees/service.py` on every create/update) — this meant zero changes were needed in `assignments/`, `dashboard/`, `auth/`, `content/`, or two of the roster's own modals (`DeleteArchiveEmployeeModal.tsx`, `RegeneratePasswordModal.tsx`), all of which keep reading `.name` unchanged.
2. **Whether the "{Last Name}, {First Name}" display format should reach the Assignment picker.** The only literal "employee picker" in the codebase is `AssignmentModal.tsx`'s employee-select dropdown, fed by `assignments/repository.py`'s own independent read of the `employees` table — a different AD-1 owner, and not named anywhere in this story's AC. **User chose to confine the new display format to `EmployeesPage.tsx`'s own grid/card Name cell only** — `AssignmentModal.tsx`, `assignments/repository.py`, and `assignments/schemas.py` were left untouched.

Both decisions kept the diff contained to the Employees module (17 files, 635 insertions / 213 deletions) instead of spreading into four other AD-1-owned modules — a deliberate minimal-blast-radius choice, not an oversight.

A UX mockup (`_bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/05.1-Employees-Tab.html`) was consulted during story creation for column order and the red-flag visual treatment (`⚠ {n}d`, `title="Over {N} days..."`), but used only as a visual reference — the mockup's extra "Experience" column and its own split-name demo data were deliberately not reproduced, since the canonical `epics.md` AC text (not the mockup) only calls for four new columns.

Implementing the story also broke 14 tests in **four other backend test files** that directly construct `Employee(...)` ORM rows or POST `"name"`-keyed payloads — none of which were in the original Task 6 scope (which only anticipated `test_employees_router.py`). This was discovered only by running the full backend suite, not by static analysis, and all four were root-caused and fixed in the same session.

Code review then found a real, previously-unnoticed data-integrity gap: `first_name`/`last_name` are each independently capped at 255 characters, but the derived `name` column is itself `String(255)` — two near-max-length names could combine past that limit and fail at INSERT with an unhandled `DataError` instead of a clean 422, the exact failure mode the schema file's own pre-existing code comment says `max_length` values exist to prevent. Also found: one genuinely ambiguous spec reading (AC5's "Project, Location, and Technologies join the existing filterable-field set" was implemented as display-only, with no new search/filter wiring) — surfaced to the user as a decision-needed item rather than guessed at.

---

## Agents Invoked

### 1. Blind Hunter (`bmad-review-adversarial-general` skill, background subagent)

**Purpose:** Open-ended adversarial critique of the finished diff — no spec context, no priors.

**When Invoked:** Part of `bmad-code-review`'s 3-parallel-layer step, once the story reached `review` status. Given only the diff (as a file path, read directly by the subagent — the diff was 1964 lines, too large to embed inline in the prompt).

**Key Findings Identified:** The AC5 filterable-field-set gap (the finding that became the decision-needed item); the 255-char combined-name overflow (later corroborated independently by Edge Case Hunter, one of the strongest signals in the review); an unused `employees_table` variable in the migration; row-by-row (not set-based) SQL backfill; Days-in-Talent-Pool not excluding archived employees; two stacked `# last_updated:` comment lines in `sprint-status.yaml`; a missing type hint on `_build_employee_response`'s `employee` parameter; no test for the exact 90-day boundary; the name-splitting heuristic's permanent, undocumented-per-row data loss; `isSelf` logic not excluding a hypothetical second `HR_ADMIN` row; no lower-bound guard against clock-skew-induced negative Days-in-Talent-Pool; thin modal-level test coverage for the new required-field split.

### 2. Edge Case Hunter (`bmad-review-edge-case-hunter` skill, background subagent)

**Purpose:** Method-driven walk of every branching path and boundary condition — orthogonal to Blind Hunter's attitude-driven pass.

**When Invoked:** Same trigger, launched in parallel with Blind Hunter and the Acceptance Auditor. Output as structured JSON (`location`, `trigger_condition`, `guard_snippet`, `potential_consequence`).

**Key Findings Identified:** The same 255-char combined-name overflow, independently derived at both the create and update call sites with concrete guard-snippet suggestions (the base finding this merged into during triage); the same clock-skew negative-days risk, with a `max(0, ...)` guard-snippet; the migration's silent single-token fallback with no logging of which rows were auto-guessed; a precise, verified-in-Python edge case Blind Hunter missed entirely — `rsplit(' ', 1)` on a legacy name with an internal double space leaves a trailing space on `first_name`; one false positive (flagged as `confidence: medium`) claiming the removed Department column was a defect, when it is in fact AC3's explicit, intended behavior — expected, since this layer reviews with no spec context by design.

### 3. Acceptance Auditor (custom prompt, background subagent)

**Purpose:** Cross-check the diff against the story file's own 6 ACs and both Dev Notes scope-boundary decisions — full `review_mode`, spec file read directly.

**When Invoked:** Same trigger, full review mode against the story file as spec.

**Key Findings Identified:** No AC violations — all 6 ACs independently verified line-by-line against the diff and confirmed correctly implemented, and both Dev Notes scope decisions were verified as *actually honored* in the diff (not just claimed): `name` is genuinely kept real and auto-derived with zero changes to the four other modules, and `displayName()` is genuinely confined to `EmployeesPage.tsx` alone. Found two smaller, real documentation-accuracy gaps neither of the other layers caught: a stale comment in `schemas.py` still referencing the pre-rename `_with_assignment_history` helper (renamed to `_build_employee_response` by this same story's Task 2); and two test literals in `test_dashboard_router.py` (added during the "found during implementation" fallout-fixing pass) that didn't actually follow the true last-whitespace-token split strategy the Dev Agent Record claimed was applied uniformly everywhere — functionally harmless, but made the story's own completion claim inaccurate.

---

## Skills Invoked

### 1. `bmad-agent-dev` (Amelia persona activation)

**Purpose:** Activate the Senior Software Engineer persona for test-first implementation.

**When Invoked:** `start implementation for both API and UI for the story 10-2-employee-grid-columns-first-last-name-and-days-in-talent-pool if required refer the UX desing`. The user's initial message already named a clear intent mapping to the `bmad-dev-story` menu item, so the greeting/menu was skipped and dispatch happened directly — but `bmad-dev-story` immediately found no story file existed yet and the sprint-status entry was `backlog`, not `ready-for-dev`, so the user was asked how to proceed (create the story first, implement directly from `epics.md`/PRD, or create-then-stop) before `bmad-create-story` ran.

### 2. `bmad-create-story`

**Purpose:** Produce a comprehensive, implementation-ready story file for 10.2, since none existed yet.

**When Invoked:** Immediately after the user chose "create the story first" in response to the missing-story-file prompt.

**Workflow Steps Executed:**
1. Read Epic 10's Story 10.2 section directly from `epics.md` (lines 2960–2989) — the AC text already fully authored there, including the exact "{Last Name}, {First Name}" format and the FR-35 90-day flag requirement.
2. Read the existing `employees/` module end to end — `models.py`, `schemas.py`, `service.py`, `repository.py`, `router.py` — plus `core/seeds.py`, migration 011 (the precedent for `employee_code`'s row-by-row backfill), and the frontend's `EmployeesPage.tsx`, `CreateEmployeeModal.tsx`, `EditEmployeeModal.tsx`, `DeleteArchiveEmployeeModal.tsx`, `RegeneratePasswordModal.tsx`, and `employeesApi.ts`.
3. Read the UX mockup (`05.1-Employees-Tab.html`) for column order and the red-flag visual convention, explicitly noting which parts of it (the Experience column, the mock data's pre-split name fields) were *not* part of this story's canonical AC and would not be reproduced.
4. Read `assignments/repository.py`/`AssignmentModal.tsx` to establish that the Assignment picker is a separate, independently-owned read of the `employees` table (AD-1) before deciding it was out of scope.
5. Surfaced both scope-boundary judgment calls to the user via `AskUserQuestion` (the `name` column's fate; the display-format's reach) — both resolved with the narrower, minimal-blast-radius option.
6. Wrote 6 ACs and 7 Tasks/Subtasks with exact file-level guidance, a Dev Notes section explicitly recording both scope decisions and their reasoning, a split-strategy table for the 5 seeded employees, and References back to `epics.md`, the mockup, Story 10.1, and `CLAUDE.md`'s AD-1.
7. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `10-2-...` entry updated `backlog` → `ready-for-dev`.

**Output File:** `_bmad-output/implementation-artifacts/10-2-employee-grid-columns-first-last-name-and-days-in-talent-pool.md`
**Sprint Status:** `10-2-...`: `backlog` → `ready-for-dev`

---

### 3. `bmad-dev-story` (implementation, Amelia persona)

**Purpose:** Execute the story's 7 tasks in sequence: migration + model → schemas + service → frontend API types → Create/Edit modals → grid/self-row rework → backend tests → frontend tests.

**When Invoked:** Immediately after the story file was created and marked `ready-for-dev`.

**Workflow Steps Executed:**
1. **Task 1 — migration + model:** new `015_split_employee_name_into_first_last.py` (nullable columns added, Python-loop backfill via last-whitespace-token split, then `NOT NULL` applied); `Employee.first_name`/`last_name` added to `models.py`, `name` deliberately kept; `core/seeds.py`'s 5 seeded employees given matching `first_name`/`last_name` values. Applied live against the local dev DB and verified the backfill directly via `psql` — including a pre-existing test-fixture row with no space in its name (`"Test"`), which correctly hit the single-word fallback.
2. **Task 2 — schemas + service:** `CreateEmployeeRequest`/`UpdateEmployeeRequest` had `name` replaced with required `first_name`/`last_name`; `EmployeeResponse` gained `first_name`, `last_name`, and `days_in_talent_pool`; the four call sites of the old `_with_assignment_history` helper were consolidated into one new `_build_employee_response` helper that also computes the Days-in-Talent-Pool value; `create_employee_service`/`update_employee_service` both build the derived `name` field alongside the split fields.
3. **Task 3 — frontend API types:** `employeesApi.ts`'s `EmployeeResponse`/`CreateEmployeeRequest`/`UpdateEmployeeRequest` updated to match the new backend contract.
4. **Task 4 — Create/Edit modals:** `CreateEmployeeModal.tsx`/`EditEmployeeModal.tsx` both split their single Name input into First Name/Last Name inputs, with the submit-disabled condition requiring both. `DeleteArchiveEmployeeModal.tsx`/`RegeneratePasswordModal.tsx` deliberately left untouched, per the scope-boundary decision.
5. **Task 5 — grid columns + self-row handling:** `EmployeesPage.tsx`'s table/card views swapped Department for Project/Location/Technologies/Days-in-Talent-Pool; added a `displayName()` helper scoped to this file only; added the `TALENT_POOL_FLAG_DAYS = 90` constant and a `DaysInTalentPoolValue` render helper (blank for the acting HR Admin's own row, red `⚠ {n}d` past the threshold, plain `{n}d` otherwise); wired `useAuth()` to detect `isSelf` per row, passed into `RowActions` (which renders a `(you)` label in place of Delete/Archive for the self row) and into the filter logic (`filtered` excludes the self row only once a search term or Department/Position filter is active).
6. **Task 6 — backend tests:** `test_employees_router.py`'s 57 occurrences of the removed `name` field were converted via a new `_name_fields()` test helper mirroring the production split strategy exactly, chosen so every existing `body["name"] == "..."` assertion kept passing unchanged (every existing literal was exactly two words). **Found during implementation, not anticipated in the original task scope:** 4 other backend test files (`test_dashboard_router.py`, `test_db.py`, `test_admin_api_keys_router.py`, `test_override_endpoint.py`) directly construct `Employee(...)` ORM rows or POST `"name"`-keyed payloads and broke against the new `NOT NULL` columns/removed request field — all root-caused and fixed with the same split strategy. (`test_provenance_detail.py`'s own `Employee(...)` constructions were confirmed to be pure in-memory objects never `session.add`-ed, so the DB constraint never applies there — left untouched.)
7. **Task 7 — frontend tests:** `EmployeesPage.test.tsx`'s `makeEmployee()` fixture updated to auto-derive `first_name`/`last_name` from any `name` override (so existing call sites needed no changes), a `displayName()` test helper added and wired into every grid-text assertion, the create-flow test updated to the new field testids, and 4 new tests added for the new columns, the 90-day flag, and the self-row blank/`(you)`/filter-drop-out behavior. `EditEmployeeModal.test.tsx` updated similarly. No `CreateEmployeeModal.test.tsx` exists — coverage for that component comes entirely through `EmployeesPage.test.tsx`.
8. Full regression: backend 721 passed / 2 skipped / 0 failed (after fixing the 14 fallout failures from the 4 other test files); frontend 428 passed / 0 failed across 41 files; `tsc --noEmit` unchanged at 31 pre-existing errors.
9. Story's Dev Agent Record, Completion Notes, Change Log, and File List filled in; Status → `review`.

**Output Files:**
- `backend/alembic/versions/015_split_employee_name_into_first_last.py` (new)
- `backend/app/employees/models.py`, `schemas.py`, `service.py` (modified)
- `backend/app/core/seeds.py` (modified)
- 5 backend test files (modified — see full list in Files Created/Updated below)
- `frontend/src/lib/api/employeesApi.ts`, `frontend/src/features/admin/CreateEmployeeModal.tsx`, `EditEmployeeModal.tsx`, `frontend/src/pages/hr/EmployeesPage.tsx` (modified)
- 2 frontend test files (modified)
- `_bmad-output/implementation-artifacts/10-2-employee-grid-columns-first-last-name-and-days-in-talent-pool.md`

**Sprint Status:** `10-2-...`: `ready-for-dev` → `in-progress` → `review`

---

### 4. `bmad-code-review` (3-layer adversarial review + decision resolution + patch application)

**Purpose:** Independent adversarial verification of the finished implementation, followed by resolving every finding.

**When Invoked:** User said "proceed" at the review checkpoint, confirming the review target (recent conversation — Story 10.2's uncommitted implementation, matching the sole `review`-status entry in `sprint-status.yaml`).

**Workflow Steps Executed:**
- Constructed the diff against uncommitted working-tree changes (`git diff HEAD`, 17 files changed, 635 insertions / 213 deletions — the new migration file included via a temporary `git add -N` so `git diff` would pick it up, reverted immediately after capturing the diff). Confirmed scope via checkpoint (`review_mode = "full"`, spec file = the story file itself).
- Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor in parallel as background subagents, all three given the diff as a file path (too large — 1964 lines — to embed inline) plus repo access to read full file context beyond the diff hunks.
- Normalized and deduplicated 20 raw findings across the three layers down to 17 unique findings, merging 2 pairs that different layers independently converged on (the 255-char combined-name overflow; the clock-skew negative-days risk).
- **Read the actual code at every finding's location before rating severity**, per the workflow's own rule — confirmed the stale comment reference, the unused migration variable, the sprint-status.yaml duplicate line (checking it was the *first* duplication, not an established convention), the missing `isSelf`-role reachability (confirmed `create_employee_service` hardcodes `role="EMPLOYEE"`, so no UI path creates a second `HR_ADMIN`), and reproduced the double-space `rsplit()` bug directly in a Python one-liner before treating it as real.
- Triaged into: **1 decision-needed, 9 patch, 2 defer, 5 dismiss.**
- **Decision-needed item resolved by the user:** whether AC5's "Project, Location, and Technologies join the existing filterable-field set" required new filter/search capability. Presented three options (treat as non-regression language only / extend the search box to also match these fields / add dedicated dropdown filters); **user chose to extend the search box** — implemented as an additional match condition in `EmployeesPage.tsx`'s `filtered` `useMemo` (blank still just excludes that field from matching, per the pre-existing FR-25 rule), with the search placeholder text updated and a new test added.
- **All 9 remaining patches applied** (plus the resolved decision, for 10 total code changes — user chose "apply every patch," no per-finding confirmation):
  1. A combined `first_name`+`last_name` length guard added to both request schemas via a shared `model_validator`, converting an unhandled `DataError`/500 into a clean 422 — with 3 new tests including an exact-255-char boundary case.
  2. The unused `employees_table` migration variable removed.
  3. `sprint-status.yaml`'s duplicated header comment fixed (replaced the stale line instead of stacking a second one above it).
  4. A missing type hint added to `_build_employee_response`'s `employee` parameter.
  5. A new test asserting the exact 90-day boundary does *not* flag.
  6. `days_in_talent_pool` clamped with `max(0, ...)` against clock skew.
  7. The migration's `rsplit(' ', 1)` result now `.strip()`-ed on both halves, fixing the double-internal-space trailing-space bug — re-verified directly in Python.
  8. The stale `_with_assignment_history` comment reference corrected to `_build_employee_response`.
  9. `test_dashboard_router.py`'s two name-split literals realigned to a true last-whitespace-token split, making the Dev Agent Record's "same strategy everywhere" claim actually accurate.
- **Deferred 2 findings** to `deferred-work.md` (logged with a "How to apply" note each): the migration's single-token fallback silently fabricating data with no audit-log trail (accepted, spec-documented defensive-only heuristic per AC1); missing standalone modal-level tests for partial-blank First/Last Name states (the actual disabled-condition code was directly read and confirmed correct — a test-depth gap, not a known defect).
- **Dismissed 5 findings after verification**, each checked rather than waved off: row-by-row SQL backfill (matches migration 011's own established precedent, appropriate for an 8-row pilot table); Days-in-Talent-Pool not excluding archived rows (matches AC3's `(now() − created_at).days` formula verbatim — not a deviation); the name-splitting heuristic's permanent data mangling (explicitly authorized by AC1's own text); `isSelf` not excluding other `HR_ADMIN` rows (confirmed unreachable — no UI path creates a second one); Edge Case Hunter's Department-column/filter-mismatch finding (that's AC3's explicit, intended behavior, an expected false positive from a layer reviewing with no spec context by design).
- Re-ran the full regression suite after all patches — backend **724 passed** (721 baseline + 3 new), 2 skipped, 0 failed; frontend **430 passed** (428 baseline + 2 new), 0 failed; `tsc --noEmit` unchanged at 31 pre-existing errors.
- Story Status → `done`; `sprint-status.yaml` synced (`10-2-...`: `done`).

**Output:** Story file's "### Review Findings" subsection (1 checked-off decision with resolution note, 10 checked-off patches with inline "Fixed:" notes, 2 checked-off deferrals); Change Log entry; 2 new `deferred-work.md` entries.

**Documentation Generated:**
- The story file's Review Findings section, Change Log, Status field, and Dev Agent Record
- Sprint status synced (`10-2-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`)
- Two new entries in `_bmad-output/implementation-artifacts/deferred-work.md`
- This implementation-steps document (`documentation/ImplementationStepsForStory10-2.md`)

---

## Files Created/Updated

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/015_split_employee_name_into_first_last.py` | Adds `employees.first_name`/`last_name` (nullable → backfilled via last-whitespace-token split → `NOT NULL`); symmetric `downgrade()`. Code-review patches: removed an unused table-reflection variable, `.strip()`-ed both halves of the split |

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/employees/models.py` | `first_name`/`last_name` columns added; `name` deliberately kept as a real, auto-derived column |
| `backend/app/employees/schemas.py` | `name` removed from `CreateEmployeeRequest`/`UpdateEmployeeRequest` in favor of required `first_name`/`last_name`; `EmployeeResponse` gained `first_name`, `last_name`, `days_in_talent_pool`. Code-review patches: a combined-length `model_validator` on both request schemas, a stale helper-name comment fixed |
| `backend/app/employees/service.py` | Four call sites of `_with_assignment_history` consolidated into one `_build_employee_response` helper computing both `has_assignment_history` and `days_in_talent_pool`; `create_employee_service`/`update_employee_service` build the derived `name` field. Code-review patches: added a type hint, clamped `days_in_talent_pool` at 0 |
| `backend/app/core/seeds.py` | 5 seeded employees given matching `first_name`/`last_name` values (same split strategy as the migration, so a fresh seed and a migrated pre-existing DB always agree) |
| `backend/tests/test_employees_router.py` | New `_name_fields()` test helper; 57 occurrences of the removed `name` field converted; blank-name test split into blank-first-name/blank-last-name; missing-required-field test updated. Code-review patches: added 3 tests for the new combined-length guard |
| `backend/tests/test_dashboard_router.py` | Found-during-implementation fallout fix: 2 `Employee`-creating call sites updated to the new required fields. Code-review patch: both name-split literals realigned to a true last-whitespace-token split |
| `backend/tests/test_db.py` | Found-during-implementation fallout fix: 2 direct `Employee(...)` ORM constructions given `first_name`/`last_name` |
| `backend/tests/test_admin_api_keys_router.py` | Found-during-implementation fallout fix: `_create_second_hr_admin()` helper's `Employee(...)` construction given a computed `first_name`/`last_name` split |
| `backend/tests/test_override_endpoint.py` | Found-during-implementation fallout fix: 1 direct `Employee(...)` ORM construction given `first_name`/`last_name` |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/api/employeesApi.ts` | `EmployeeResponse` gained `first_name`, `last_name`, `days_in_talent_pool`; `name` replaced with `first_name`/`last_name` in both request types |
| `frontend/src/features/admin/CreateEmployeeModal.tsx` | Single Name input split into First Name/Last Name; payload and disabled-submit condition updated |
| `frontend/src/features/admin/EditEmployeeModal.tsx` | Same split as Create; header/other text left reading `employee.name` unchanged (auto-derived) |
| `frontend/src/pages/hr/EmployeesPage.tsx` | Table/card Department column replaced with Project/Location/Technologies/Days-in-Talent-Pool; `displayName()` helper (scoped to this file); `TALENT_POOL_FLAG_DAYS` constant + flagged-value renderer; `isSelf` detection via `useAuth()` driving the self-row blank-days/`(you)`-label/filter-exclusion behavior. Code-review patch: search box extended to also match Project/Location/Technologies, placeholder text updated |
| `frontend/src/tests/EmployeesPage.test.tsx` | `makeEmployee()` fixture updated to auto-derive split-name fields; `displayName()` test helper added; grid/card text assertions rewired; create-flow test updated to new field testids; min-width class assertion updated (`720px`→`1080px`). New tests: new-columns rendering, 90-day flag, self-row blank/`(you)`/filter-drop-out. Code-review patches: 90-day-boundary test, search-extension test |
| `frontend/src/tests/EditEmployeeModal.test.tsx` | Mock fixture and every field-interaction assertion updated from the single Name input to First Name/Last Name inputs |

### Planning/Tracking — Modified Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `10-2-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`. Code-review patch: fixed a duplicated header comment line |
| `_bmad-output/implementation-artifacts/deferred-work.md` | 2 new entries logged from code review (migration audit-logging gap; modal-level partial-blank test coverage gap) |

### Documentation Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/10-2-employee-grid-columns-first-last-name-and-days-in-talent-pool.md` | Story file — 6 ACs, 7 Tasks, Dev Notes recording both scope decisions and the 5-employee split table, Dev Agent Record, Review Findings section |
| `documentation/ImplementationStepsForStory10-2.md` | This file |

### Not Changed (by design)

- `assignments/service.py`, `dashboard/service.py`, `auth/router.py`, `content/admin_api_keys_router.py` — all read `Employee.name` directly and needed zero change because `name` was deliberately kept real and auto-derived (scope decision 1)
- `frontend/src/features/admin/DeleteArchiveEmployeeModal.tsx`, `RegeneratePasswordModal.tsx` — both only read `.name` off an already-fetched `EmployeeResponse`, unaffected by the split (scope decision 1)
- `frontend/src/features/assignments/AssignmentModal.tsx`, `backend/app/assignments/repository.py`, `assignments/schemas.py` — the Assignment picker's independent read of `employees`, explicitly out of scope for the "{Last Name}, {First Name}" display format (scope decision 2)
- `backend/app/employees/router.py`, `repository.py` — both generic/pass-through, needed no field-specific changes
- `backend/tests/test_employees_service.py` — pure password-generation unit tests, untouched by this story
- `backend/tests/test_provenance_detail.py` — its `Employee(...)` constructions are pure in-memory objects never persisted, so the new `NOT NULL` columns never applied there

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `bmad-create-story`
- Read `epics.md`'s already-authored Story 10.2 AC text and the full existing `employees/` module (backend + frontend) before writing any Dev Notes
- Consulted the UX mockup for column order/red-flag styling, explicitly noting which parts (an extra Experience column, mock-data-only pre-split names) were not part of the canonical AC
- Surfaced two genuine cross-module scope-boundary questions to the user via `AskUserQuestion` before drafting a single task — both resolved toward the narrower, minimal-blast-radius option
- Status → `ready-for-dev`

### Phase 2: Implementation
**Execution:** Amelia persona
- 7 tasks executed in sequence: migration + model → schemas + service → frontend API types → Create/Edit modals → grid/self-row rework → backend tests → frontend tests
- Verified the migration's backfill live against the local dev DB via direct `psql` inspection, including confirming the single-word-name defensive fallback actually fired on a pre-existing test-fixture row
- Found and fixed 14 test failures across 4 backend test files not anticipated in the original task scope — all root-caused via a full-suite run, not static analysis
- Full regression: 721/723 backend (2 skipped), 428/428 frontend, tsc unchanged at 31 pre-existing errors
- Story marked `review`

### Phase 3: Code Review + Decision + Patches
**Skill:** `bmad-code-review`
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor — the auditor given the story file directly as spec) against the uncommitted diff, both subagents given the diff as a file path due to its size (1964 lines)
- 20 raw findings deduplicated to 17 unique findings: 1 decision-needed, 9 patched, 2 deferred, 5 dismissed after direct verification
- The decision-needed finding was a genuinely ambiguous spec-text reading (AC5's "filterable-field set" phrase) the implementation phase had already made a defensible but incomplete call on — resolved by the user choosing to extend search rather than add new dropdown filters
- The most consequential patched finding — the 255-char combined-name overflow — was independently corroborated by two layers using two different methods (adversarial prose and edge-case JSON with a guard-snippet), and fixed with a shared Pydantic validator plus a boundary test
- The Acceptance Auditor caught two documentation-accuracy defects neither of the other layers found: a stale post-rename comment, and two test literals that didn't actually match the split strategy the story's own completion notes claimed
- Full regression re-verified after patches: 724/726 backend (2 skipped, 0 masked failures), 430/430 frontend
- Story marked `done`

---

## Test Coverage

### New/Extended Test Files

- `test_employees_router.py` — 60 total tests (57 updated via the new `_name_fields()` helper + 3 net new from code review: combined-length rejection, exactly-255-char boundary acceptance, update-path length rejection). Also gained direct `first_name`/`last_name`/`days_in_talent_pool` assertions in the full-roster-fields test.
- `test_dashboard_router.py`, `test_db.py`, `test_admin_api_keys_router.py`, `test_override_endpoint.py` — fallout fixes only (no net-new tests), all now passing against the new schema.
- `EmployeesPage.test.tsx` — 30 total tests (24 from implementation, including 4 net-new for the new columns/flag/self-row behavior, + 2 more from code review: the 90-day boundary and the AC5 search extension).
- `EditEmployeeModal.test.tsx` — 7 total tests, all pre-existing, 3 with field-interaction assertions rewritten for the First/Last Name split.

### Regression Verification

- Backend: 707 baseline (pre-story) → 14 failures surfaced on first full run (fallout from 4 other test files, all fixed) → 721 passed / 2 skipped (clean, pre-review) → 724 passed / 2 skipped (post-review, 3 net new tests), 0 failed at every clean checkpoint
- Frontend: 424 baseline (pre-story) → 428 passed / 0 failed (post-implementation, 4 net new) → 430 passed / 0 failed (post-review, 2 more net new), 41 files throughout
- `tsc --noEmit`: 31 pre-existing errors at every checkpoint, none in this story's files
- Migration 015 applied live against the real local dev DB and verified directly via `psql`: all 5 seeded rows split correctly, plus 3 pre-existing test-fixture rows (one correctly hitting the single-word-name fallback)

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AC1: migration + backfill** | `first_name`/`last_name` added nullable, backfilled via last-whitespace-token split (Python loop, `.strip()`-ed after code review), then set `NOT NULL` | `backend/alembic/versions/015_split_employee_name_into_first_last.py` |
| **AC2: split required fields, "Last, First" grid display** | `name` removed from both request schemas in favor of required `first_name`/`last_name`; `EmployeesPage.tsx`'s `displayName()` formats the grid/card Name cell | `backend/app/employees/schemas.py`, `frontend/src/features/admin/{Create,Edit}EmployeeModal.tsx`, `frontend/src/pages/hr/EmployeesPage.tsx` |
| **AC3: expanded grid columns, Department removed** | Table/card views swap Department for Project/Location/Technologies/Days-in-Talent-Pool; Department stays a stored field and toolbar filter | `frontend/src/pages/hr/EmployeesPage.tsx` |
| **AC4: 90-day red flag via a single named constant** | `TALENT_POOL_FLAG_DAYS = 90`, icon+text (never color-only) rendering, boundary-tested at exactly 90 | `frontend/src/pages/hr/EmployeesPage.tsx` |
| **AC5: search/filter/pagination unaffected + code-review-resolved filterable-set extension** | Existing Department/Position filters untouched; search box extended to also match Project/Location/Technologies (user-resolved decision) | `frontend/src/pages/hr/EmployeesPage.tsx` |
| **AC6: acting HR Admin's self-row handling** | Blank Days-in-Talent-Pool, `(you)` label replacing Delete/Archive, drops out of filtered results only once a filter is active — driven by `useAuth()`'s `userId` | `frontend/src/pages/hr/EmployeesPage.tsx` |
| **Scope decision 1: `name` kept real, auto-derived** | `employees/service.py` writes `name = f"{first_name} {last_name}"` on every create/update; 4 other modules + 2 modals need zero changes | `backend/app/employees/{models,service}.py` |
| **Scope decision 2: display format confined to the roster grid** | `displayName()` defined and used only inside `EmployeesPage.tsx`; `AssignmentModal.tsx` untouched | `frontend/src/pages/hr/EmployeesPage.tsx` |
| **255-char combined-name overflow guard (found during code review, patched)** | Shared `model_validator` on both request schemas rejecting `len(first_name) + 1 + len(last_name) > 255` | `backend/app/employees/schemas.py` |

---

## Key Technical Achievements

✅ **Ran the full create → implement → review → decide → patch pipeline in one continuous session**, correctly discovering the missing story file/status before any implementation work began
✅ **Two genuine cross-module scope-boundary questions were surfaced to the user rather than silently resolved either way**, before a single line of the story's ACs/tasks were drafted — both decisions kept the diff to 17 files in one module instead of rippling into 4 other AD-1-owned modules
✅ **Found and fixed 14 fallout test failures across 4 files never in the original task scope**, via actually running the full suite rather than trusting static analysis
✅ **Verified the migration's backfill live against the real local dev DB**, not just read the code — including confirming the single-word-name defensive fallback actually fires correctly on real data
✅ **Code review's two strongest findings were each independently corroborated by two different methods** (adversarial prose + edge-case JSON with a guard-snippet) — the 255-char overflow and the clock-skew negative-days risk, both patched with boundary tests
✅ **A genuinely ambiguous spec-text reading was surfaced as a decision rather than guessed at** — AC5's "join the filterable-field set" phrase, resolved by the user rather than assumed
✅ **The Acceptance Auditor caught two self-inflicted documentation-accuracy defects** neither of the other two layers found — a stale post-rename comment and two test literals that didn't match the strategy the story's own notes claimed
✅ **A false-positive finding from a spec-blind reviewer layer was correctly identified and dismissed with evidence**, not defensively waved away — Edge Case Hunter's Department-column claim was checked directly against AC3's own text before dismissal
✅ **Zero regressions across every regression run in the session's final checkpoints** — 721 → 724 passed backend, 428 → 430 passed frontend, same 31 pre-existing `tsc` errors throughout

---

## Deferred Items (Not Story 10-2 Scope)

Both formally deferred to `deferred-work.md`:

- **Migration's single-token fallback (`last_name="Employee"`) silently fabricates data with no logging/audit trail of which rows were auto-guessed** [`backend/alembic/versions/015_split_employee_name_into_first_last.py`] — accepted, spec-documented defensive-only heuristic (AC1 explicitly authorizes the split strategy "since no existing column boundary exists to split on"); no current row hits this path except a disposable test fixture. Revisit only if this migration/strategy is ever reused against a real pre-existing database with unknown data quality.
- **No standalone modal-level test for partial-blank First/Last Name states** [`frontend/src/features/admin/CreateEmployeeModal.tsx`, `EditEmployeeModal.tsx`] — the actual disabled-condition code was directly read and confirmed correct during implementation; existing coverage exercises the happy path only. Revisit if a dedicated `CreateEmployeeModal.test.tsx` or partial-blank suite is ever added.

---

## Conclusion

Story 10-2 is **✅ DONE** after a full create-then-implement-then-review-decide-and-patch cycle, run start to finish in one session:

- All 6 acceptance criteria satisfied — the migration correctly splits and backfills `first_name`/`last_name`, the roster grid shows the new columns in the specified order with a properly-thresholded red flag, search/filter/pagination behavior is preserved (and extended per the code-review-resolved decision), and the acting HR Admin's own row is correctly handled everywhere the AC specifies — verified by a 724-test backend regression pass and a 430-test frontend regression pass, both clean before and after the code-review patches
- Two deliberate scope-boundary decisions, made explicitly with the user before implementation began, kept the diff contained to a single module (17 files) instead of rippling into 4 other AD-1-owned modules
- Code review surfaced 17 unique findings after deduplicating 20 raw ones: 1 requiring a human decision (resolved — extend search, implemented and tested), 9 patched (a real 255-char data-integrity gap chief among them), 2 deferred as pre-existing/accepted tradeoffs, 5 dismissed after direct verification
- Zero regressions across every regression run in the session's final checkpoints (721 → 724 backend, 428 → 430 frontend)
- **Not yet committed to git** — working tree still uncommitted as of this document, on top of `HEAD` at `5c7ce2fd` ("feat: Story 10.1 - rename seeded HR Admin identity to Sails Admin (FR-34 prereq)")

**Epic 10 status:** in-progress — 2 of 16 stories (10.1, 10.2) done; next in the documented build order per the Sprint Change Proposal is any of 10.4 through 10.9 (10.1/10.10's identity/seed foundation and 10.2/10.3's employee-grid work are the only build-order-sequenced dependencies).
