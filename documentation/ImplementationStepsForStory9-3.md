# Implementation Steps for Story 9-3: Frontend Skill Assignment Dashboard Landing Page

**Story Key:** 9-3-frontend-skill-assignment-dashboard-landing-page
**Epic:** 9 (Skill Assignment Dashboard) — 3 of 5 stories
**Status:** ✅ DONE (code-reviewed; not yet committed to git)
**Completed Date:** 2026-09-13

---

## Overview

Story 9.3 builds the Skill Assignment Dashboard landing page (FR-31, FR-32 display, UX-DR44) — the new org-wide "how are we doing" page an HR Admin sees at `/dashboard`: three top-line stats, an Assignment Progress ring, and an Employee Segmentation pie chart, with the pie chart deliberately the visually larger, primary element on the page.

The kickoff instruction asked for "both API and UI." Unlike Stories 9.1/9.2, both backend endpoints this page consumes (`GET /api/dashboard/stats`, `GET /api/dashboard/segmentation`) were **already shipped and `done`** — so this story turned out to be genuinely frontend-only, with zero backend code added. No story file existed yet for 9.3 (only 9.1/9.2 had been created), so this session ran `bmad-create-story` first, then `bmad-dev-story`, then `bmad-code-review`, all in one continuous pass.

Two real judgment calls were found and resolved during story creation, both documented in the story file rather than guessed at silently:

1. **A genuine scope tension in `epics.md` itself.** Story 9.3's own AC1 text describes the fully-wired end state ("click Dashboard in the left nav... lands on the new page"), but `epics.md`'s own Story 9.5 AC and its "Recommended build order" note both explicitly claim that exact nav-repoint as Story 9.5's job, sequenced *after* 9.3 ("Story 9.5 (nav shell) last, since it repoints 'Dashboard' to Story 9.3's page, which must exist first"). Resolved by scoping this story to a real, directly-navigable `/dashboard` route, deliberately not touching `HrAppShell.tsx`'s nav wiring — verified this story's own AC1 via direct navigation, not a nav click.
2. **A real drift between two design artifacts.** The UX spec's own written "Typography Tokens" table (`06.1-skill-assignment-dashboard.md`) specifies 20px/24px for the Progress/Segmentation headings; its companion Phase-5 prototype HTML uses 18px/20px instead. Resolved in favor of the written spec, the canonical Phase 4 deliverable.

A third open question (the Empty-state CTA's exact link target, since this codebase's real assignment-creation flow is a modal with no standalone route) was deliberately left for implementation time and resolved there by grepping every `AssignmentModal` usage in the codebase.

A real, unanticipated **deployment gap** — not a code defect — was found during live verification: both `talentpilot-api` and `talentpilot-ui` Docker containers were running images stale relative to `HEAD`, silently 404ing on Story 9.2's already-shipped `/segmentation` endpoint until both images were rebuilt.

Code review then found a real, spec-verified defect the story's own authoring had introduced: the Empty state's own Scope Note had silently paraphrased away the UX spec's literal "Stats show zeros" instruction, causing the implementation to drop the stats row entirely in the Empty state instead of keeping it visible alongside the swapped-out message.

---

## Agents Invoked

### 1. Blind Hunter (`bmad-review-adversarial-general` skill, background subagent)

**Purpose:** Open-ended adversarial critique of the finished diff — no spec context, no priors.

**When Invoked:** Part of `bmad-code-review`'s 3-parallel-layer step, once the story reached `review` status.

**Key Findings Identified:** Raised that `extractErrorMessage` might assume the wrong error-envelope key (`message` vs. a more conventional `detail`) with no test locking in the real path; that the six chart-fill hex colors were duplicated as inline literals with no single source of truth; that `EmployeeSegmentationResponse.needs_attention`'s full list is fetched but entirely unused by this page; and roughly a dozen other observations (untested `App.tsx` route wiring, an implementation-detail heading-class test, no frontend role-gate test, CTA-link-target ambiguity, tracking-doc narrative triplication, Retry-button double-click, and others) — each investigated individually rather than accepted at face value.

### 2. Edge Case Hunter (`bmad-review-edge-case-hunter` skill, background subagent)

**Purpose:** Method-driven walk of every branching path and boundary condition — orthogonal to Blind Hunter's attitude-driven pass.

**When Invoked:** Same trigger, launched in parallel with Blind Hunter and the Acceptance Auditor.

**Key Findings Identified:** Raised a set of defensive-coding gaps — an unmount-during-fetch `setState` risk, no timeout for an indefinitely-pending request, `conicGradient`/`isEmpty` having no guard against negative/NaN/undefined backend fields, `overall_percent` rendered without client-side rounding/clamping, and `extractErrorMessage` silently falling back on an empty-string message. Each was checked against this codebase's actual established conventions before being triaged.

### 3. Acceptance Auditor (custom prompt, background subagent)

**Purpose:** Cross-check the diff against the story's own ACs, Scope Notes, and Tasks — and, critically, against the UX design spec the story cites as its source.

**When Invoked:** Same trigger, full review mode against the story file as spec, with the UX spec file also loaded as additional context.

**Key Findings Identified:** This audit's **single most consequential finding of the whole review**: the Empty state was dropping the entire top-line stats row, directly contradicting `06.1-skill-assignment-dashboard.md`'s own literal Page States instruction ("Stats show zeros; ring/pie chart area replaced with..."). The auditor traced this precisely to the story's own Scope Note 9, which had paraphrased that clause away during authoring — a genuine implementation-matches-story-but-not-spec gap. Everything else audited (the 9.3/9.5 nav boundary, every other Scope Note, every Object ID, the Dev Agent Record's factual test-count/`tsc` claims) was independently re-verified and confirmed compliant — including re-running the actual test suite and `tsc --noEmit` itself rather than trusting the story file's own claims.

---

## Skills Invoked

### 1. `bmad-agent-dev` (Amelia persona activation)

**Purpose:** Activate the Senior Software Engineer persona for test-first implementation.

**When Invoked:** `start implementation for both API and UI for the story 9-3-frontend-skill-assignment-dashboard-landing-pag, if required refer the UX design`. Sprint status showed 9.3 as `backlog` (no story file yet, unlike 9.1/9.2 which were already `done`) — dispatched straight to `bmad-create-story` first, matching this project's own established same-session create-then-dev precedent.

### 2. `bmad-create-story`

**Purpose:** Produce a comprehensive, implementation-ready story file for 9.3, since none existed yet.

**When Invoked:** Immediately on recognizing Story 9.3 had no story file, before any implementation work began.

**Workflow Steps Executed:**
1. Loaded Epic 9's Story 9.3 AC text and Epic 9's overview/dependencies from `epics.md`, plus Stories 9.4/9.5's AC text and the epic's own "Recommended build order" note (needed to resolve the 9.3/9.5 nav-scope tension).
2. Located and fully read the UX design spec — `_bmad-output/C-UX-Scenarios/06-ritas-pulse-check/06.1-skill-assignment-dashboard/06.1-skill-assignment-dashboard.md` (Page Basics, Layout Sections, every Object ID table, Interactions, Page States, Spacing/Typography tokens, Accessibility Requirements) — plus its companion Phase-5 prototype (`06.1-Skill-Assignment-Dashboard.html`), diffing the two and catching their typography discrepancy.
3. Read both already-`done` backend story files (9.1, 9.2) in full for their exact response contracts, then verified those contracts directly against the live `backend/app/dashboard/schemas.py`/`router.py` rather than trusting the story files' prose alone.
4. Read the current frontend's real routing/nav/page-shape conventions directly: `App.tsx`, `HrAppShell.tsx` (confirming its 3-link `NAV_LINKS`, still pointing "Dashboard" at `/hr/dashboard`), `EmployeesPage.tsx` (the page-shape precedent chosen), `DashboardPage.tsx` (the existing three-state precedent and footer-text convention), `dashboardApi.ts`, `types/dashboard.ts`, `client.ts`.
5. Wrote 15 numbered Scope Notes covering: the frontend-only scope confirmation; exact response shapes to mirror verbatim; the two new API-client methods to add; the new `/dashboard` route (not `/hr/dashboard`); the critical 9.3/9.5 nav-wiring scope boundary (with a full explanation of the epics.md-internal tension and how to defend against a future reviewer flagging it); reusing `HrAppShell` unmodified; the single-file page-shape precedent to follow; the `extractErrorMessage` helper to copy verbatim; the four Page States and their exact trigger conditions/copy; the visual-hierarchy typography/layout resolution (with the prototype-vs-spec discrepancy flagged); the `conicGradient` charting approach (no library) with exact hex values; the deliberate non-interactive Needs Attention row; accessibility requirements; route registration; and the confirmed-dead files to leave untouched.
6. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `9-3-...` entry updated `backlog` → `ready-for-dev`.

**Output File:** `_bmad-output/implementation-artifacts/9-3-frontend-skill-assignment-dashboard-landing-page.md`
**Sprint Status:** `9-3-...`: `backlog` → `ready-for-dev`

---

### 3. `bmad-dev-story` (implementation, Amelia persona)

**Purpose:** Execute the story's 6 tasks in sequence: types, API client, page component, route, tests, regression.

**When Invoked:** Immediately after the story file was created and marked `ready-for-dev`.

**Workflow Steps Executed:**
1. **Task 1 — Types:** `DashboardStatsResponse`, `NeedsAttentionEntry`, `EmployeeSegmentationResponse` added to `frontend/src/types/dashboard.ts`, field-for-field identical (snake_case) to the live backend Pydantic schemas.
2. **Task 2 — API client:** `getDashboardStats()`/`getEmployeeSegmentation()` added to the existing `dashboardApi` object in `frontend/src/lib/api/dashboardApi.ts`, mirroring `getDashboard`'s exact `apiClient.get<T>(url)` shape.
3. **Task 3 — Page component:** New `frontend/src/pages/hr/SkillAssignmentDashboard.tsx`, modeled on `EmployeesPage.tsx`'s fetch/error/race-guard shape — `HrAppShell`-wrapped, parallel `Promise.all` fetch with a `requestIdRef` race-guard, all four UX-spec Page States (Loading/Error+Retry/Empty+CTA/Loaded), a locally-scoped `conicGradient` helper ported from the Phase-5 prototype (no chart library added) for the Progress Ring and Segmentation Pie, and the Needs Attention legend row rendered as permanently non-interactive plain text (Story 9.4's job to add the click/popover layer).
4. **Task 4 — Route:** `/dashboard` registered in `frontend/src/App.tsx`, `RequireAuth`-wrapped, identical to every other protected route; `/hr/dashboard` and every existing route left untouched (diff-verified).
5. **Task 5 — Tests:** New `frontend/src/tests/SkillAssignmentDashboard.test.tsx` — loaded state (all stat/ring/legend values), Needs Attention non-interactivity, visual-hierarchy heading classes, both empty triggers (zero Employees, zero Assignments), error+retry. One originally-planned subtask (a stale-response race-guard test) was **investigated and deliberately dropped, not faked**: this page's only second-fetch trigger (Retry) is unreachable until the first request has already settled, so the classic race the guard defends against can't actually be exercised through the real UI — writing a "passing" test that didn't genuinely exercise the guard would have been false coverage.
6. **Task 6 — Regression:** `vitest run` → 411/411 (404 baseline + 7 new); `tsc --noEmit` → 31 pre-existing errors, unchanged, none in new/modified files; `vite build` → clean, 537 modules.
7. **Live verification (beyond the task checklist, done anyway per this project's UI-change convention):** Playwright (Chromium, installed ad hoc, removed after use) against Docker containers. First pass surfaced a real, unanticipated **environment gap**: both `talentpilot-api` and `talentpilot-ui` images were stale relative to `HEAD`, so `/api/dashboard/segmentation` 404'd even though Story 9.2's route existed in the checked-out code. Fixed by `docker compose build backend frontend && docker compose up -d backend frontend` — not a code change, recorded in Dev Notes so it wasn't mistaken for a Story 9.2 regression. After rebuilding: HR Admin login → `/dashboard` rendered live org data (5 Employees, 6 Assignments) correctly in both light and dark theme (screenshots captured); a non-HR-Admin (Employee) session hitting `/dashboard` cleanly showed the Error state with the backend's real 403 message via Retry, confirming the deliberate no-frontend-role-gate design decision works end-to-end.
8. Story's Dev Agent Record, Completion Notes, and File List filled in; Status → `review`.

**Output Files:**
- `frontend/src/types/dashboard.ts`, `frontend/src/lib/api/dashboardApi.ts`, `frontend/src/App.tsx` (modified)
- `frontend/src/pages/hr/SkillAssignmentDashboard.tsx`, `frontend/src/tests/SkillAssignmentDashboard.test.tsx` (new)
- `_bmad-output/implementation-artifacts/9-3-frontend-skill-assignment-dashboard-landing-page.md`

**Sprint Status:** `9-3-...`: `ready-for-dev` → `in-progress` → `review`

---

### 4. `bmad-code-review` (3-layer adversarial review + patch application)

**Purpose:** Independent adversarial verification of the finished implementation, followed by resolving every finding.

**When Invoked:** User explicitly asked to run code review immediately after implementation completed (offered via `AskUserQuestion`, chosen: "Run code review now").

**Workflow Steps Executed:**
- Constructed the diff against uncommitted working-tree changes (5 modified + 3 new files — since 2 of the 3 new files are untracked, built via a combined `git diff HEAD` + `git diff --no-index /dev/null <file>` for each, 673 diff lines total), confirmed scope with the user via `AskUserQuestion`.
- Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor in parallel as background subagents, the Acceptance Auditor also given the UX design spec as additional loaded context.
- Normalized and deduplicated the three layers' raw findings, then **read the actual code and the cited UX spec line before rating each one** — including grepping `backend/app/core/errors.py` directly to settle the "message vs. detail" envelope-key question, and re-running the flagged "loading state" test in isolation to check for a claimed extra `act()` warning (none appeared).
- Triaged into: **0 decision-needed, 3 patch, 1 defer, ~14 dismiss.**
- **User chose to apply all 3 patches** (option 1: "apply every patch, no per-finding confirmation"):
  1. **Empty state restructured** so the stats row renders unconditionally whenever data has loaded, with the Empty message and the Progress/Segmentation grid as mutually-exclusive siblings beneath it (previously nested inside one another) — `dashboard-state-loaded`'s testid now denotes specifically the non-empty grid, matching the UX spec's literal state model.
  2. **Added a test** rejecting with this app's actual centralized error-envelope shape (`{ response: { data: { message: ... } } }`), locking in the real backend-message extraction path the Completion Notes had claimed was live-verified but no test protected.
  3. **Extracted the six chart-fill hex colors** to one `CHART_COLORS` module-level constant, referenced from every ring/pie/legend call site.
- **Deferred 1 finding** to `deferred-work.md`: `EmployeeSegmentationResponse.needs_attention`'s full flagged-Assignment list is fetched on every page load but entirely unused by this story (only the count is read) — an unavoidable consequence of Story 9.2's existing single-endpoint response shape, extending that story's own already-logged unbounded-list-growth deferral.
- **Dismissed ~14 findings after verification**, each checked rather than waved off: the "message vs. detail" envelope-key concern was verified false by reading `backend/app/core/errors.py` directly (confirmed `"message"` is always the key) and was already independently proven correct by this story's own live Playwright session; ~13 others each matched an already-established, already-accepted codebase-wide pattern (identical to `EmployeesPage.tsx`'s own conventions, this codebase's total absence of runtime API-response validation, the backend's own server-side rounding guarantee, the already-documented 9.3/9.5 nav-sequencing decision, this project's own established triple-narrative documentation convention, etc.) — verified by direct grep/read in each case, not assumed.
- Re-ran the full frontend suite — **412 passed** (404 baseline + 8, up from 7 after the patch's added test), zero regressions. `tsc --noEmit` unchanged at 31 pre-existing errors. `vite build` clean.
- Rebuilt the Docker frontend image and re-verified live via Playwright: the Loaded state renders identically and correctly after the restructuring.
- Story Status → `done`; `sprint-status.yaml` synced; `project-context.md` updated per this project's own established rule that no story reaches `done` without a matching entry there.

**Output:** Story file's "### Review Findings" subsection (3 checked-off patches with inline "Fixed:" notes, 1 checked-off deferred item, ~14 dismissed noted in prose); `deferred-work.md` gained a new "Deferred from: code review of 9-3-..." section.

**Documentation Generated:**
- The story file's Review Findings section, Change Log, and Status field
- `deferred-work.md`'s new Story 9.3 section
- Sprint status synced (`9-3-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`; `epic-9` remains `in-progress`, since Stories 9.4/9.5 are still `backlog`)
- Two `project-context.md` entries (implementation completion, then code-review completion)

---

## Files Created/Updated

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/types/dashboard.ts` | `DashboardStatsResponse`, `NeedsAttentionEntry`, `EmployeeSegmentationResponse` added — snake_case, field-for-field matching the live backend Pydantic schemas |
| `frontend/src/lib/api/dashboardApi.ts` | `getDashboardStats()`/`getEmployeeSegmentation()` added to the existing `dashboardApi` object |
| `frontend/src/App.tsx` | New `/dashboard` route registered, `RequireAuth`-wrapped |

### Frontend — New Files

| File | Purpose |
|------|---------|
| `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` | The Skill Assignment Dashboard landing page — Loading/Error+Retry/Empty+CTA/Loaded states, `conicGradient`-based Progress Ring + Employee Segmentation Pie, non-interactive Needs Attention row, `CHART_COLORS` constant (code review patch) |
| `frontend/src/tests/SkillAssignmentDashboard.test.tsx` | 8 tests (7 original + 1 added by code review: real-backend-error-message extraction; the Empty-state test was also strengthened to assert stats-row/ring/segmentation presence) |

### Planning/Tracking — Modified Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `9-3-...` progressed `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | New "Deferred from: code review of 9-3-..." section, 1 entry |
| `_bmad-output/project-context.md` | Two entries appended (implementation completion, then code-review completion), per this project's own established "no story reaches `done` without a matching entry here" rule |

### Documentation Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/9-3-frontend-skill-assignment-dashboard-landing-page.md` | Story file — 4 ACs, 15 Scope Notes, Dev Notes, Dev Agent Record, Review Findings section |
| `documentation/ImplementationStepsForStory9-3.md` | This file |

### Not Changed (by design)

- Any backend file (`backend/`) — both consumed endpoints (Stories 9.1/9.2) already existed, confirmed directly against the live code before writing the story
- `frontend/src/components/layout/HrAppShell.tsx` — nav wiring is Story 9.5's explicitly-claimed scope, deliberately untouched here
- `frontend/src/pages/hr/Dashboard.tsx`, `frontend/src/features/dashboard/DashboardPage.tsx`, the `/hr/dashboard` route — the existing full-grid page, untouched
- `frontend/src/pages/hr/DashboardStub.tsx`, `frontend/src/features/dashboard/AssignmentsList.tsx`, `frontend/src/features/dashboard/DashboardRow.tsx` — confirmed dead code, out of scope

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `bmad-create-story`
- Read the full UX design spec and its companion prototype directly (catching their typography discrepancy), both already-`done` backend stories' files plus the live backend schema/router code, and the current frontend's real routing/nav/page-shape conventions
- Resolved a real epics.md-internal scope tension (9.3 vs. 9.5's nav-wiring ownership) before it could become a mid-implementation surprise
- 15 numbered Scope Notes written, including the nav-boundary reasoning and the visual-hierarchy/typography resolution
- Status → `ready-for-dev`

### Phase 2: Implementation
**Execution:** Amelia persona, frontend-only (confirmed both consumed endpoints already `done`)
- 6 tasks executed in sequence: types → API client → page component → route → tests → full regression
- One test-design gap self-caught and deliberately left undone rather than faked (the race-guard test)
- A real deployment gap found and fixed during live verification (stale Docker images), not a code defect
- Full regression: 411 passed (404 baseline + 7 new), zero regressions; live-verified in both light/dark theme and against a non-HR-Admin session
- Story marked `review`

### Phase 3: Code Review + Patches
**Skill:** `bmad-code-review`
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor — the auditor also given the UX spec) against the uncommitted diff
- 18 unique findings after triage: 0 decision-needed, 3 patched, 1 deferred, ~14 dismissed after direct verification (including grepping the backend's actual error handler to settle one claim)
- The most consequential finding was a genuine spec-compliance gap the story's own authoring had introduced (Empty state dropping the stats row) — caught by tracing the implementation back to the UX spec's literal wording, not just the story file's own paraphrase of it
- Full regression re-verified after patches: 412 passed (404 baseline + 8, up from 7), zero regressions
- Story marked `done`

---

## Test Coverage

### New/Extended Test Files

- `SkillAssignmentDashboard.test.tsx` — 8 tests:
  - `shows the loading state before data resolves`
  - `renders stats, progress ring, and segmentation once both requests resolve (AC1, AC4)`
  - `renders the Needs Attention row as plain, non-interactive text regardless of count (Story 9.4 scope, not this story)`
  - `applies a visibly larger heading token to the Segmentation card than the Progress Ring card (AC2, UX-DR44)`
  - `shows the Empty state when there are zero active Employees, while still showing the stats row with zeros (AC3, UX spec Page States)` (strengthened by code review patch)
  - `shows the Empty state when there are zero active Assignments (AC3)`
  - `shows the backend's real error message when the rejection carries one (matches this app's centralized error envelope)` (code review patch)
  - `shows the Error state with Retry when a request fails, and Retry re-fetches (AC3)`

### Regression Verification

- Frontend: 404 → 411 (implementation) → 412 (code review patch) passed, 0 failed throughout
- `tsc --noEmit`: 31 pre-existing errors at every checkpoint, none in this story's files
- `vite build`: clean at every checkpoint (536 → 537 modules)
- Live verification (Playwright, installed ad hoc, removed after use, against rebuilt Docker containers): HR Admin login → real data in light/dark theme; Employee session → clean Error state with the real 403 message

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **Frontend-only scope** | Both consumed endpoints (Stories 9.1/9.2) verified `done` directly against live backend code before any implementation began; zero backend files touched | (verification only, no backend files) |
| **9.3/9.5 nav-wiring scope boundary** | New `/dashboard` route added and directly navigable; `HrAppShell.tsx`'s `NAV_LINKS` and the "Dashboard" link's target deliberately left unchanged — confirmed via `git diff` | `frontend/src/App.tsx` (added), `frontend/src/components/layout/HrAppShell.tsx` (untouched) |
| **AC1: never re-derive backend data** | Every displayed number comes directly from `DashboardStatsResponse`/`EmployeeSegmentationResponse`, verbatim — no client-side Status/Provenance/segmentation logic | `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` |
| **AC2/UX-DR44: visual hierarchy** | Segmentation card `border-2` + `text-2xl` heading vs. Progress Ring's plain border + `text-xl` heading; `grid-cols-[1fr_1.5fr]` layout ratio | `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` |
| **AC3: three-state discipline, spec-literal Empty state** | Loading/Error+Retry/Empty+CTA/Loaded, with the Empty state keeping the stats row visible (code review patch) rather than replacing the whole content area | `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` |
| **AC4/NFR-A2: never color-only** | Every stat/ring segment/pie segment carries a text label with its number via the shared `LegendRow` component | `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` |
| **Story 9.4 scope boundary** | Needs Attention rendered as a permanently non-interactive `LegendRow` — no button, no `aria-expanded`, no popover markup | `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` |

---

## Key Technical Achievements

✅ **Ran the full create → implement → review → patch pipeline in one continuous session**, correctly identifying that both consumed backend endpoints were already done and scoping this story as frontend-only from the outset
✅ **Resolved a real epics.md-internal scope tension before it caused rework** — Story 9.3's own AC1 text vs. Story 9.5's explicit claim to the nav-repoint, settled by scoping to a directly-navigable route and documenting the reasoning inline
✅ **Caught a real cross-artifact drift** (UX spec's written typography tokens vs. its own prototype HTML) and resolved it in favor of the canonical written spec
✅ **Found and fixed a real deployment gap during live verification**, not a code defect — stale Docker images silently masking an already-shipped backend endpoint — and correctly distinguished it from a Story 9.2 regression
✅ **Declined to fake a test** — investigated a planned race-guard test, found it wasn't genuinely exercisable through this page's real UI, and documented the honest reason for dropping it rather than writing a test that would pass without proving anything
✅ **Code review caught a genuine spec-compliance gap this story's own authoring introduced** — the Acceptance Auditor traced an Empty-state implementation choice back to the UX spec's literal wording and found the story's own Scope Note had silently paraphrased away a requirement
✅ **One claimed defect verified false against ground truth, not argued away** — Blind Hunter's "message vs. detail" envelope-key concern was settled by reading `backend/app/core/errors.py` directly
✅ **Zero regressions across every regression run in the session** — 404 → 411 → 412, with the same 31 pre-existing `tsc` errors at every checkpoint

---

## Deferred Items (Not Story 9-3 Scope)

From this story's own code review, logged in `deferred-work.md`:
- **`EmployeeSegmentationResponse.needs_attention`'s full flagged-Assignment list is fetched on every `/dashboard` load but entirely unused by this story** — only `needs_attention_count` is read. Extends Story 9.2's own already-logged deferral about the list's unbounded growth; not fixable without a backend change, which is out of this story's frontend-only scope. Revisit once Story 9.4 (the actual consumer) ships and real roster size is known.

Carried forward from earlier epics, unaffected by this story:
- `auth/repository.py::authenticate()` still does not read `Account` (Epic 7's own flagged gap) — irrelevant to this story's frontend display scope.

---

## Conclusion

Story 9-3 is **✅ DONE** after a full create-then-implement-then-review-and-patch cycle, run start to finish in one session:

- All 4 acceptance criteria satisfied — org-wide stats/ring/pie chart rendered from live backend data with no re-derivation, the pie chart visually larger/more prominent than the ring, the full Loading/Error/Empty/Loaded state set (with the Empty state correctly keeping stats visible after the code-review patch), and text/number labeling on every segment — verified by 8 dedicated frontend tests plus a full 412-test regression pass, both before and after the code-review patches, and live-verified against rebuilt Docker containers in both light/dark theme
- Code review surfaced 18 findings: 0 requiring a human decision, 3 patched (the most consequential being a genuine spec-compliance gap, not a code defect), 1 correctly deferred as an extension of Story 9.2's own already-accepted debt, and ~14 dismissed after direct verification (including one settled by reading the backend's actual error-handling code)
- Zero regressions across every regression run in the session (404 → 411 → 412 passed)
- **Not yet committed to git** — working tree still uncommitted as of this document, on top of `HEAD` at `9072ac70` ("Story 9.2: Backend Employee Segmentation endpoint (FR-32/AR-27/AR-28)")

**Epic 9 status:** `in-progress`. Stories 9.1, 9.2, and 9.3 are `done`; Story 9.4 (Frontend: Needs Attention Popover & Drill-Down) and Story 9.5 (Frontend: Nav Shell — Add "Skill Assignments" Entry) remain `backlog`.
