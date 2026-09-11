---
baseline_commit: 30bd7a78f31161ed06a67201f966405b9f15db95
---

# Story 7.3: HR Admin Views the Employee Roster

Status: done

## Story

As an **HR Admin**,
I want to see the current Employee roster with search, filter, and pagination,
So that I can find who I need and confirm the roster reflects reality (FR-25).

## Scope Notes (read before starting)

1. **This is a read-only, list-only story.** No new schema, no mutation endpoints. Story 7.1 already added every profile column (`employee_code`, `phone`, `experience`, `technologies`, `position`, `project`, `manager_name`, `location`, `department`, `updated_at`, `archived_at`) and `EmployeeResponse` already exposes all of them. Story 7.2 already mounted `employees_router` at `/api/admin/employees`. This story adds exactly one new route: `GET ""` on that router.
2. **Search/filter/pagination are client-side, not query parameters.** Verified against both the established precedent (`skills/router.py::list_skills_route` / `SkillsPage.tsx` — Story 6.10 fetches the full Skill list once with no query params and does everything in the browser) and the actual working reference prototype (`_bmad-output/E-Development/05-Ritas-Roster-Management-Prototype/05.1-Employees-Tab.html`, `getFiltered()`/`renderEmployees()`, lines ~345-439 — one `employees` array fetched once, then filtered/paginated entirely in JS with **no** separate calls per filter/page change). `GET /api/admin/employees` takes **no query parameters** and returns the **full roster in one response** (active and archived both — the "show archived" toggle is a client-side filter over data already in hand, not a second fetch).
3. **HR_ADMIN-only, hard-scoped.** Mirrors `list_skills_with_content`'s `require_hr_admin(current_user)` gate exactly — an EMPLOYEE session must get `403`, not a filtered/empty roster (AC's own wording: "no EMPLOYEE-role session can reach this endpoint, mirroring FR-14's existing role gate").
4. **Do not touch `assignments/repository.py::list_employees`.** That is a *different* endpoint (the Skill Assignment Flow's employee-picker combobox, Story 3.4-era), already unscoped and already used elsewhere — it is not this story's GET route and has no `archived_at` filter of its own yet (that only becomes relevant once Story 7.5 ships archiving). Leave it exactly as-is; add a new function in `employees/repository.py` instead, matching `skills/repository.py::list_all_skills`'s shape (AD-1 — `employees/` is the sole owner of the `employees` table's queries, same as `skills/` is for `skills`).
5. **No left-pane nav shell in this story.** FR-29 (the left-side nav pane) is Story 7.7's job, built *after* this story specifically because it needs this page to exist first as a real nav target (epics.md's own recommended build order). The UX spec (`05.1-employees-roster.md`) spec's this page *with* the future left-pane shell and flags in its own "Out of Scope" section that 01.1/04.1 (and, by the same logic, this new page today) still use the pre-FR-29 top-header nav. Build this page's header exactly like `SkillsPage.tsx`'s existing top-header (Dashboard/Skills links + user menu), adding a third "Employees" link — consistent with the codebase's actual current state, not the UX spec's future-state shell.
6. **Row/card action icons (Edit, Regenerate Password, Delete/Archive) and "+ New Employee" render but are not wired to real behavior.** Stories 7.4 (Edit), 7.5 (Delete/Archive), 7.6 (Regenerate Password) own those modals; no story has yet built the Create Employee UI either (Story 7.2 was backend-only — see its File List, no frontend files). AC explicitly requires the three row/card action icons to render with descriptive `aria-label`s (UX-DR42) regardless — render all four buttons per the UX spec's toolbar/row layout, wire each to a lightweight "not available yet" toast rather than leaving them silently inert (matches this codebase's established no-silent-dead-button convention) or a real navigation/modal that doesn't exist.
7. **Sort order matters for deterministic pagination.** `list_all_skills` has no `ORDER BY` (fine for a grid); this story's list backs a paginated table, so sort by `employee_code` ascending in the repository query — this also happens to match the 5 seeded demo employees' natural `EMP-0001`..`EMP-0005` order (Story 7.1 backfill).

## Acceptance Criteria

**AC1 — Default roster view:**
**Given** I open the Employees page
**When** the roster loads
**Then** I see a paginated list (15 records/page, UX-DR35) of active Employees by default, in a Table view (UX-DR34: columns ID, Name, Position, Department, Email, Status) with a toggle to switch to a Card view — both views share the same filter/search/page state.

**AC2 — Search and filter:**
**Given** I search by name or filter by Department/Position
**When** results update
**Then** the list (in whichever view is active) reflects the filter, pagination resets to page 1, and clearing the filter restores the full list.

**AC3 — Show archived:**
**Given** I enable "Show archived"
**When** the list re-renders
**Then** archived Employees (per Story 7.1's `archived_at`) appear, visually distinguished by an Archived status badge (never color-only, UX-DR41) — disabling it hides them again.

**AC4 — Role-scoped:**
**And** the roster endpoint hard-scopes to what an HR Admin session is allowed to see (no EMPLOYEE-role session can reach this endpoint, mirroring FR-14's existing role gate).

**AC5 — Action icon accessibility:**
**Given** the Table view's row/card action icons (Edit, Regenerate Password, Delete/Archive — the entry points into Stories 7.4/7.5/7.6)
**When** they render
**Then** each carries a descriptive `aria-label` naming the action and the Employee (e.g. "Edit {Employee name}") — never icon-only with no accessible name (UX-DR42).

**AC6 — Narrow-viewport table:**
**Given** a viewport narrower than the Table view's minimum comfortable width
**When** the roster renders in Table view
**Then** the table scrolls horizontally within its own container rather than compressing columns to illegibility (UX-DR43).

## Tasks / Subtasks

- [x] **Task 1: Repository** (`backend/app/employees/repository.py`)
  - [x] `list_all_employees(db) -> list[Employee]`: unfiltered `select(Employee)`, `.order_by(Employee.employee_code)`, no `archived_at` filter (the frontend, not the query, decides what "show archived" means) — mirrors `skills/repository.py::list_all_skills`'s shape.

- [x] **Task 2: Service** (`backend/app/employees/service.py`)
  - [x] `list_employees_service(db, *, current_user) -> list[EmployeeResponse]`: `require_hr_admin(current_user)` first, then `repository.list_all_employees(db)`, mapped through `EmployeeResponse.model_validate(...)`.

- [x] **Task 3: Router** (`backend/app/employees/router.py`)
  - [x] `GET ""` → `list_employees_route`, `response_model=list[EmployeeResponse]`. No new mount needed — `employees_router` is already mounted at `/api/admin/employees` (Story 7.2).

- [x] **Task 4: Backend tests** (`backend/tests/test_employees_router.py`, extend existing file)
  - [x] AC1/full roster: create 2+ employees via the existing `POST` route, `GET`, assert both appear with every `EmployeeResponse` field present and no password/hash leakage.
  - [x] AC3/archived-inclusion: directly set `archived_at` on a test-created row via the private session (Story 7.5 doesn't exist yet, so there's no API path to archive) — assert `GET` still returns it (i.e., the endpoint applies no `archived_at` filter; that filtering is the frontend's job).
  - [x] Deterministic order: assert returned `employee_code`s are ascending.
  - [x] AC4: EMPLOYEE session → `403`; unauthenticated → `401`.
  - [x] Full regression run; record before/after counts in the Dev Agent Record.

- [x] **Task 5: Frontend API client** (`frontend/src/lib/api/employeesApi.ts`, new file)
  - [x] `EmployeeResponse` TS interface mirroring the backend schema exactly (all fields from `backend/app/employees/schemas.py::EmployeeResponse`, including `archived_at: string | null`).
  - [x] `listEmployees(): Promise<EmployeeResponse[]>` → `GET /api/admin/employees`, mirrors `skillsApi.ts::listSkillsWithContent`'s shape.

- [x] **Task 6: Employees page** (`frontend/src/pages/hr/EmployeesPage.tsx`, new file)
  - [x] Header: reuse `SkillsPage.tsx`'s exact top-header pattern (logo, Dashboard/Skills/Employees nav links, user menu + Sign Out), with "Employees" as the active link this time (Scope Note 5).
  - [x] Toolbar: heading + summary count (`{N} employees · {M} active`), search-by-name input, Department filter select (options derived from the fetched roster's distinct non-null values, matching the prototype's `updateFilterOptions()`), Position filter select (same), "Show archived" checkbox, Table/Card view toggle, "+ New Employee" button (Scope Note 6 — toast stub).
  - [x] Fetch once on mount via `listEmployees()` (loading / error+Retry / empty states, mirroring `SkillsPage.tsx`'s `refetch` pattern with a `requestIdRef` staleness guard).
  - [x] Client-side derived list: filter by search term (name, case-insensitive substring) AND department AND position AND (archived-toggle governs whether `archived_at !== null` rows are included) — AC2's "blank/optional field never makes an Employee unfindable via Name search" from PRD FR-25 falls out naturally (filters are independent `AND` clauses; an employee with no department simply doesn't match a department filter, but still matches on name search alone).
  - [x] Pagination: 15/page over the filtered result; changing search/filter/archived-toggle resets to page 1 (AC2); changing the view toggle does not (AC1's "share the same filter/search/page state").
  - [x] Table view: columns ID/Name/Position/Department/Email/Status (AC1), `overflow-x-auto` wrapper + `min-w-[720px]` table (AC6, matches the prototype's exact classes), row action icons with `aria-label`s (AC5).
  - [x] Card view: same fields + actions, responsive grid (`grid-cols-1 md:grid-cols-2 xl:grid-cols-3`), same `aria-label`'d actions (AC5).
  - [x] Status badge: text-labeled "Active"/"Archived" (not color-only, AC3/UX-DR41) — reuse-worthy small component or inline, matching the prototype's `statusBadge()` shape (green/active vs. gray/archived, both carrying visible text).

- [x] **Task 7: Route** (`frontend/src/App.tsx`)
  - [x] Add `<Route path="/employees" element={<RequireAuth><EmployeesPage /></RequireAuth>} />` (route matches the UX spec's `/employees`, Scope Note 5's header links to it). Also added the "Employees" nav link to `Dashboard.tsx` and `SkillsPage.tsx`'s existing headers (not originally an explicit task, but without it the new page would be an orphan route reachable only by typing the URL — matches how Story 6.10 added the "Skills" link to `Dashboard.tsx` when it shipped).

- [x] **Task 8: Frontend tests** (`frontend/src/tests/EmployeesPage.test.tsx`, new file, mirrors `SkillsPage.test.tsx`'s structure)
  - [x] Renders loading → loaded roster; error+Retry path; empty-roster path.
  - [x] Search filters by name; Department/Position filters compose with search; clearing restores the full list.
  - [x] Show-archived toggle reveals/hides archived rows with a visible "Archived" badge.
  - [x] Table ↔ Card toggle preserves search/filter/page state (AC1).
  - [x] Pagination: a >15-employee fixture set renders page controls and paginates correctly; changing a filter resets to page 1 (AC2).
  - [x] Every row/card action button has the expected `aria-label` text (AC5).
  - [x] `tsc --noEmit` and `vite build` clean; record before/after in the Dev Agent Record.

### Review Findings

_(`bmad-code-review`, 2026-09-11, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor. Acceptance Auditor independently re-ran every backend/frontend test suite, `tsc --noEmit`, and `vite build` and reproduced the Dev Agent Record's counts exactly; zero AC/Scope Note violations found.)_

- [x] [Review][Decision] `GET /api/admin/employees` returns the entire roster unbounded, every field, every load — no `LIMIT`/pagination on the query [`backend/app/employees/repository.py:20-29`] — **RESOLVED (user, 2026-09-11): keep as-is.** Matches this story's own explicit Scope Note 2 (client-side filtering over one full fetch, mirroring the `SkillsPage`/Story 6.10 precedent) and is fine at pilot scale. No code change.

- [x] [Review][Patch] `test_list_employees_returns_full_roster_with_all_fields` only checks field *presence*, not values [`backend/tests/test_employees_router.py:295`]
- [x] [Review][Patch] Pagination Prev/Next handlers use raw `page` state instead of the clamped `currentPage`, so a click can silently no-op if the two ever diverge [`frontend/src/pages/hr/EmployeesPage.tsx:368,389`]
- [x] [Review][Patch] Department/Position filter options are computed from the full employee list regardless of the "Show archived" toggle, so an option that exists only on archived rows appears while archived rows are hidden and always yields "No employees match your search" [`frontend/src/pages/hr/EmployeesPage.tsx:128-129`]
- [x] [Review][Patch] AC6 (narrow-viewport horizontal scroll) is marked "covered by passing tests" in the Completion Checklist/Dev Agent Record, but no test asserts the `overflow-x-auto`/`min-w-[720px]` scroll-container classes exist [`frontend/src/pages/hr/EmployeesPage.tsx:302`, `frontend/src/tests/EmployeesPage.test.tsx`]

- [x] [Review][Defer] Hardcoded "Rita" identity in the header instead of reading the real authenticated user [`frontend/src/pages/hr/EmployeesPage.tsx:177`] — deferred, pre-existing (copied faithfully from `SkillsPage.tsx`/`Dashboard.tsx` per this story's own instruction to mirror that page's structure; not a new defect)
- [x] [Review][Defer] No frontend role-gating on protected routes — `RequireAuth` checks authentication only, never role [`frontend/src/App.tsx:3`] — deferred, pre-existing (systemic across the whole app; the backend's `403` is the real, correctly-enforced security boundary per AC4)
- [x] [Review][Defer] A failed refetch (Retry) would wipe an already-successfully-rendered roster entirely rather than keeping stale data visible alongside the error [`frontend/src/pages/hr/EmployeesPage.tsx:282-339`] — deferred, pre-existing (identical pattern copied from `SkillsPage.tsx`; also currently unreachable here since nothing but the Retry button itself re-triggers `refetch()`)
- [x] [Review][Defer] Selected Department/Position filter value can go stale if options are recomputed after a refetch — deferred, currently unreachable (no post-mount refetch trigger exists in this story's scope yet; becomes relevant once Stories 7.4-7.6 wire real mutations)
- [x] [Review][Defer] Department/Position values aren't trimmed or case-normalized at create time, so differently-cased/whitespaced entries fragment into separate filter options — deferred, pre-existing (root cause is Story 7.2's `CreateEmployeeRequest`, already `done`, out of this story's scope)
- [x] [Review][Defer] No read-side length bound on free-text profile fields — deferred, low real risk (only the validated Create endpoint writes them today; theoretical future-proofing)
- [x] [Review][Defer] Filter dropdown options sort with default JS lexicographic order, not locale-aware — deferred, cosmetic (matches the reference prototype's own identical `.sort()` behavior)
- [x] [Review][Defer] Pagination renders one button per page with no windowing — deferred, fine at pilot scale (matches the reference prototype exactly)
- [x] [Review][Defer] No debounce on the search input — deferred, negligible at current/expected pilot scale (consistent with this story's already-reasoned client-side-filtering design)
- [x] [Review][Defer] Dev Agent Record's live Playwright verification is unretained/unverifiable from the diff alone — deferred, process note only (every other quantitative claim in the record was independently reproduced exactly by the Acceptance Auditor)

Dismissed as false positives / no real consequence: "redundant `Depends(get_current_user)`" (required to inject `CurrentUser` into the handler — router-level `dependencies=[...]` only gates access, doesn't inject values; identical pattern used by every other route in this router and in `skills/router.py`); shared `toastMessage` not resetting its dismiss timer on an identical repeated message (technically true of React's state-bailout, but zero observable consequence since the displayed text doesn't change either way).

## Dev Notes

### Why client-side filtering, not query parameters — verified, not assumed

Two independent pieces of evidence converge: (1) `skills/router.py::list_skills_route` (the most directly analogous existing endpoint — also an HR-Admin-only roster-style list feeding a toolbar with search/filter) takes zero query parameters, and `SkillsPage.tsx` does 100% of its filtering/search in the browser over one fetched array; (2) the actual working reference prototype's own JS (`05.1-Employees-Tab.html` lines 345-439) implements `getFiltered()` as a pure in-memory `Array.prototype.filter` over one `employees` array populated once via `getEmployees()`, with `renderEmployees()` re-deriving filtered+paginated output on every keystroke/toggle/page click — never a second network call. At this project's real data scale (single-digit to low-hundreds of Employees for a pilot), a full-fetch-then-filter approach is both simpler and already the codebase's established pattern; do not add query-parameter-based server-side filtering/pagination that neither precedent nor the AC text calls for.

### `EmployeeResponse` already has everything this story's table/card views need

No new Pydantic schema is needed (unlike Stories 7.1/7.2, which each added real schema work). `EmployeeResponse` (from Story 7.2) already carries every field the UX spec's Table columns (ID/Name/Position/Department/Email/Status) and Card view (+ the remaining profile fields, reachable via a future Edit modal) require. `Status` is derived client-side from `archived_at` (`null` → "Active", non-null → "Archived") — there is no separate `status` field on the model or response; do not add one.

### The "+ New Employee" / row-action gap is real, not an oversight to silently fix here

Story 7.2 built `POST /api/admin/employees` but explicitly no frontend (confirmed via its File List — zero `frontend/` entries). No story in `epics.md` currently owns a "Create Employee modal" frontend task by name; it's implicitly bundled into FR-24/Story 7.2's UX intent but was never actually built. This story's AC doesn't test creation, editing, regenerating, or deleting/archiving — only viewing. Per Scope Note 6, render all four action affordances (matches AC5's explicit aria-label requirement and the UX spec's toolbar/row layout) but wire them to a stub ("Coming soon" toast) rather than inventing unspecified modal/navigation behavior that a later story (7.2's frontend half, 7.4, 7.5, 7.6) will actually own. Flag this gap in the Dev Agent Record so it isn't silently rediscovered later.

### Filter dropdown source — derive from the fetched roster, not a separate lookup

PRD FR-25's consequence text and the prototype's `updateFilterOptions()` both confirm Department/Position filter *options* are just the distinct non-null values already present in the fetched Employee list (`[...new Set(employees.map(e => e.department))].sort()`), not a separate `/departments` endpoint. Recompute on every fetch (so a newly-created Employee with a brand-new Department value would appear as a filter option after the next `refetch()`, even though this story doesn't build Create's UI to trigger that itself).

### Reuse, don't reinvent, the Story 6.10 page shape

`SkillsPage.tsx` is the closest existing analog (HR-Admin-only listing page, top-header nav, fetch-once-then-filter, loading/error/empty states, `requestIdRef` staleness guard on refetch). Mirror its structure and conventions directly rather than designing a new page pattern from scratch — the codebase's established convention (see Story 6.10/6.x Dev Notes throughout `project-context.md`) is to reuse a sibling page's shape whenever one already exists for the same role/pattern.

## Dev Agent Record

### Debug Log

- Red phase confirmed before writing any implementation: the 5 new router tests all failed with `405 Method Not Allowed` (no `GET` route existed yet) before Task 1-3 landed.
- All 5 new backend tests passed on the first implementation attempt (no red→green iteration needed beyond the initial red confirmation) — full backend regression: **662 passed, 2 skipped, 0 failed** (657-passed post-Story-7.2 baseline + 5 new).
- All 11 new frontend tests passed on the first run. `tsc --noEmit`: 31 pre-existing errors, byte-identical before/after (confirmed via `git stash` against baseline — zero new errors from any file this story touched). `vite build`: clean, 530 modules (up from 513 pre-story).
- **Live browser verification required an unplanned Docker rebuild**: the running `talentpilot-api` container has no volume mount (documented recurring fact since Story 6.4/6.5/7.1), so the new `GET` route 404'd against the live container until `docker compose build backend && docker compose up -d backend` was run. Also discovered mid-verification that port 5173 is occupied by the *existing* `talentpilot-ui` Docker container serving a stale pre-story build — `vite dev` silently fell back to port 5174, and the first verification pass was accidentally pointed at the stale container (explains an initial false failure: no "Employees" nav link, `/employees` 404). Corrected by pointing the verification script at the actual dev-server port.
- Live Playwright smoke test (ad hoc `playwright-core` + the pre-existing local Chromium cache from a prior session's install, uninstalled after use — no `package.json`/lockfile change retained) against the rebuilt Docker backend + local `vite dev`, logged in as the real seeded Rita account: nav link present → roster loads with the 5 real seeded demo employees (`EMP-0001`..`EMP-0005`) → summary count correct → name search narrows to 1 row → Card view toggle works and preserves the active search filter → Show Archived toggles without error → 5 Edit buttons found via `aria-label` → clicking a row action shows the "not available yet" toast without crashing → a real EMPLOYEE-role login (Casey) gets a genuine `403` from `GET /api/admin/employees`. All 10 checks passed. Two benign console messages observed (a `401` from the app's own pre-login session-check on `/login` page load, and one unrelated `404` — both pre-existing patterns already documented in prior stories' Dev Agent Records, not introduced by this story).

### Completion Notes

- Implemented `GET /api/admin/employees` (Story 7.3, FR-25): the first read-only list endpoint for the `employees/` module, following `skills/repository.py::list_all_skills`'s exact shape but adding a deterministic `ORDER BY employee_code` (skills' list backs an unordered grid; this one backs a paginated table).
- Confirmed via direct inspection of `skills/router.py`/`SkillsPage.tsx` and the actual working reference prototype's JS (not assumed) that search/filter/pagination/"show archived" belong entirely on the frontend, over one full-roster fetch — no query parameters were added to the endpoint.
- `EmployeesPage.tsx` mirrors `SkillsPage.tsx`'s structure directly (fetch-once-then-filter, `requestIdRef` staleness guard, loading/error+Retry/empty states) rather than inventing a new page shape.
- Per Scope Note 6, the "+ New Employee" button and the three row/card action icons (Edit, Regenerate Password, Delete/Archive) render with the exact `aria-label`s the AC/UX spec require, but are wired to a shared "Not available yet — coming in a future story." toast rather than real navigation/modals — no story currently owns the Create Employee frontend (Story 7.2 was backend-only), and Edit/Regenerate/Delete-Archive belong to Stories 7.4/7.5/7.6 respectively. This is flagged explicitly rather than silently left as dead buttons.
- Added the "Employees" nav link to the two existing HR Admin pages (`Dashboard.tsx`, `SkillsPage.tsx`) so the new page is actually reachable through navigation, not just by typing the URL — a small, in-scope addition beyond the story's original task list, discovered while wiring the route.
- Live-verified end-to-end against the real Docker backend + a real seeded HR Admin login (not just the test suite): the roster genuinely renders the 5 real seeded demo employees, filters/toggles/pagination-adjacent state behave correctly in a live browser, and the HR-only role gate (AC4) returns a real `403` for an EMPLOYEE-role session — not just asserted by a mocked test.
- Left `assignments/repository.py::list_employees` (the Skill Assignment Flow's employee-picker read) completely untouched, per Scope Note 4 — it is a different endpoint with a different purpose and is out of this story's ownership.

### Code Review Patches (2026-09-11)

4 patch findings from `bmad-code-review` applied (see Review Findings above):
- `test_list_employees_returns_full_roster_with_all_fields` now populates and asserts every optional field's actual value (not just key presence) — a swapped/mismapped column would now fail the test.
- Pagination Prev/Next button handlers now compute from the clamped `currentPage` instead of the raw `page` state, closing a latent (currently unreachable, but real) stale-state bug.
- Department/Position filter options are now derived from the archived-toggle-respecting subset of the roster, not the full unfiltered list — an option that exists only on archived rows no longer appears while "Show archived" is off.
- Added a dedicated AC6 test asserting the `overflow-x-auto`/`min-w-[720px]` scroll-container classes are present on the table. **Caveat, worth remembering:** this only verifies the CSS classes exist — jsdom cannot measure real layout/overflow/scroll behavior, so this is evidence the mechanism is wired correctly, not a full visual/behavioral confirmation of AC6 at a real narrow viewport (that was separately confirmed by eye during the live Playwright verification, not by this test).

Re-verified after patches: backend 662 passed / 2 skipped / 0 failed (unchanged count — the value-assertion patch strengthened an existing test function rather than adding a new one). Frontend 355 passed / 0 failed (354 + 1 new AC6 test).

### Test Results

```
Backend:  662 passed, 2 skipped, 0 failed  (657-passed post-Story-7.2 baseline + 5 new tests; unchanged after code-review patches, which strengthened an existing test rather than adding one)
Frontend: 355 passed, 0 failed  (343-passed baseline + 11 new tests + 1 more from the AC6 code-review patch)
tsc --noEmit: 31 pre-existing errors, unchanged (verified via git-stash baseline diff, both pre- and post-patch)
vite build: clean, 530 modules
```

No new regressions relative to baseline commit `30bd7a78`. Live browser verification (Playwright, ad hoc, against a rebuilt `talentpilot-api` Docker image and the real seeded dev DB): all 10 checks passed, including a genuine `403` for an EMPLOYEE-role session. All counts re-verified after the code-review patches (see Code Review Patches above).

## File List

New files:
- `frontend/src/lib/api/employeesApi.ts` — `EmployeeResponse` interface, `listEmployees()`
- `frontend/src/pages/hr/EmployeesPage.tsx` — the roster page (Table/Card views, search, filters, archived toggle, pagination, action-icon stubs); code review: pagination Prev/Next now use clamped `currentPage`, Department/Position options now respect "Show archived"
- `frontend/src/tests/EmployeesPage.test.tsx` — 12 tests covering all 6 ACs (11 at implementation + 1 code-review AC6 patch)

Modified files:
- `backend/app/employees/repository.py` — `list_all_employees` added
- `backend/app/employees/service.py` — `list_employees_service` added
- `backend/app/employees/router.py` — `GET ""` → `list_employees_route` added
- `backend/tests/test_employees_router.py` — 5 new tests (full roster/field shape, archived-inclusion, ordering, 403, 401); code review: the full-roster test now asserts actual field values, not just key presence
- `frontend/src/App.tsx` — `/employees` route added
- `frontend/src/pages/hr/Dashboard.tsx` — "Employees" nav link added
- `frontend/src/pages/hr/SkillsPage.tsx` — "Employees" nav link added
- `_bmad-output/implementation-artifacts/deferred-work.md` — code review: 10 findings logged under a new `7-3-hr-admin-views-the-employee-roster` heading

No changes to:
- `backend/app/assignments/repository.py::list_employees` — a different, pre-existing endpoint (Scope Note 4), untouched
- `backend/app/employees/schemas.py` — `EmployeeResponse` already existed from Story 7.2, reused as-is
- `backend/app/main.py` — `employees_router` already mounted (Story 7.2)

## Architecture Compliance

- **AD-1**: all new queries against the `employees` table live in `employees/repository.py` — no other module gains a direct `Employee` query because of this story.
- **AD-6/FR-14**: `GET /api/admin/employees` is HR_ADMIN-only via `require_hr_admin`, matching every other `/api/admin/*` list endpoint in this codebase.
- **AR-24/AR-25**: not touched by this story (read-only; no credential or session-revalidation logic involved).

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.3] — full AC text (as extended by the 2026-09-11 implementation readiness check with AC5/AC6)
- [Source: _bmad-output/C-UX-Scenarios/05-ritas-roster-management/05.1-employees-roster/05.1-employees-roster.md] — full page spec: object IDs, table/card columns, toolbar, states, accessibility requirements
- [Source: _bmad-output/E-Development/05-Ritas-Roster-Management-Prototype/05.1-Employees-Tab.html] — working reference prototype (lines ~85-180 toolbar/table/card markup, ~340-439 filter/pagination JS)
- [Source: _bmad-output/implementation-artifacts/7-1-employees-module-foundation-schema-migration-and-credential-reconciliation.md] — schema/profile fields this story reads
- [Source: _bmad-output/implementation-artifacts/7-2-hr-admin-creates-a-new-employee-record.md] — `employees_router` mount point, `EmployeeResponse` shape, `require_hr_admin` usage pattern
- [Source: backend/app/skills/router.py::list_skills_route, backend/app/skills/repository.py::list_all_skills, backend/app/content/service.py::list_skills_with_content] — the exact list-endpoint pattern this story mirrors
- [Source: frontend/src/pages/hr/SkillsPage.tsx, frontend/src/lib/api/skillsApi.ts] — the page/API-client shape this story mirrors
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#FR-25] — full FR text and consequences

## Completion Checklist

- [x] `list_all_employees` repository function added, ordered by `employee_code`, no `archived_at` filter
- [x] `list_employees_service` added: HR-Admin-gated
- [x] `GET /api/admin/employees` added and working
- [x] `EmployeesPage.tsx` + `employeesApi.ts` implement Table/Card toggle, search, Department/Position filters, Show-archived toggle, 15/page pagination, all sharing state per AC1/AC2
- [x] Row/card action icons render with correct `aria-label`s (AC5), wired to a stub (Scope Note 6)
- [x] Table view horizontally scrolls at narrow widths instead of compressing (AC6)
- [x] Route `/employees` added to `App.tsx`
- [x] All 6 ACs covered by passing backend + frontend tests
- [x] Full backend + frontend regression run, zero new regressions
- [x] `tsc --noEmit` / `vite build` clean
- [x] Live-verified end-to-end in a real browser against a rebuilt Docker backend (not just tests)
- [x] Sprint status updated to `review` (then `done` after code review)

## Change Log

- 2026-09-11: Story created (`bmad-create-story`), building on Story 7.1 (schema) and Story 7.2 (router mount, `EmployeeResponse`). Confirmed via direct inspection of `skills/router.py`/`SkillsPage.tsx` and the actual working reference prototype's JS that filtering/search/pagination are client-side, not query parameters — matches this codebase's one existing precedent (Story 6.10) exactly. Flagged the "+ New Employee"/row-action-wiring gap (no story currently owns the Create Employee frontend) rather than silently building unspecified behavior. Status → `ready-for-dev`.
- 2026-09-11: Implementation complete (`bmad-agent-dev`/Amelia, direct TDD). Backend: `list_all_employees`/`list_employees_service`/`GET ""` added (5 new tests, red confirmed before green); full regression 662 passed/2 skipped/0 failed. Frontend: `EmployeesPage.tsx`/`employeesApi.ts` added, route wired, "Employees" nav link added to `Dashboard.tsx`/`SkillsPage.tsx` (11 new tests, all green on first run); full regression 354 passed/0 failed; `tsc --noEmit` byte-identical to the 31-error pre-existing baseline; `vite build` clean. Live-verified end-to-end via an ad hoc Playwright smoke test against a rebuilt `talentpilot-api` Docker image and the real seeded dev DB — all 10 checks passed, including a genuine `403` for an EMPLOYEE-role session (AC4). Status → `review`.
- 2026-09-11: Code review (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). Acceptance Auditor independently re-ran every test suite/`tsc`/`vite build` and found zero AC/Scope Note violations. 1 decision-needed resolved (unbounded roster fetch — user chose to keep as-is, matches Scope Note 2/Story 6.10 precedent), 4 patches applied (weak test assertions strengthened to check values not just key presence; pagination Prev/Next now use the clamped `currentPage` instead of raw `page` state; Department/Position filter options now respect the "Show archived" toggle; added a real AC6 test for the horizontal-scroll classes), 10 deferred to `deferred-work.md` (hardcoded "Rita" header identity, no frontend role-gating, refetch-wipes-roster-on-error, stale filter option after refetch, unnormalized department/position at create time, no read-side length bound, non-locale-aware dropdown sort, unwindowed pagination, no search debounce, unretained live-verification tooling — all either pre-existing patterns or currently unreachable given this story's scope), 2 dismissed as false positives (a "redundant" `Depends()` that's actually required for FastAPI DI, and a toast dismiss-timer non-issue with zero observable consequence). Full regression re-verified after patches: backend 662 passed/2 skipped/0 failed, frontend 355 passed/0 failed, `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean. Status → `done`.
