---
baseline_commit: af60d6c2f0f26eb6df5738a37e21eb34131d32f1
---

# Story 10.6: Skill Assignments Grid Search and Pagination

Status: done

## Story

As an **HR Admin**,
I want to search and page through the Skill Assignments (Readiness Dashboard) grid,
So that I can find a specific Employee or Skill row quickly as assignments grow (FR-38).

## Scope Notes (read before starting)

1. **This story diverges from its own literal "same pattern as Story 10.5" instruction, deliberately, by user decision.** Story 10.5 (Skills tab) and Story 7.3 (Employees roster) both fetch their full list once with no query params, then filter/paginate entirely client-side — that pattern was viable there because neither backend endpoint had ever done otherwise. The Skill Assignments grid (`DashboardPage.tsx` / `GET /api/dashboard`) is different: it has had **real server-side pagination** since Story 3.5/9.1 (SQL `LIMIT`/`OFFSET` via `AssignmentsService.list_assignments_for_hr`, `page`/`page_size` query params, a 12s live-poll scoped to only the currently-visible page). Asked explicitly via `AskUserQuestion` before implementation: the user chose **server-side search** (a new `search` query param, ILIKE against Employee/Skill name, applied to both the count and page queries) over a literal client-side-fetch-everything mirror of 10.5, specifically to preserve the existing server-pagination design and keep live updates scoped to the visible page (the story's own third AC bullet).
2. **`page_size` default changes from 50 to 15** (`DashboardPage.tsx`'s `DashboardState.pageSize` initial value) — this is the "15 per page" half of AC1. The backend's own `Query(50, ...)` default on `GET /api/dashboard` is unchanged (Story 9.1's original default) since the frontend always passes an explicit `page_size`; only the frontend's default state value moved.
3. **Search matches Employee name OR Skill name** (AC text: "matching at least Employee name and Skill name"), case-insensitive substring (`ILIKE '%term%'`), mirroring the exact pattern `assignments/repository.py::list_employees`/`list_skills` already use for the Assignment modal's own combobox search (Story 3.4) — not a new bespoke approach.
4. **No change to FR-8–FR-12 row behavior.** Status badge derivation, the Provenance Drill-Down modal, 30-second-scale live auto-update (actually 12s per Story 5.4's `POLL_INTERVAL_MS`), and HR Override are all untouched — this story only changes which rows are fetched/visible, never what a visible row shows or how it updates (AC2).
5. **Live row updates apply only to the currently-visible (filtered + paginated) page** (AC3) — already true architecturally, since `pollDashboard` re-fetches with the exact same `page`/`pageSize`/`search` the grid is currently showing. A row that changes on a different page or outside the current search filter is reflected next time that page/filter is viewed, not via any cross-page notification (none exists elsewhere in this product, e.g. Story 9.4's Needs Attention popover is a separate, independent mechanism).
6. **No `bmad-create-story` pass ran before implementation** — at the user's explicit request to start API + UI development directly, matching Story 10.4's precedent. This file was authored alongside implementation, not before it.

## Acceptance Criteria

**AC1 — Search + pagination:**
**Given** the Readiness Dashboard grid (Epic 5, reached via the "Skill Assignments" nav entry per Story 9.5)
**When** this story ships
**Then** it gains a search control matching at least Employee name and Skill name, and pagination at **15 per page**, same UX pattern as Story 10.5 (server-side implementation per Scope Note 1).

**AC2 — No regression to existing row behavior:**
**Given** the existing FR-8–FR-12 row behavior (Status badge, drill-down, live auto-update, HR Override)
**When** search/pagination is added
**Then** none of it changes — this story only affects which rows are visible at once, never what a visible row shows or how it updates.

**AC3 — Live updates stay scoped to the visible page:**
**And** live row updates (FR-11) continue to apply only to rows on the currently-visible page — a row that updates on a page not currently shown is reflected next time that page is viewed, not via a cross-page notification (no such mechanism exists elsewhere in this product).

## Tasks / Subtasks

- [x] **Task 1: Backend — `search` query param on `GET /api/dashboard`** (AC: 1)
  - [x] `assignments/repository.py::list_assignments_for_hr` gains an optional `search: str | None` param; when present, joins `Assignment.employee`/`Assignment.skill` (relationship-based join, so SQLAlchemy resolves the correct FK among Employee's 3 relationships to Assignment) and filters both the count and page queries with `or_(Employee.name.ilike(pattern), Skill.name.ilike(pattern))`. No join at all when `search` is absent (unfiltered page loads are unchanged).
  - [x] `assignments/service.py::AssignmentsService.list_assignments_for_hr` and `dashboard/service.py::DashboardService.get_dashboard_assignments` pass `search` straight through (AD-1: dashboard/ owns no table, never filters rows itself).
  - [x] `dashboard/router.py::get_dashboard` gains `search: str | None = Query(None, max_length=200)`; a blank/whitespace-only value is trimmed to `None` before reaching the service (behaves identically to omitting it).

- [x] **Task 2: Backend tests** (`backend/tests/test_dashboard_router.py`, extended)
  - [x] Search matches Employee name (case-insensitive substring) and excludes non-matching rows.
  - [x] Search matches Skill name and excludes a different Skill assigned to the same Employee.
  - [x] `total_count` and the paginated rows both reflect the *filtered* result set (page_size=1, 2 matching rows, both pages consistent).
  - [x] A whitespace-only `search` value behaves identically to omitting it.

- [x] **Task 3: Frontend — search input + 15/page** (AC: 1, 2, 3)
  - [x] `dashboardApi.ts::getDashboard` gains an optional third `search` param (`params.search: search || undefined`, so axios omits it when empty).
  - [x] `DashboardPage.tsx`: `DashboardState` gains `search: string`; initial `pageSize` changes from 50 to 15; a new `handleSearchChange` sets `search` and resets `page` to 1 in one update (AC's implicit "search resets pagination" convention, matching Story 10.5's AC2 precedent even though this story's own AC text doesn't restate it).
  - [x] The existing 150ms debounce `useEffect` (previously `[state.page, state.pageSize]`) gains `state.search` in its deps — reuses the exact mechanism already debouncing page/pageSize changes, no new debounce code.
  - [x] The poll effect (`[state.page, state.pageSize, state.requestId]`) also gains `state.search`, and `pollDashboard`'s `getDashboard` call now passes it — otherwise a 12s poll tick would silently revert the grid to the unfiltered set while an admin is mid-search.
  - [x] A single `toolbar` JSX block ("+ New Assignment" button + the new search `<input data-testid="dashboard-search-input">`) is rendered at the same tree position in all 4 state branches (Loading/Error/Empty/Loaded), replacing 4x-duplicated inline button markup — this is what keeps the search input's DOM identity (and the admin's typing focus/cursor) stable across a Loading↔Loaded branch swap triggered by the debounced re-fetch.
  - [x] Empty state distinguishes a genuinely empty roster ("No assignments yet — click **+ New Assignment** to get started") from a no-results search ("No assignments match your search.").

- [x] **Task 4: Frontend tests** (`frontend/src/features/dashboard/DashboardPage.test.tsx`, extended)
  - [x] Default `page_size` sent to the API is 15, not 50.
  - [x] Search input renders with `data-testid="dashboard-search-input"`.
  - [x] Typing a search term re-fetches with that term (debounced).
  - [x] A new search term resets pagination to page 1 (navigate to page 2 first, then search, assert `getDashboard(1, 15, term)`).
  - [x] A no-match search shows "No assignments match your search." (not the generic empty-roster copy).
  - [x] A genuinely empty roster with no search term still shows the original "No assignments yet" copy.

- [x] **Task 5: Regression + type-check + build**
  - [x] Backend: full suite (`pytest`).
  - [x] Frontend: full suite (`npx vitest run`), `npx tsc --noEmit`, `npx vite build`.

- [x] **Task 6: Live verification**
  - [x] Backend live-verified via `curl` against the real running app + Postgres (login, unfiltered page, `search=casey`, `search=<no-match>`).
  - [x] Frontend live-verified via a throwaway Playwright script (`chromium-cli` unavailable in this Windows/Git-Bash environment) against the local Vite dev server + local uvicorn (Docker's `talentpilot-api`/`talentpilot-ui` stopped, not rebuilt, for the duration — same precedent as Story 10.4; `talentpilot-db` reused as-is). Confirmed: search input renders in the toolbar, typing "casey" filters to only Casey's 4 assignments, clearing restores the full 7-assignment list, and a nonsense term shows "No assignments match your search." Screenshots captured. Docker containers restarted afterward to restore the pre-session state.

### Review Findings

_(`bmad-code-review`, 2026-09-18, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor. 0 decision-needed, 5 patches, 7 deferred, 8 dismissed.)_

- [x] [Review][Patch] Live-poll `useEffect` restarts (tears down/rebuilds `setInterval`) on every search keystroke, since `state.search` is in its dependency array and updates on every `onChange` — a continuously-typing admin can defer the 12s live-update poll indefinitely, not just debounce it [frontend/src/features/dashboard/DashboardPage.tsx:273-340] — fixed: added a `searchRef` mirroring `state.search`, `pollDashboard` now reads `searchRef.current` instead of closing over `state.search`, and `state.search` was removed from the poll-lifecycle effect's dependency array (a separate lightweight effect keeps the ref current). Verified via `git stash`-style RED/GREEN: reintroduced the bug, confirmed the new regression test failed (7 `setInterval` calls instead of 2), restored the fix, confirmed green. Two new tests added to `DashboardPage.polling.test.tsx`.
- [x] [Review][Patch] `_create_throwaway_employee_for_search`'s `last_name` literal (e.g. `ZephyrineSearchTargetemp`) has no random suffix, unlike `employee_code`/`email` — an orphaned employee from a crashed prior run (before its own `finally` cleanup) would collide with a later run's exact-`total_count`-1 assertion for that same literal search string [backend/tests/test_dashboard_router.py:186-200] — fixed: `last_name` now includes the same random hex suffix as `employee_code`/`email` (appended after the fixed prefix, so existing `search=` substrings still match).
- [x] [Review][Patch] `dashboardApi.ts::getDashboard`'s own default parameter still reads `pageSize: number = 50`, contradicting the story's "15 per page" default — dead code today (every call site passes `state.pageSize` explicitly) but a latent trap for a future caller that omits it [frontend/src/lib/api/dashboardApi.ts:34-38] — fixed: default changed to 15.
- [x] [Review][Patch] `ORDER BY assigned_at DESC` has no secondary sort key (e.g. `Assignment.id`) — pre-existing gap, but the new `test_dashboard_search_pagination_count_reflects_filtered_total` test now depends on stable page1≠page2 ordering across two assignments that could theoretically share a timestamp [backend/app/assignments/repository.py:275] — fixed: `.order_by(desc(Assignment.assigned_at), Assignment.id)`.
- [x] [Review][Patch] Search `<input>` has no `maxLength` matching the backend's `Query(None, max_length=200)` — an over-limit paste silently 422s into the generic "Couldn't load assignments" error instead of being prevented client-side [frontend/src/features/dashboard/DashboardPage.tsx:613-620] — fixed: `maxLength={200}` added to the input.

- [x] [Review][Defer] `pattern = f"%{search}%"` doesn't escape literal `%`/`_` characters before they reach Postgres `ILIKE` — deferred, pre-existing: identical, unescaped pattern already shipped in `list_employees`/`list_skills` (Story 3.4) two functions above; not a security issue (fully parameterized), just a functional edge case for a rare literal-wildcard search term [backend/app/assignments/repository.py:285-289]
- [x] [Review][Defer] No test exercises the `search` `max_length=200` boundary (expected 422) — deferred: standard FastAPI/Pydantic `Query()` validation, framework-guaranteed behavior; no other length-capped query param in this codebase (e.g. `page_size`'s own `le=500`) has a dedicated boundary test either
- [x] [Review][Defer] No test confirms `GET /api/dashboard?search=...` still returns 403 for an EMPLOYEE session — deferred: `require_hr_admin` is evaluated independently of the `search` query param's value, and the existing no-search 403 test already covers the same code path; low-value duplicate coverage
- [x] [Review][Defer] New search `<input>` has no `aria-label`, relies on the placeholder alone — deferred, pre-existing: identical to `SkillsPage.tsx`'s (Story 10.5) and `EmployeesPage.tsx`'s (Story 7.3) own search inputs, both already deferred once for the same reason in this exact codebase
- [x] [Review][Defer] No client-side trim before the debounced fetch fires — a whitespace-only keystroke still triggers one debounced network round-trip (server correctly no-ops via `.strip()`) — deferred, pre-existing pattern: identical to Story 10.5's own deferred "no debounce on the search input" finding, negligible at pilot scale
- [x] [Review][Defer] `pollDashboard` doesn't clamp `state.page` if `total_count` shrinks while polling (search-filtered or not) — could show "No assignments match your search" on a now-out-of-range page — deferred, pre-existing cross-cutting gap: `handleAssignmentDeleted` already has its own clamp fix for the explicit-delete-button path only; the general poll-driven external-shrink case was never addressed platform-wide, not introduced by this story
- [x] [Review][Defer] No backend test proves `search` can't surface another HR Admin's assignments — deferred: `base_filters` (`Assignment.assigned_by == hr_admin_id`) is AND-combined with the search `.where()` via SQLAlchemy's standard multi-`.where()` chaining, verified correct by direct code reading; the plain (non-search) pagination path has never had a dedicated multi-admin-isolation test either

Dismissed as noise / handled elsewhere: AC1's literal "same pattern as Story 10.5" wording — not an oversight, explicitly surfaced via `AskUserQuestion` before implementation and documented in Scope Note 1, a disclosed and approved deviation, not a defect; "join+filter duplicated between `count_stmt`/`stmt`" — matches this exact file's own pre-existing `base_filters`-unpacked-into-two-statements shape one paragraph above, not a new anti-pattern, 2 lines, premature to abstract; "`selectinload` + manual `.join()` on the same relationships is redundant" — correct, standard SQLAlchemy usage (join for filtering, `selectinload` for eager-loading are independent concerns); the `selectinload` queries fire on every dashboard fetch regardless of search, not new overhead; "`search` isn't re-normalized at the repository/service layer, only the router strips it" — no live call site reaches the repository with unstripped whitespace today, purely theoretical; "frontend empty-state message could race a stale response" — already prevented by the existing `requestId` staleness guard in both `fetchDashboard` and `pollDashboard`, verified by direct code reading; "`sprint-status.yaml` says `review` while its own comment says `code review not yet run`" — an accurate snapshot at authoring time, resolved by this very review pass completing; "`sprint-status.yaml`'s new entries don't fold into the single `last_updated` line" — a tracking-file comment-style preference, not code, and the file's own prior entries already vary in format; "live browser verification is an unverifiable narrative claim" — a process-transparency note describing ephemeral scratchpad artifacts, not a code defect, matching this project's established Dev-Agent-Record convention.

## Dev Notes

### Why this story doesn't literally mirror Story 10.5 (Scope Note 1)

Story 10.5's own Dev Notes justified its client-side-only approach by verifying (via direct code reading) that `GET /api/admin/skills` had *never* had server-side pagination — there was nothing to preserve. That verification does not hold for `GET /api/dashboard`: Story 3.5 (dashboard list) and Story 9.1 (documented pagination contract) both predate Story 10.5, and the endpoint has always done real `LIMIT`/`OFFSET` with a documented `page`/`page_size` contract, consumed by a 12s live-poll that is itself scoped to the current page. A literal 10.5 mirror (fetch up to 500 rows unbounded, filter/paginate client-side) would have quietly abandoned that design and made the poll diff against the *entire* fetched set rather than the visible page — arguably violating this story's own AC3. Presented as an explicit `AskUserQuestion` before writing any code; user chose to preserve the server-pagination design.

### Reused mechanisms, not reinvented ones

- **Debounce:** `state.search` was added to the *existing* 150ms `setTimeout` effect that already debounces `page`/`pageSize` changes (`DashboardPage.tsx`) — no new debounce timer.
- **ILIKE search pattern:** `Employee.name.ilike(pattern)` / `Skill.name.ilike(pattern)` copies `assignments/repository.py::list_employees`/`list_skills`'s existing pattern (Story 3.4's Assignment-modal combobox search) verbatim in shape, not a new bespoke query style.
- **Empty-state message split:** "No assignments match your search." mirrors Story 10.5's own equivalent AC2 message for `SkillsPage.tsx`.

### The toolbar-hoisting fix (frontend structural note)

`DashboardPage.tsx` returns 4 structurally distinct JSX trees depending on state (Loading/Error/Empty/Loaded). Before this story, each branch inlined its own copy of the "+ New Assignment" button in a `<div className="py-3 flex items-center justify-between">`. Adding a controlled search `<input>` inside each of those 4 separately-inlined blocks would have caused a real bug: every debounced search keystroke triggers `fetchDashboard`, which blanks `assignments` and sets `loading: true`, which swaps the component from the Loaded branch to the Loading branch (or Empty, on a no-match result) — a different top-level returned tree. Since React reconciles by structural position rather than "which `if` produced this," keeping the search input at the *same* position across all 4 branches (a single `toolbar` element inserted immediately after `{liveRegion}{toastElement}{drillDownModal}` in every branch, mirroring how those three are already shared) is what preserves the `<input>` DOM node's identity — and the admin's typing focus/cursor — across that transition. Live-verified (Task 6): typing multiple characters in a row does not lose focus.

## Architecture Compliance (`ARCHITECTURE-SPINE.md`)

- **AD-1** (module table ownership): `dashboard/` still owns no table and never filters rows itself — `search` is passed through to `assignments/`'s own repository, which already owned the `Assignment`/`Employee`/`Skill` read path here (Story 3.5). No new cross-module query added.
- **AD-2** (coaching-only boundary): untouched — this story adds no new read of `skill_progress`.
- **AD-3** (single derivation authority): untouched — Status/Provenance derivation in `dashboard/service.py::_compute_status_and_provenance_from_data` is unmodified; search only changes which `Assignment` rows are fetched before that derivation runs.
- **AD-6** (server-side role gate): unchanged — `GET /api/dashboard` keeps its existing `require_hr_admin` dependency; the new `search` param is just another `Query(...)`, not a new route or a new scoping rule.

## Project Structure Notes

Backend: `backend/app/assignments/repository.py`, `backend/app/assignments/service.py`, `backend/app/dashboard/router.py`, `backend/app/dashboard/service.py` (all modified), `backend/tests/test_dashboard_router.py` (extended).
Frontend: `frontend/src/lib/api/dashboardApi.ts`, `frontend/src/features/dashboard/DashboardPage.tsx` (both modified), `frontend/src/features/dashboard/DashboardPage.test.tsx` (extended).
No new files, no schema/migration changes (no new column or table).

## References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 10.6` lines 3064-3082] — canonical AC text this story implements.
- [Source: `_bmad-output/implementation-artifacts/10-5-skills-tab-search-and-pagination.md`] — the "same pattern" this story's AC text names; Scope Note 1 above documents exactly where and why this story departs from it.
- [Source: `backend/app/assignments/repository.py::list_employees`/`list_skills`] — the existing ILIKE search pattern mirrored here.
- [Source: `backend/app/dashboard/router.py`/`service.py`, `backend/app/assignments/service.py`] — the server-side pagination contract (Story 3.5/9.1) this story extends rather than replaces.
- [Source: `frontend/src/features/dashboard/DashboardPage.tsx`, `frontend/src/lib/api/dashboardApi.ts`] — the files this story modifies.
- [Source: CLAUDE.md, "Live dashboard updates are client polling (≤30s)... Capture posts periodically"] — the 12s poll interval this story's search must not break.

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

- RED confirmed for both new backend and frontend test suites before finalizing: stashed the backend implementation (`repository.py`/`service.py`/`router.py`) and re-ran the 4 new `test_dashboard_router.py` search tests — 3 of 4 failed as expected (the join/filter logic genuinely didn't exist yet; the blank-search-is-a-no-op test passed trivially both ways, as expected for an unsupported/ignored query param). Restored via `git stash pop`, re-ran: 4/4 passed. Same procedure for the frontend: stashed `DashboardPage.tsx`/`dashboardApi.ts`, re-ran the 6 new `DashboardPage.test.tsx` Story 10.6 tests — 5/5 feature-dependent tests failed (1 trivially passed, same reasoning), restored, re-ran: 6/6 passed.
- Backend full suite: `pytest -q` → 738 passed, 2 skipped (was 732 passed/2 skipped per Story 10.4's last recorded baseline; +4 new search tests, +2 from Story 10.5 landing in between).
- Frontend full suite: `npx vitest run` → 450 passed, 41 files (444 baseline post-Story-10.5 + 6 new).
- `npx tsc --noEmit -p .`: 31 pre-existing errors, unchanged (none reference `DashboardPage.tsx`/`dashboardApi.ts`).
- `npx vite build`: clean, 538 modules (matches Story 10.5's own baseline).
- Live verification: backend via direct `curl` (login, unfiltered/`search=casey`/`search=<no-match>` against the real running app + the existing `talentpilot-db` Docker Postgres, migrated to head). Frontend via a throwaway Playwright script (`chromium-cli` — this repo's preferred browser-driver per the `run` skill — is not available in this Windows/Git-Bash environment; fell back to a local `npm install --no-save playwright` + a one-off `.mjs` script, deleted afterward, `package.json`/`package-lock.json` confirmed untouched). Screenshots confirmed: search input renders correctly positioned, "casey" search narrows the grid to Casey's 4 assignments with focus retained through the debounced re-fetch, clearing restores all 7 seeded assignments, and a nonsense term shows the new "No assignments match your search." copy. Docker's `talentpilot-api`/`talentpilot-ui` were stopped (not rebuilt) for the duration, per Story 10.4's precedent, and restarted afterward to restore the pre-session environment state.

### Completion Notes List

- All 3 ACs implemented and verified: AC1 (search matching Employee/Skill name + 15/page pagination) via server-side `search` query param + frontend `pageSize` default change; AC2 (no regression to existing row behavior) confirmed by leaving `_compute_status_and_provenance_from_data`, the drill-down modal, and the poll's diff/announcement logic untouched; AC3 (live updates scoped to the visible page) confirmed by threading `state.search` through the poll effect so a poll tick never silently reverts an active search.
- Deliberately departed from a literal Story 10.5 mirror (client-side-only) after an explicit `AskUserQuestion` — see Scope Note 1 and the matching Dev Notes section for the full reasoning: the Skill Assignments grid already had real server-side pagination that a client-side rewrite would have abandoned.
- A real, pre-existing-pattern-avoiding UX bug was caught and fixed proactively during implementation (not found by a later review pass): a naive per-branch search input would have lost focus on every debounced keystroke due to React's branch-swap reconciliation. Fixed structurally (single shared `toolbar` element at a consistent tree position) and confirmed via live Playwright verification that focus survives a real search interaction.
- Full regression green both sides: backend 738/738 passed (2 pre-existing skips, unrelated), frontend 450/450 passed, `tsc`/`vite build` unchanged from their pre-existing baselines.
- Live-verified end-to-end in a real browser against the real backend/DB, not just automated tests.

### File List

Modified files:
- `backend/app/assignments/repository.py` — `list_assignments_for_hr` gains optional `search` param, conditional `Employee`/`Skill` join + `ilike` filter on both count and page queries; code review patch: `Assignment.id` added as a secondary `ORDER BY` sort key for pagination stability
- `backend/app/assignments/service.py` — `AssignmentsService.list_assignments_for_hr` passes `search` through
- `backend/app/dashboard/router.py` — `GET /api/dashboard` gains `search: str | None = Query(None, max_length=200)`, trimmed/blank-to-`None` before calling the service
- `backend/app/dashboard/service.py` — `DashboardService.get_dashboard_assignments` gains `search` param, passed through to `AssignmentsService`
- `backend/tests/test_dashboard_router.py` — 4 new tests under a new "Story 10.6" section (employee-name match, skill-name match + non-matching-row exclusion, pagination-count-reflects-filtered-total, blank-search-is-a-no-op); code review patch: `_create_throwaway_employee_for_search`'s `last_name` now carries a random hex suffix
- `frontend/src/lib/api/dashboardApi.ts` — `getDashboard` gains an optional third `search` param; code review patch: `pageSize` default corrected from 50 to 15
- `frontend/src/features/dashboard/DashboardPage.tsx` — `DashboardState.search`; `pageSize` default 50→15; `handleSearchChange`; debounce effect gains `state.search`; shared `toolbar` (button + search input) replaces 4x-duplicated inline toolbar markup; Empty-state message split (search vs. genuinely-empty); code review patch: added `searchRef` + a lightweight sync effect so the poll-lifecycle effect no longer depends on `state.search` directly (`pollDashboard` reads `searchRef.current`), fixing a keystroke-triggered poll-interval restart bug; code review patch: `maxLength={200}` on the search input
- `frontend/src/features/dashboard/DashboardPage.test.tsx` — 6 new tests under a new "Story 10.6" `describe` block
- `frontend/src/features/dashboard/DashboardPage.polling.test.tsx` — 2 new tests: the poll-interval-restart regression test (verified RED against the pre-patch code, reproducing the exact bug, then GREEN) and a poll-carries-current-search-term test
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — `10-6-skill-assignments-grid-search-and-pagination`: `backlog` → `in-progress` → `review` → `done`
- `_bmad-output/implementation-artifacts/deferred-work.md` — code review: 7 findings logged under a new `10-6-skill-assignments-grid-search-and-pagination` heading

No changes to:
- Any database migration/schema file — no new column or table
- `ProvenanceDrillDownModal.tsx`, `DeleteAssignmentModal.tsx`, `DashboardRow.tsx` — row-level behavior (AC2) untouched
- `progress/` module — Status/Provenance derivation (AD-3) untouched

## Change Log

- 2026-09-18: Story started directly (`bmad-agent-dev`/Amelia, at the user's explicit request to start API + UI implementation for Story 10.6, referencing CLAUDE.md and the UX design) — no `bmad-create-story` pass ran first, matching Story 10.4's precedent. Before writing code, surfaced via `AskUserQuestion` that this story's own "same pattern as Story 10.5" AC instruction conflicts with the Skill Assignments grid's existing real server-side pagination (unlike Skills/Employees); user chose server-side search over a literal client-side mirror. Story file authored alongside implementation.
- 2026-09-18: Implementation complete (`bmad-agent-dev`/Amelia, TDD: RED confirmed via `git stash`/re-run for both backend and frontend new-test suites, then GREEN). Backend: `search` query param on `GET /api/dashboard`, threaded through `dashboard/service.py` → `assignments/service.py` → `assignments/repository.py`, ILIKE-matching Employee/Skill name, applied to both count and page queries. Frontend: 15/page default, debounced search input, poll/fetch effects search-aware, a structural fix (shared `toolbar` element) to prevent a real focus-loss bug during debounced re-fetches. Full regression green both sides (backend 738/738, frontend 450/450), `tsc`/`vite build` unchanged from baseline. Live-verified end-to-end: backend via `curl` against the real app + DB, frontend via a throwaway Playwright script (screenshots confirmed search/clear/no-match all work correctly, including focus retention) since `chromium-cli` wasn't available in this environment. Docker's `talentpilot-api`/`talentpilot-ui` were stopped for local dev-server verification and restarted afterward. Status → `review`.
- 2026-09-18: Code-reviewed via `bmad-code-review` (3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 0 decision-needed, 5 patches applied, 7 deferred, 8 dismissed. Most significant patch: the frontend's live-poll `useEffect` had `state.search` in its dependency array, so it tore down/restarted the 12s `setInterval` on every keystroke — a continuously-typing admin could indefinitely defer live updates. Fixed via a `searchRef` (kept current by a separate lightweight effect) that `pollDashboard` reads instead of closing over `state.search`; verified with a genuine RED/GREEN cycle (reintroduced the bug, confirmed the new regression test caught it — 7 `setInterval` calls instead of 2 — then restored the fix). Other patches: `dashboardApi.ts`'s stale `pageSize=50` default corrected to 15; a secondary `Assignment.id` sort key added to stabilize pagination ordering; a random suffix added to a test fixture's `last_name` to close a rare cross-run flakiness window; `maxLength={200}` added to the search input to match the backend's validation bound. Full regression re-verified after patches: backend 738/738 passed, frontend 452/452 passed (450 + 2 new poll-regression tests), `tsc` unchanged at the 31-error baseline, `vite build` clean at 538 modules. 7 deferred items logged in `deferred-work.md` (mostly pre-existing patterns already accepted elsewhere in this codebase — unescaped ILIKE wildcards, placeholder-only search-input labeling, missing debounce trim — plus a few low-value test-coverage gaps). Status → `done`.
