# Implementation Steps for Story 7-3: HR Admin Views the Employee Roster

**Story Key:** 7-3-hr-admin-views-the-employee-roster
**Epic:** 7 (Employee Roster Management) — **third story**
**Status:** ✅ DONE
**Completed Date:** 2026-09-11

---

## Overview

Story 7.3 builds the first read-only view of the Employee roster (`GET /api/admin/employees`, FR-25) on top of Story 7.1's schema and Story 7.2's already-mounted `employees_router`. No new schema, no new mutation endpoints — a single list route plus a new `EmployeesPage.tsx` with Table/Card views, search, Department/Position filters, a "Show archived" toggle, and 15-per-page pagination.

The central design decision — confirmed by directly inspecting `skills/router.py`/`SkillsPage.tsx` (Story 6.10) and the actual working reference prototype's JS, not assumed — was that search, filtering, and pagination all belong on the frontend over one full-roster fetch, not as backend query parameters. The endpoint takes zero query parameters and returns the entire roster (active and archived alike) in one response; the browser does the rest, exactly like the Skills tab already does.

No story file existed for 7.3 at the start of this session (it was `backlog` in `sprint-status.yaml`), so this session ran the full pipeline in one continuous pass: create the story, implement it end to end (API + UI), live-verify it in a real browser against a rebuilt Docker backend, then run it through a 3-layer adversarial code review and apply every patch the review turned up.

---

## Agents Invoked

### 1. **Blind Hunter (`bmad-review-adversarial-general` skill, via a background subagent)**

**Purpose:** Open-ended adversarial critique of the finished diff — no spec context, no priors.

**When Invoked:** Automatically, as part of the `code-review` workflow's 3-parallel-layer step, once the story reached `review` status.

**Input:** The full uncommitted diff (backend `employees/repository.py`/`service.py`/`router.py`, `test_employees_router.py`, and the new `EmployeesPage.tsx`/`employeesApi.ts`/`EmployeesPage.test.tsx`) plus repo access for surrounding context.

**Key Findings Identified (15 items, unranked):** unbounded `SELECT *` with no `LIMIT`/pagination on the new endpoint; full-PII overfetch per request; a "redundant" `Depends(get_current_user)` (later dismissed — it's required FastAPI DI, not redundant); a test that only checks field *presence*, not values; a pre-existing test-cleanup pattern that leaks rows on exception (deferred — not introduced by this story); an overstated "AC6 covered by tests" claim; a hardcoded "Rita" identity in the header (deferred — copied faithfully from `SkillsPage.tsx` per the story's own instruction to mirror it); no frontend role-gating on `/employees` (deferred — systemic, pre-existing across the whole app); a `page`/`currentPage` state-desync risk in pagination; no search-input debounce; unnormalized Department/Position values at create time (deferred — Story 7.2's scope, already `done`); a shared-toast dismiss-timer non-issue (dismissed — zero observable consequence); self-graded/unverifiable Playwright evidence; a conflated "unbounded fetch" justification; and no read-side length bound on free-text fields.

### 2. **Edge Case Hunter (`bmad-review-edge-case-hunter` skill, via a background subagent)**

**Purpose:** Method-driven walk of every branching path and boundary condition — orthogonal to Blind Hunter's attitude-driven pass.

**When Invoked:** Same trigger, launched in parallel with Blind Hunter and the Acceptance Auditor.

**Key Findings Identified (8 items, JSON-formatted with location/trigger/guard/consequence):** no `LIMIT`/`OFFSET` (duplicate of Blind Hunter's finding — merged in triage); non-locale-aware dropdown sort (cosmetic, matches the reference prototype exactly); Department/Position filter options computed from the *full* roster regardless of the "Show archived" toggle — a real, fixable bug; a stale selected-filter-value risk after a future refetch (deferred — currently unreachable); a Retry-after-failure roster-wipe pattern (deferred — pre-existing, copied from `SkillsPage.tsx`, also currently unreachable here); the shared-toast timer concern (duplicate, dismissed); Prev/Next pagination buttons using stale `page` state instead of the clamped `currentPage` — a real, fixable bug; and unwindowed pagination-button rendering (deferred — fine at pilot scale, matches the prototype).

### 3. **Acceptance Auditor (custom prompt, via a background subagent)**

**Purpose:** Cross-check the diff against the story's own spec — 6 Acceptance Criteria and 7 Scope Notes — and independently re-execute every quantitative claim in the Dev Agent Record rather than taking it on faith.

**When Invoked:** Same trigger, `review_mode = "full"` since the story file was set as `{spec_file}`.

**Verification method:** Actually ran `pytest`, `vitest`, `tsc --noEmit`, and `vite build` in the real repo against the live Postgres container, rather than reading the Dev Agent Record's numbers and trusting them.

**Result:** Every quantitative claim reproduced exactly — backend 662 passed/2 skipped, frontend 354 passed, `tsc` at the same 31 pre-existing errors, `vite build` at 530 modules. **Zero AC or Scope Note violations found.** The only claim it could not independently verify was the ad hoc live-browser Playwright smoke test itself (tooling was installed and uninstalled within the session, per its own documented process) — flagged as an audit caveat, not a contradiction.

**Output:** A clean audit report with a full AC1–AC6 and Scope-Note-1-through-7 cross-check table, each line citing the exact code that satisfies it.

---

## Skills Invoked

### 1. **`bmad-create-story` (story creation)**

**Purpose:** Produce a comprehensive story file for 7.3 from scratch — none existed yet, only the epic's raw AC text.

**When Invoked:** Explicit user instruction: "start development api and ui for the story 7-3-hr-admin-views-the-employee-roster and refer the ux design if required."

**Workflow Steps Executed:**
1. Confirmed via `sprint-status.yaml` that 7.1 and 7.2 were `done` and 7.3 was `backlog` with no story file — the natural next pick.
2. Read Epic 7's Story 7.3 AC text from `epics.md` (6 ACs, including two added by the 2026-09-11 implementation-readiness check for `aria-label`s and horizontal scroll).
3. Read the dedicated UX spec (`_bmad-output/C-UX-Scenarios/05-ritas-roster-management/05.1-employees-roster/05.1-employees-roster.md`) and the working reference prototype (`05.1-Employees-Tab.html`) in full — object IDs, table/card columns, toolbar layout, filter/pagination JS logic (`getFiltered()`/`renderEmployees()`), and accessibility requirements.
4. Read the actual current backend state (`employees/models.py`, `router.py`, `schemas.py`, `service.py`, `repository.py` from Stories 7.1/7.2) and the frontend precedent (`SkillsPage.tsx`, `skillsApi.ts`, `App.tsx`) to confirm exactly what to build on and what pattern to mirror.
5. **Confirmed a design decision by direct evidence, not assumption:** cross-referenced `skills/router.py`'s zero-query-param `GET` route and the prototype's pure-client-side `getFiltered()` to settle that Story 7.3's endpoint should take no query parameters — search/filter/pagination live entirely in the browser.
6. **Flagged a real, unassigned gap rather than silently building around it:** no story owns the Create Employee frontend (Story 7.2 was backend-only); Story 7.3's row/card action icons and "+ New Employee" button would need to render (AC5 requires `aria-label`s) without real behavior — resolved as a documented toast-stub decision, not invented navigation.
7. Wrote 7 Scope Notes covering: read-only/list-only scope, client-side filtering (not query params), HR_ADMIN-only hard gate, leaving `assignments/repository.py::list_employees` untouched, no left-pane nav shell (that's Story 7.7's job), stubbed action icons, and deterministic `ORDER BY employee_code` sorting.
8. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `7-3-...` entry updated from `backlog` to `ready-for-dev`.

**Output File:** `_bmad-output/implementation-artifacts/7-3-hr-admin-views-the-employee-roster.md`
**Sprint Status:** `7-3-...`: `backlog` → `ready-for-dev`

---

### 2. **Direct TDD implementation (Amelia persona, `bmad-dev-story`-equivalent execution)**

**Purpose:** Execute the story's 8 tasks in sequence — backend list endpoint, frontend page, routing, and tests for both.

**When Invoked:** Continuing directly from story creation in the same session (no separate user prompt needed — the original instruction already covered "start development api and ui").

**Workflow Steps Executed:**

1. **Red phase confirmed first:** wrote 5 new backend router tests before touching any implementation code; ran them and confirmed all 5 failed with `405 Method Not Allowed` (no `GET` route existed yet).
2. **Task 1 — Repository:** `list_all_employees(db)` — unfiltered `select(Employee).order_by(Employee.employee_code)`, no `archived_at` filter, mirroring `skills/repository.py::list_all_skills`'s shape but adding deterministic ordering (this one backs a paginated table, not an unordered grid).
3. **Task 2 — Service:** `list_employees_service(db, *, current_user)` — `require_hr_admin(current_user)` gate first, then the repository call, mapped through `EmployeeResponse.model_validate(...)`.
4. **Task 3 — Router:** `GET ""` → `list_employees_route`, `response_model=list[EmployeeResponse]`. No new mount needed (Story 7.2 already mounted `employees_router` at `/api/admin/employees`).
5. **Green phase:** all 5 new backend tests passed on the first implementation attempt.
6. **Task 5 — Frontend API client:** `frontend/src/lib/api/employeesApi.ts` — `EmployeeResponse` TS interface mirroring the backend schema field-for-field, `listEmployees(): Promise<EmployeeResponse[]>`.
7. **Task 6 — Employees page:** `frontend/src/pages/hr/EmployeesPage.tsx` — reused `SkillsPage.tsx`'s exact header/toolbar/fetch-once-then-filter shape (including its `requestIdRef` staleness guard) rather than inventing a new page pattern. Client-side derived list: search (name, case-insensitive substring) AND department AND position AND archived-toggle, all independent `AND` clauses. 15/page pagination; search/filter/archived-toggle reset to page 1, view toggle does not (matching AC1's "shared state" requirement exactly).
8. **Task 7 — Route:** added `/employees` to `App.tsx`, plus — beyond the original task list, discovered while wiring the route — added the "Employees" nav link to `Dashboard.tsx` and `SkillsPage.tsx` so the new page was actually reachable through navigation, not just by typing the URL.
9. **Task 8 — Frontend tests:** 11 new tests in `EmployeesPage.test.tsx` covering loading/error/empty states, search, Department/Position filter composition, archived-employee findability via name search even with blank optional fields, the Show Archived toggle, Table↔Card state preservation, pagination behavior with a 20-employee fixture, and `aria-label` presence on every action button. All 11 passed on the first run.
10. **Full regression:** backend 662 passed/2 skipped/0 failed (657-passed post-Story-7.2 baseline + 5 new); frontend 354 passed/0 failed; `tsc --noEmit` byte-identical to the pre-existing 31-error baseline (verified via `git stash` A/B comparison); `vite build` clean at 530 modules (up from 513).
11. **Live browser verification, not just the test suite.** This required an unplanned detour: the running `talentpilot-api` Docker container has no volume mount, so the new route 404'd against it until `docker compose build backend && docker compose up -d backend` was run. A second surprise: port 5173 was already occupied by the *existing* `talentpilot-ui` Docker container serving a stale pre-story build — `vite dev` silently fell back to port 5174, and the first verification pass was accidentally pointed at the stale container (explaining an initial false failure: no "Employees" nav link, `/employees` 404). Corrected by pointing an ad hoc Playwright script (installed and later uninstalled within the session) at the actual dev-server port and the rebuilt backend: logged in as the real seeded Rita account, confirmed the roster renders the 5 real seeded demo employees, search/filter/view-toggle/archived-toggle all work, action icons carry the right `aria-label`s and show a "not available yet" toast without crashing, and a real EMPLOYEE-role login (Casey) genuinely gets a `403` from the API. All 10 checks passed.
12. Filled in the story file's Dev Agent Record, File List, Completion Checklist, and Change Log; Status → `review`.

**Output File:** `_bmad-output/implementation-artifacts/7-3-hr-admin-views-the-employee-roster.md`
**Sprint Status:** `7-3-...`: `ready-for-dev` → `review`

---

### 3. **`code-review` (3-layer adversarial review + patch application)**

**Purpose:** Independent adversarial verification of the finished implementation, followed by resolving every finding.

**When Invoked:** `/code-review` slash command, no argument — resolved via Tier 2 (recent conversation) and Tier 3 (the unique `review`-status story in `sprint-status.yaml`), both agreeing on the same target.

**Workflow Steps Executed:**

- Constructed the diff from uncommitted changes (`git diff HEAD`, plus `git diff --no-index` for the 4 new files) — 1,157 lines total, well under the chunking threshold.
- Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor in parallel as background subagents (see **Agents Invoked** above); all three completed and reported back independently.
- **Triaged 17 unique findings** (after deduplication) by reading the actual code at each location — not rating from the diff hunk alone — to judge real reachability: `1 decision-needed`, `4 patch`, `10 defer`, `2 dismiss`.
- **Decision-needed, presented to the user:** the unbounded/no-pagination roster fetch, framed as a deliberate Scope-Note-2 trade-off rather than an oversight, with three options (keep as-is / add server-side pagination now / keep-as-is-but-record-the-limitation). **User chose to keep as-is** — matches established precedent, fine at pilot scale.
- **Patches, presented to the user, "apply every patch" chosen:**
  1. Strengthened `test_list_employees_returns_full_roster_with_all_fields` to populate and assert every optional field's actual *value*, not just key presence — a swapped/mismapped column would now fail the test.
  2. Fixed pagination Prev/Next handlers to compute from the clamped `currentPage` instead of the raw `page` state, closing a latent (currently unreachable, but real) stale-state bug.
  3. Fixed Department/Position filter options to derive from the archived-toggle-respecting subset of the roster, not the full unfiltered list — an option that exists only on archived rows no longer silently appears while "Show archived" is off.
  4. Added a dedicated AC6 test asserting the `overflow-x-auto`/`min-w-[720px]` scroll-container classes are present, correcting the Completion Checklist's overstated "all 6 ACs covered by tests" claim into something a test actually backs (with an explicit caveat noted that jsdom can't verify real browser overflow/scroll behavior, only that the mechanism is wired).
- **Dismissed as false positives:** a "redundant" `Depends(get_current_user)` (it's required FastAPI DI to inject the value — router-level `dependencies=[...]` only gates access, doesn't inject); a shared-toast dismiss-timer concern with zero observable consequence (identical repeated message means nothing visually changes either way).
- **10 items deferred** to `deferred-work.md`, each tagged with why: several are pre-existing patterns faithfully copied from `SkillsPage.tsx`/`Dashboard.tsx` per this story's own explicit instruction to mirror that page (hardcoded "Rita" identity, the Retry-wipes-roster pattern, no frontend role-gating); several are currently unreachable given this story's own scope (stale filter option after a refetch that nothing yet triggers); and a few are genuinely out of this story's ownership (unnormalized Department/Position values are Story 7.2's `CreateEmployeeRequest`, already `done`).
- Re-ran the full regression suite after all 4 patches: backend 662 passed/2 skipped/0 failed (unchanged count — one test was strengthened, not added), frontend 355 passed/0 failed (+1 new AC6 test), `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean.

**Output:** Story file gained a "### Review Findings" subsection (1 resolved decision, 4 checked-off patches, 10 checked-off defers with reasons, 2 dismissed noted in prose) and a "### Code Review Patches" completion-notes addendum; `deferred-work.md` gained a new `7-3-hr-admin-views-the-employee-roster` heading with all 10 deferred items in the ledger's established format. Story status → `done`; `sprint-status.yaml` updated to match.

**Documentation Generated:**
- The story file's Review Findings section, Code Review Patches notes, corrected Test Results block, and updated File List
- A new heading in `deferred-work.md` with 10 fully-described, `**How to apply:**`-tagged entries
- Sprint status synced (`7-3-...`: `backlog` → `ready-for-dev` → `review` → `done`)

---

## Files Created/Updated

### Backend — New Files

*(none — this story extended the existing `employees/` module scaffold and test file from Stories 7.1/7.2)*

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/employees/repository.py` | `list_all_employees` added — unfiltered, ordered by `employee_code` |
| `backend/app/employees/service.py` | `list_employees_service` added — HR-Admin-gated |
| `backend/app/employees/router.py` | `GET ""` → `list_employees_route` added |
| `backend/tests/test_employees_router.py` | 5 new tests (full roster/field shape, archived-inclusion, ordering, 403, 401); code review: the full-roster test now asserts actual field values, not just key presence |

### Frontend — New Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/api/employeesApi.ts` | `EmployeeResponse` interface, `listEmployees()` |
| `frontend/src/pages/hr/EmployeesPage.tsx` | The roster page — Table/Card views, search, filters, archived toggle, pagination, action-icon stubs; code review: pagination Prev/Next now use clamped `currentPage`, Department/Position options now respect "Show archived" |
| `frontend/src/tests/EmployeesPage.test.tsx` | 12 tests covering all 6 ACs (11 at implementation + 1 code-review AC6 patch) |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/App.tsx` | `/employees` route added |
| `frontend/src/pages/hr/Dashboard.tsx` | "Employees" nav link added |
| `frontend/src/pages/hr/SkillsPage.tsx` | "Employees" nav link added |

### Not Changed (by design)

- `backend/app/assignments/repository.py::list_employees` — a different, pre-existing endpoint (the Skill Assignment Flow's employee picker, Scope Note 4), left completely untouched
- `backend/app/employees/schemas.py` — `EmployeeResponse` already existed from Story 7.2, reused as-is
- `backend/app/main.py` — `employees_router` already mounted (Story 7.2)

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/7-3-hr-admin-views-the-employee-roster.md` | Story file — 6 ACs, 7 Scope Notes, Dev Notes, Dev Agent Record, Review Findings section |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `7-3-...`: `backlog` → `ready-for-dev` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | New `7-3-hr-admin-views-the-employee-roster` heading, 10 deferred findings |
| `documentation/ImplementationStepsForStory7-3.md` | This file |

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `bmad-create-story`
- Read the dedicated UX spec and working reference prototype in full, not just the epic's AC text
- Confirmed by direct code inspection (not assumption) that search/filter/pagination belong on the frontend, matching the one existing precedent (Story 6.10) exactly
- Flagged the unassigned "Create Employee frontend" gap explicitly rather than silently inventing behavior for it
- Status → `ready-for-dev`

### Phase 2: Implementation
**Execution:** Direct TDD (Amelia persona)
- Red phase confirmed (5 failing tests) before any implementation code was written
- 8 tasks executed in sequence: repository → service → router → API client → page → route/nav → tests
- All 16 new tests (5 backend + 11 frontend) passed on the first run
- Full regression clean; `tsc`/`vite build` unchanged against baseline
- Live-verified in a real browser against a rebuilt Docker backend — required an unplanned image rebuild and a port-mismatch correction along the way
- Story marked `review`

### Phase 3: Code Review + Patches
**Skill:** `code-review`
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor) — the Auditor independently re-ran every test/build command and found zero AC/Scope Note violations
- 17 unique findings triaged: 1 decision-needed (resolved by the user — keep the unbounded fetch), 4 patches (all applied), 10 deferred (logged with reasons), 2 dismissed as false positives
- Full regression re-verified after patches: zero new failures
- Story marked `done`

---

## Test Coverage

### New/Extended Test Files (16 tests at implementation, 17 after the code-review patch)

- `test_employees_router.py` — 5 new: full roster with all field values asserted (strengthened by code review), archived-row inclusion (no `archived_at` filter at the endpoint), deterministic `employee_code` ordering, 403 (EMPLOYEE session), 401 (unauthenticated)
- `EmployeesPage.test.tsx` — 12 new: loading/error+Retry/empty states, name search, Department/Position filter composition, blank-optional-field findability via name search, Show Archived toggle with a visible badge, Table↔Card state preservation, 20-employee pagination fixture with a mid-flow filter reset, every action button's `aria-label`, the "not available yet" toast, and (code-review patch) the AC6 horizontal-scroll class assertion

### Regression Verification

- Backend: 662 passed, 2 skipped, 0 failed — both after initial implementation and, unchanged, after the code-review patches (the value-assertion patch strengthened an existing test rather than adding a new one)
- Frontend: 354 passed after implementation → 355 passed after the code-review patches (+1 new AC6 test)
- `tsc --noEmit`: 31 pre-existing errors, byte-identical before and after this story's entire change set (verified via `git stash` A/B comparison both times)
- `vite build`: clean, 530 modules, both before and after patches
- Live Playwright browser smoke test against a rebuilt Docker backend and the real seeded dev DB: all 10 checks passed, including a genuine `403` for an EMPLOYEE-role session — not just asserted by a mocked test

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **Client-side filtering, not query parameters** | `GET /api/admin/employees` takes zero query params; the frontend fetches once and does search/filter/pagination/archived-toggle entirely in the browser, matching the Story 6.10/`SkillsPage.tsx` precedent | `employees/router.py`, `employees/repository.py`, `EmployeesPage.tsx` |
| **AD-1 — single-owner data module** | All new `employees` table queries live in `employees/repository.py`; `assignments/repository.py::list_employees` (a different, pre-existing endpoint) was left untouched | `employees/repository.py` |
| **AD-6/FR-14 role gate** | `list_employees_service` calls `require_hr_admin(current_user)` before any query, mirroring `content/service.py::list_skills_with_content`'s established service-layer gate pattern exactly | `employees/service.py` |
| **Deterministic pagination ordering** | `list_all_employees` adds `.order_by(Employee.employee_code)` — a deliberate departure from `skills/repository.py::list_all_skills`'s unordered shape, since this list backs a paginated table, not an unordered grid | `employees/repository.py` |
| **Stub, don't invent, unspecified UI behavior** | The "+ New Employee" button and all three row/card action icons render with correct `aria-label`s but show a "not available yet" toast rather than real navigation/modals that no story yet owns | `EmployeesPage.tsx` |

---

## Key Technical Achievements

✅ **Ran the full create → implement → review → patch pipeline in one continuous session**, starting from a story that didn't exist yet and a sprint-status entry still at `backlog`
✅ **Confirmed the client-side-filtering design by direct code inspection, twice** — once during story creation (reading `skills/router.py`/`SkillsPage.tsx` and the prototype's JS) and once more when the Acceptance Auditor independently verified the same conclusion during code review
✅ **All 16 new tests passed on the first run** at implementation — a direct result of thorough story authoring (Scope Notes matching the established `SkillsPage`/`skills/` pattern closely enough that the implementation and the tests agreed from the start)
✅ **Live-verified end-to-end in a real browser, not just the test suite** — and the verification process itself surfaced two real environment gotchas (a Docker image needing a rebuild for code changes to take effect, and a port collision with a stale existing container) that would otherwise have gone unnoticed
✅ **Code review's Acceptance Auditor independently re-executed every quantitative claim** (test counts, `tsc` error count, `vite build` module count) rather than trusting the Dev Agent Record's prose, and found all of them accurate
✅ **Found and fixed a real, if currently low-reachability, pagination logic bug** (Prev/Next buttons using stale `page` state instead of the clamped `currentPage`) before it could surface once the roster naturally grows past 15 employees or a future story wires a post-mutation refetch
✅ **Found and fixed a real filter-options bug** (Department/Position dropdown not respecting the "Show archived" toggle) that will become user-visible the moment Story 7.5 ships employee archiving
✅ **Correctly distinguished a deliberate design trade-off from an oversight** — the unbounded roster fetch was presented to the user as a decision, not silently patched or silently ignored, and resolved as intentional
✅ **Zero regressions across every regression run** — implementation, live verification, and both rounds of code-review patch re-verification

---

## Deferred Items (Not Story 7-3 Scope)

All 10 logged to `deferred-work.md` under a new `7-3-hr-admin-views-the-employee-roster` heading:

1. **Hardcoded "Rita" identity in the header** instead of reading the real authenticated user — pre-existing pattern copied faithfully from `SkillsPage.tsx`/`Dashboard.tsx`, not a new defect.
2. **No frontend role-gating on protected routes** (`RequireAuth` checks authentication only, never role) — systemic across the whole app; the backend's `403` is the real, correctly-enforced security boundary.
3. **A failed refetch (Retry) would wipe an already-successfully-rendered roster entirely** — identical pre-existing pattern from `SkillsPage.tsx`; also currently unreachable here since nothing but the Retry button itself re-triggers `refetch()`.
4. **Selected Department/Position filter value can go stale after a refetch** — currently unreachable given this story's scope; becomes relevant once Stories 7.4-7.6 wire real mutations.
5. **Department/Position values aren't trimmed or case-normalized at create time** — root cause is Story 7.2's `CreateEmployeeRequest`, already `done`, out of this story's scope.
6. **No read-side length bound on free-text profile fields** — low real risk; only the validated Create endpoint writes them today.
7. **Filter dropdown sort uses default JS lexicographic order, not locale-aware** — cosmetic, matches the reference prototype's own identical behavior.
8. **Pagination renders one button per page with no windowing** — fine at pilot scale, matches the reference prototype.
9. **No debounce on the search input** — negligible at current/expected pilot scale.
10. **The Dev Agent Record's live Playwright verification is unretained/unverifiable from the diff alone** — a process note, not a code defect; every other quantitative claim was independently reproduced exactly.

Carried forward from earlier Epic 7 stories, still open, unaffected by this story:
- `auth/repository.py::authenticate()` still does not read `Account` — Story 7.2's newly-created Employees still can't log in with their generated password until a future story wires that path.

---

## Conclusion

Story 7-3 is **✅ DONE** after a full create-then-implement-then-verify-then-review-and-patch cycle, run start to finish in one session:

- All 6 acceptance criteria satisfied, verified by 17 dedicated tests (5 backend + 12 frontend) plus a live Playwright browser smoke test against a rebuilt Docker backend
- Zero AC or Scope Note violations, confirmed independently by an Acceptance Auditor that re-ran every test suite and build command itself
- Clean first-pass implementation — 16 new tests, zero red-phase failures beyond the initial (expected) red confirmation
- Code review found 17 unique issues across 3 parallel layers; 1 decision resolved by the user, 4 real bugs patched (including two genuine, if currently low-reachability, logic bugs), 10 correctly deferred with reasons, 2 correctly dismissed as false positives
- Zero regressions across every regression run in the session
- An unplanned Docker-rebuild-and-port-collision detour during live verification, worked through and documented rather than skipped

**Epic 7 status:** Stories 7.1, 7.2, and 7.3 are all `done`. Story 7.4 (HR Admin Edits an Employee Record) is next in the backlog.
