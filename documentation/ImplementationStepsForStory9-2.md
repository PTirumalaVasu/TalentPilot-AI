# Implementation Steps for Story 9-2: Backend Employee Segmentation Endpoint

**Story Key:** 9-2-backend-employee-segmentation-endpoint
**Epic:** 9 (Skill Assignment Dashboard) — 2 of 5 stories
**Status:** ✅ DONE (code-reviewed; not yet committed to git)
**Completed Date:** 2026-09-13

---

## Overview

Story 9.2 adds `GET /api/dashboard/segmentation`, the backend endpoint behind the Skill Assignment Dashboard landing page's Employee Segmentation pie chart (FR-32, AR-27, AR-28): every active Employee with at least one active Assignment is classified into exactly one of three buckets — **Needs Attention**, **On Track**, or **In Progress** — using a fixed priority order, not independent per-bucket checks.

The kickoff instruction asked for "both API and UI." `epics.md` scopes Story 9.2 as backend-only (the pie chart itself is Story 9.3), so the user was asked to confirm scope via `AskUserQuestion` and chose **"Backend 9.2 only (Recommended)"** — the same backend-only pattern Story 9.1 followed.

Like Story 9.1, this is a **read-composition** exercise, not a new-table feature (AR-26): it reuses Story 9.1's exact org-wide read (`list_assignments_for_dashboard`), archived-Employee filter, and override batch-load, adding exactly one new step — grouping that same already-fetched Assignment list by Employee. AR-27 explicitly calls this out as "the first per-Employee, full-roster aggregation read in this project," requiring a recorded query-plan check before the story could be marked done; that check confirmed **zero new SQL queries** are introduced (the grouping is pure in-memory work) and recorded the live dev DB's actual scale (5 active Employees, 6 active Assignments).

Two real design decisions, not directly prescribed by the epic AC, were made and documented during story authoring:

1. **`ON_TRACK_THRESHOLD = 0.8`** (AR-28's required named constant) was placed in `dashboard/service.py`, not `progress/service.py` — segmentation is a dashboard-owned aggregation, not part of `progress/`'s AD-3 per-Assignment Status/Provenance derivation authority — mirroring the existing `NEEDS_ATTENTION_STALENESS_DAYS` precedent's comment style and explicitly citing PRD Open Question 20 as the threshold's not-yet-user-confirmed status.
2. The **Needs Attention detail list is one entry per flagged *Assignment*, not one per Employee** — an Employee with more than one stale Assignment produces more than one entry, avoiding silent data loss. `needs_attention_count` in the response is a *separately computed* distinct-Employee count (matching the pie chart's segment size), explicitly documented so it is never conflated with the list's row count.

A real, non-obvious test-design problem was found and solved during implementation: unlike Story 9.1's org-wide count-delta tests, segmentation bucket membership is a function of an Employee's **entire** active-Assignment set — the seeded demo Employees (Casey/Morgan/Rita) could not be reused for bucket-membership assertions, since their other Assignments from unrelated tests in this shared dev DB would make the resulting bucket unpredictable. This was solved by creating a dedicated throwaway Employee per test scenario, extending Story 9.1's own archived-Employee-test precedent to every new test in this story.

This session ran story creation, TDD implementation, and a 3-layer adversarial code review with patch application, all in one continuous pass — the same pipeline shape as Story 9.1.

---

## Agents Invoked

### 1. Backend research subagent (1, `Explore` type, story-creation phase)

**Purpose:** Exhaustively analyze the exact code Story 9.2 would extend — `progress/service.py`'s derivation authority, `dashboard/service.py`'s Story 9.1 composition pattern, `dashboard/schemas.py`/`router.py`'s conventions, `employees/repository.py`, and the existing test fixtures — before writing the story file.

**When Invoked:** Immediately after `bmad-create-story` was launched for 9.2, in place of running the same searches manually.

**Key Findings Identified:** Confirmed `NEEDS_ATTENTION_STALENESS_DAYS`'s exact constant-placement precedent (a plain module-level constant, not a `Settings` field) to mirror for `ON_TRACK_THRESHOLD`; confirmed `get_provenance_detail`'s exact return shape (`ProvenanceDetail.provenance`/`.status`) and that an active HR Override's `provenance` is always `"HR Override"`, never `"Needs Attention"`; confirmed `get_dashboard_stats`'s exact composition pattern (`list_assignments_for_dashboard` → archived-Employee filter → `_batch_load_overrides` → `_compute_status_and_provenance_from_data`) to extend rather than reinvent; confirmed `DashboardStatsResponse`'s plain-`BaseModel` (no `from_attributes`) schema style to mirror; confirmed the exact test fixtures/helpers in `test_dashboard_router.py` (`_client`, `_login`, `_cleanup_assignment(s)_for`, seeded IDs) to reuse.

### 2. Blind Hunter (`bmad-review-adversarial-general` skill, background subagent)

**Purpose:** Open-ended adversarial critique of the finished diff — no spec context, no priors.

**When Invoked:** Part of `bmad-code-review`'s 3-parallel-layer step, once the story reached `review` status.

**Key Findings Identified:** Raised, as the review's most consequential finding, that the story's own Dev Notes claimed the Needs-Attention/HR-Override interaction was "confirmed safe via direct code reading" but nothing actually tested it. Also flagged that `ON_TRACK_THRESHOLD`'s boundary was never tested cleanly (every existing test sat at 0%, 100%, or a case masked by a simultaneous override), that no test asserted the endpoint's no-side-effect/read-only guarantee, and an untyped `dict`. Raised several other points (duplicated expensive-read pattern between `/stats` and `/segmentation`, unbounded `needs_attention` list growth, cross-endpoint consistency) that were triaged as pre-existing-debt extensions rather than new defects.

### 3. Edge Case Hunter (`bmad-review-edge-case-hunter` skill, background subagent)

**Purpose:** Method-driven walk of every branching path and boundary condition — orthogonal to Blind Hunter's attitude-driven pass.

**When Invoked:** Same trigger, launched in parallel with Blind Hunter and the Acceptance Auditor.

**Key Findings Identified:** Raised a float-rounding risk at the exact `0.8` threshold, `None`-name crash risks for `employee_name`/`skill_name`, an override batch-load race condition, unbounded list growth, a possible duplicate-row risk from query "fan-out," and status/provenance literal-string comparison fragility. Three of these (float rounding, `None`-name crashes, duplicate rows) were investigated and empirically/structurally disproven rather than accepted at face value.

### 4. Acceptance Auditor (custom prompt, background subagent)

**Purpose:** Cross-check the diff against the story's own ACs, Scope Notes, and Tasks.

**When Invoked:** Same trigger, full review mode against the story file as spec.

**Key Findings Identified:** Confirmed no violations against AC1 (priority order), AC2 (constant placement/value/comment), AC3 (zero-Assignment/archived-Employee exclusion), AC4 (payload shape), or AC6 (401/403 gate). Flagged that AC5's required query-plan-check evidence technically lives outside the reviewed diff (the story file itself was untracked at review time) — confirmed to be a diff-scope artifact only, since the actual check was genuinely performed and recorded in that file. Flagged two cosmetic-only points (a docstring wording difference from `/stats`, undocumented-but-deterministic list ordering) that it self-assessed as non-functional.

---

## Skills Invoked

### 1. `bmad-agent-dev` (Amelia persona activation)

**Purpose:** Activate the Senior Software Engineer persona for test-first implementation.

**When Invoked:** `start implementation for both API and UI for the 9-2-backend-employee-segmentation-endpoint, if required refer the UX design`. Since Story 9.2 is scoped backend-only per `epics.md`, the user was asked to confirm scope via `AskUserQuestion` and chose **"Backend 9.2 only (Recommended)."**

### 2. `bmad-create-story`

**Purpose:** Produce a comprehensive, implementation-ready story file for 9.2, since none existed yet (only Story 9.1's file existed under Epic 9).

**When Invoked:** Immediately after the scope-confirmation question, before any implementation work began.

**Workflow Steps Executed:**
1. Loaded Epic 9's Story 9.2 AC text from `epics.md`, the PRD's FR-32 section (including PRD Open Question 20's not-yet-confirmed 80% threshold), and the relevant UX design decisions (UX-DR44 through UX-DR48 — no separate UX mockup file exists for this backend-only story, so the epics.md UX-DR bullets served as the design reference the user asked to consult).
2. Read Story 9.1's completed story file directly for continuity (dev notes, patterns established, module-ownership decisions).
3. Ran one research subagent to exhaustively analyze `progress/service.py`, `dashboard/service.py`, `dashboard/schemas.py`/`router.py`, `employees/repository.py`, and the existing test fixtures.
4. Independently verified several of that subagent's claims directly (reading `progress/service.py`'s `NEEDS_ATTENTION_STALENESS_DAYS`/`get_provenance_detail`, `dashboard/service.py`'s `get_dashboard_stats` in full, `dashboard/schemas.py`, `dashboard/router.py`, and `test_dashboard_router.py`'s existing Story 9.1 tests) before writing the story, rather than trusting the subagent's summary alone.
5. Wrote 11 numbered Scope Notes covering: backend-only scope; the exact new-route shape to mirror; the exact read-composition pattern to reuse (and not reinvent); the one genuinely new step (per-Employee grouping); the exact classification priority order; the `ON_TRACK_THRESHOLD` constant's placement/comment requirements; the Needs-Attention-list-is-per-Assignment design decision; the response schema style to mirror; the required AR-27 query-plan check; existing test fixtures to extend; and how to simulate a genuine "Needs Attention" Assignment in tests.
6. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `9-2-...` entry updated `backlog` → `ready-for-dev`.

**Output File:** `_bmad-output/implementation-artifacts/9-2-backend-employee-segmentation-endpoint.md`
**Sprint Status:** `9-2-...`: `backlog` → `ready-for-dev`

---

### 3. `bmad-dev-story` (TDD implementation, Amelia persona)

**Purpose:** Execute the story's 7 tasks in sequence: schemas, constant, service, router, query-plan check, tests, regression.

**When Invoked:** Immediately after the story file was created and marked `ready-for-dev`.

**Workflow Steps Executed:**
1. **Task 1 — Schemas:** `NeedsAttentionEntry` (`employee_id`/`employee_name`/`assignment_id`/`skill_id`/`skill_name`) and `EmployeeSegmentationResponse` (`on_track_count`/`in_progress_count`/`needs_attention_count`/`needs_attention`) added to `backend/app/dashboard/schemas.py`, both plain `BaseModel`s matching `DashboardStatsResponse`'s style.
2. **Task 2 — Constant:** `ON_TRACK_THRESHOLD = 0.8` added to `backend/app/dashboard/service.py`, with a comment citing PRD Open Question 20, mirroring `NEEDS_ATTENTION_STALENESS_DAYS`'s precedent.
3. **Task 3 — Service:** `DashboardService.get_employee_segmentation(session)` added — reuses `list_assignments_for_dashboard` + the same archived-Employee filter and override batch-load Story 9.1 introduced, groups the filtered Assignments by `employee_id`, then classifies each Employee via the exact priority order (Needs Attention overrides everything; else On Track if completion rate ≥ `ON_TRACK_THRESHOLD`; else In Progress).
4. **Task 4 — Router:** `GET /api/dashboard/segmentation` added to `backend/app/dashboard/router.py`, mirroring `/stats`'s exact `Depends(require_hr_admin)` + `Depends(get_db)` shape.
5. **Task 5 — AR-27 query-plan check:** Ran `SELECT COUNT(*)` against the live dev DB directly (5 active Employees, 6 active Assignments) and confirmed by code inspection that the new per-Employee grouping introduces zero additional SQL queries — recorded both facts in the story's Dev Notes.
6. **Task 6 — Tests, written first (RED before GREEN):** Wrote the structural service test and all 7 initial router tests (auth gate, On Track, In Progress catch-all, Needs-Attention-overrides-high-completion, zero-Assignment exclusion, archived-Employee exclusion) and confirmed every one failed for the expected reason (`AttributeError`/404) *before* writing any schema, constant, service, or router code.
7. Implemented schemas → constant → service → router in that order until all 8 tests passed. One test-only fix during GREEN: a wrong assumed seeded skill name ("Communication" vs. the real "Communication Skills").
8. **Task 7 — Regression:** Full backend suite run — 714 passed, 2 skipped (706 baseline + 8 new), zero regressions.
9. Story's Dev Agent Record, Completion Notes, and File List filled in; Status → `review`.

**Real test-design problem self-caught during implementation (not by review):**
- Segmentation bucket membership is a function of an Employee's *entire* active-Assignment set, so the seeded demo Employees couldn't be reused for bucket-membership assertions — their other Assignments from unrelated tests in this shared dev DB would make the resulting bucket unpredictable. Solved with a dedicated-throwaway-Employee-per-test-scenario pattern, extending Story 9.1's own archived-Employee-test precedent.
- HR Override (`POST /api/assignments/{id}/override`) was used as a lightweight way to force "Completed" status in tests, confirmed safe by directly reading `get_provenance_detail`'s override branch (an active override's provenance is always `"HR Override"`, never `"Needs Attention"`).

**Output Files:**
- `backend/app/dashboard/schemas.py`, `backend/app/dashboard/service.py`, `backend/app/dashboard/router.py` (modified)
- `backend/tests/test_dashboard.py`, `backend/tests/test_dashboard_router.py` (modified)
- `_bmad-output/implementation-artifacts/9-2-backend-employee-segmentation-endpoint.md`

**Sprint Status:** `9-2-...`: `ready-for-dev` → `in-progress` → `review`

---

### 4. `bmad-code-review` (3-layer adversarial review + patch application)

**Purpose:** Independent adversarial verification of the finished implementation, followed by resolving every finding.

**When Invoked:** `/bmad-code-review`, no argument. Since the conversation had just built Story 9.2, the target (uncommitted changes against `HEAD`, with the story file as spec context) was identified from recent conversation context (Tier 2 of the review workflow's target-discovery cascade), confirmed via `AskUserQuestion`.

**Workflow Steps Executed:**
- Constructed the diff against the uncommitted working-tree changes (7 files, 465 insertions / 6 deletions).
- Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor in parallel as background subagents, each given the full diff (and, for the Acceptance Auditor, the story file path as spec).
- Normalized and deduplicated the three layers' raw findings, then **read the actual code before rating each one** — including running a live Python check to empirically verify (or disprove) the claimed float-rounding risk, and grepping the `Employee`/`Skill`/`Assignment` model definitions to verify (or disprove) claimed null-crash and FK-nullability risks.
- Triaged into: **0 decision-needed, 4 patch, 3 defer, 11 dismiss.**
- **User chose to apply all 4 patches** (option 1: "apply every patch, no per-finding confirmation"):
  1. Added `test_employee_segmentation_override_clears_needs_attention_flag` — proves a genuinely stale Assignment that then gets HR-Overridden correctly clears the Employee's Needs Attention flag, the one interaction the Dev Notes had claimed was safe "via direct code reading" but never tested.
  2. Added `test_employee_segmentation_on_track_boundary_without_override` and `test_employee_segmentation_below_threshold_lands_in_progress` — exercise the `ON_TRACK_THRESHOLD` `>=` comparison itself at a natural 80% (no override) and a natural 75%, closing the gap where every prior test sat at 0%, 100%, or a threshold case masked by a simultaneous override.
  3. Added `test_employee_segmentation_never_triggers_content_reembed_write` — mocks `app.dashboard.service.match_content_for_skill` and asserts it is never called by `get_employee_segmentation`, proving the deliberately-omitted write-triggering fallback stays omitted.
  4. Typed `by_employee: dict = {}` as `dict[UUID, list[Assignment]]` (added `Assignment` to the existing `app.assignments.models` import).
- **Deferred 3 findings** to `deferred-work.md`, all extensions of Story 9.1's own already-accepted deferrals rather than new categories of debt: unbounded `needs_attention` list growth with no cap; cross-endpoint consistency between `/stats` and `/segmentation`; the two endpoints independently re-running the identical expensive read with no shared helper.
- **Dismissed 11 findings after verification**, several confirmed false rather than assumed: a claimed float-rounding risk at the exact 0.8 threshold, empirically disproven by running the actual comparisons in Python (every fraction mathematically equal to 0.8 rounds to the identical IEEE-754 double); claimed `None`-name crash risks, disproven against the actual schema (`Employee.name`/`Skill.name` are both `nullable=False`); a claimed join-fan-out duplicate-row risk, disproven by confirming `list_assignments_for_dashboard` uses `selectinload`, not `joinedload`; plus several design decisions (the `needs_attention_count`-vs-list-length distinction, the `sprint-status.yaml` `last_updated` convention, test-helper duplication matching an already-accepted pattern) confirmed to already be deliberate and documented, not defects.
- Re-ran the dashboard test files — 28/28 passed. Re-ran the full backend suite — **718 passed, 2 skipped** (714 + 4 new patch tests), zero regressions.
- Story Status → `done`; `sprint-status.yaml` synced; `project-context.md` updated per this project's own established rule that no story reaches `done` without a matching entry there.

**Output:** Story file's "### Review Findings" subsection (4 checked-off patches with inline "Fixed:" notes, 3 checked-off deferred items, 11 dismissed noted in prose); `deferred-work.md` gained a new "Deferred from: code review of 9-2-..." section with 3 entries.

**Documentation Generated:**
- The story file's Review Findings section, Change Log, and Status field
- `deferred-work.md`'s new Story 9.2 section
- Sprint status synced (`9-2-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`; `epic-9` remains `in-progress`, since Stories 9.3-9.5 are still `backlog`)
- Two `project-context.md` entries (implementation completion, then code-review completion)

---

## Files Created/Updated

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/dashboard/schemas.py` | `NeedsAttentionEntry` and `EmployeeSegmentationResponse` added — plain `BaseModel`s, no ORM passthrough, with explicit docstring on the `needs_attention_count`-vs-`len(needs_attention)` distinction |
| `backend/app/dashboard/service.py` | `ON_TRACK_THRESHOLD = 0.8` constant added; `DashboardService.get_employee_segmentation()` added — reuses Story 9.1's org-wide read/archived-Employee filter/override batch-load, adds a per-Employee groupby, classifies via the exact priority order; `Assignment` added to the existing model import and `by_employee` typed as `dict[UUID, list[Assignment]]` (code review patch) |
| `backend/app/dashboard/router.py` | `GET /api/dashboard/segmentation` added, mirroring `/stats`'s exact auth-dependency shape |
| `backend/tests/test_dashboard.py` | `test_employee_segmentation_service_returns_response_structure` added |
| `backend/tests/test_dashboard_router.py` | 5 new helpers (`_get_segmentation`, `_create_throwaway_employee`, `_delete_employee_hard`, `_set_override_completed`, `_insert_stale_self_reported_progress`) and 11 new tests: 7 written first (RED before GREEN) during implementation, plus 4 more added during code review to close real test-coverage gaps |

### Planning/Tracking — Modified Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `9-2-...` progressed `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | New "Deferred from: code review of 9-2-..." section, 3 entries |
| `_bmad-output/project-context.md` | Two entries appended (implementation completion, then code-review completion), per this project's own established "no story reaches `done` without a matching entry here" rule |

### Documentation Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/9-2-backend-employee-segmentation-endpoint.md` | Story file — 6 ACs, 11 Scope Notes, Dev Notes, Dev Agent Record, Review Findings section |
| `documentation/ImplementationStepsForStory9-2.md` | This file |

### Not Changed (by design)

- Any frontend file (`frontend/`) — this story is backend-only, confirmed via `AskUserQuestion` scope check ("Backend 9.2 only (Recommended)")
- `assignments/repository.py::list_assignments_for_dashboard` / `employees/repository.py::count_active_employees` — reused exactly as Story 9.1 left them, not modified

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `bmad-create-story`
- 1 research subagent + direct code verification analyzed `progress/service.py`, `dashboard/service.py`, `dashboard/schemas.py`/`router.py`, `employees/repository.py`, and existing test fixtures
- Confirmed the exact read-composition pattern to extend (Story 9.1's `get_dashboard_stats`) and the one genuinely new step (per-Employee grouping)
- 11 numbered Scope Notes written, including the `ON_TRACK_THRESHOLD` placement decision and the Needs-Attention-list-is-per-Assignment design decision
- Status → `ready-for-dev`

### Phase 2: Implementation
**Execution:** True TDD (Amelia persona), scope confirmed backend-only via `AskUserQuestion`
- Structural test + all 7 initial router tests written and confirmed RED before any production code
- 7 tasks executed in sequence: schemas → constant → service → router → query-plan check → tests → full regression
- Self-caught a real test-design problem (seeded demo Employees unusable for bucket-membership assertions) before it could reach code review
- Full regression: 714 passed, 2 skipped (706 baseline + 8 new), zero regressions
- Story marked `review`

### Phase 3: Code Review + Patches
**Skill:** `bmad-code-review`
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor) against the uncommitted diff, with the story file as spec context
- 18 unique findings after triage: 0 decision-needed, 4 patched, 3 deferred, 11 dismissed after direct verification (including an empirical Python check that disproved a claimed float-rounding bug)
- The most consequential findings were missing tests for a real, load-bearing behavioral interaction (Needs Attention + HR Override) and for the threshold comparison itself — both closed with new tests, not code changes
- Full regression re-verified after patches: 718 passed, 2 skipped (714 + 4 new), zero regressions
- Story marked `done`

---

## Test Coverage

### New/Extended Test Files

- `test_dashboard.py` — 1 new structural test (`test_employee_segmentation_service_returns_response_structure`)
- `test_dashboard_router.py` — 11 new tests + 5 non-test helpers:
  - `test_employee_segmentation_requires_authentication`
  - `test_employee_segmentation_forbidden_for_employee_role`
  - `test_employee_segmentation_on_track_employee`
  - `test_employee_segmentation_in_progress_catchall_for_zero_percent`
  - `test_employee_segmentation_needs_attention_overrides_high_completion`
  - `test_employee_segmentation_excludes_employee_with_zero_active_assignments`
  - `test_employee_segmentation_excludes_archived_employee`
  - `test_employee_segmentation_on_track_boundary_without_override` (code review patch)
  - `test_employee_segmentation_below_threshold_lands_in_progress` (code review patch)
  - `test_employee_segmentation_override_clears_needs_attention_flag` (code review patch)
  - `test_employee_segmentation_never_triggers_content_reembed_write` (code review patch)

### Regression Verification

- Backend: 706 → 714 (implementation) → 718 (code review patches) passed, 2 skipped throughout — the same 2 pre-existing, unrelated skips at every checkpoint, confirming zero regressions
- `test_dashboard.py` + `test_dashboard_router.py` in isolation: 28/28 passed after patches

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AR-26: read-composition, no new table** | `get_employee_segmentation` composes the same existing `assignments/`/`progress/` reads Story 9.1 introduced, rather than a new aggregate table | `backend/app/dashboard/service.py` |
| **AR-27: first per-Employee, full-roster aggregation read** | Confirmed by code inspection to introduce zero new SQL queries (pure in-memory groupby); actual live-DB roster/Assignment counts (5/6) recorded rather than assumed | `backend/app/dashboard/service.py`, story Dev Notes |
| **AR-28: named threshold constant** | `ON_TRACK_THRESHOLD = 0.8` as exactly one module-level constant, referenced from exactly one call site, with a comment citing PRD Open Question 20 | `backend/app/dashboard/service.py` |
| **AD-3: single Status/Provenance derivation authority** | Per-Assignment classification delegates entirely to the existing `_compute_status_and_provenance_from_data` → `ProgressService.get_provenance_detail` chain, never a second hand-rolled derivation | `backend/app/dashboard/service.py` |
| **AD-6: server-side role gate** | `GET /api/dashboard/segmentation` uses the exact same `Depends(require_hr_admin)` object as `/stats` and `GET /api/dashboard` | `backend/app/dashboard/router.py` |
| **Read-only/no-side-effect guarantee** | Deliberately omits the `match_content_for_skill` fallback (which can trigger a Content re-embed write), matching Story 9.1's own hardened `/stats` endpoint — now backed by a dedicated regression test added during code review | `backend/app/dashboard/service.py` |

---

## Key Technical Achievements

✅ **Ran the full create → implement → review → patch pipeline in one continuous session**, directly extending Story 9.1's established read-composition pattern rather than inventing a parallel one
✅ **Self-caught a real test-design problem during implementation** (seeded demo Employees unusable for bucket-membership assertions in a shared dev DB) before it could reach code review, and solved it by extending an existing precedent rather than inventing a new one
✅ **Verified, not assumed, the AR-27 "no new query" claim** — confirmed by direct code inspection and backed by live-DB counts recorded in the story's Dev Notes
✅ **Code review closed a real gap between documented confidence and actual test coverage** — the story's own Dev Notes had claimed the Needs-Attention/HR-Override interaction was "confirmed safe," but no test proved it until the review's most consequential finding forced one
✅ **Disproved three claimed defects empirically/structurally rather than dismissing them on faith** — a float-rounding risk was checked by literally running the comparisons in Python; null-crash risks and a duplicate-row risk were checked against the actual schema/query code
✅ **Zero regressions across every regression run in the session** — 706 → 714 → 718, with the same 2 pre-existing skips at every checkpoint

---

## Deferred Items (Not Story 9-2 Scope)

From this story's own code review, logged in `deferred-work.md`:
- **Unbounded `needs_attention` list growth with no cap/pagination** — extends Story 9.1's already-deferred AR-27 "no pagination/cap" debt to a list-shaped payload specifically. Real at scale, non-urgent at this pilot's current size (5 Employees); a capping strategy is better decided alongside Story 9.3/9.4, the actual consumers of this list.
- **Cross-endpoint consistency between `/api/dashboard/stats` and `/api/dashboard/segmentation`** — two independent reads of the same mutable data with no shared snapshot/transaction. Extends Story 9.1's own already-deferred single-endpoint consistency gap to a second endpoint that must now agree with the first. Low practical impact at this project's pilot scale (coaching-only data, AR-15 local-only target).
- **`get_dashboard_stats` and `get_employee_segmentation` independently re-run the identical expensive read** — no shared helper factors out "fetch + archived-Employee filter + override batch-load." A consolidation call better made once Story 9.3 reveals the actual call pattern.

Carried forward from earlier epics, unaffected by this story:
- `auth/repository.py::authenticate()` still does not read `Account` (Epic 7's own flagged gap) — irrelevant to this story's segmentation scope.

---

## Conclusion

Story 9-2 is **✅ DONE** after a full create-then-implement-then-review-and-patch cycle, run start to finish in one session:

- All 6 acceptance criteria satisfied — the exact classification priority order, a single named threshold constant, zero-Assignment exclusion, a Needs-Attention detail payload sufficient for Story 9.4's popover without a second round-trip, a recorded AR-27 query-plan check, and role-gated access matching the existing dashboard endpoints' pattern — verified by 12 dedicated backend tests plus a full 718-test regression pass, both before and after the code-review patches
- Code review surfaced 18 findings: 0 requiring a human decision, 4 patched (all closing real test-coverage gaps rather than code defects), 3 correctly deferred as extensions of Story 9.1's own already-accepted debt, and 11 dismissed after direct verification (including one empirically disproven with a live Python check)
- Zero regressions across every regression run in the session (706 → 714 → 718 passed, 2 skipped throughout)
- **Not yet committed to git** — working tree still uncommitted as of this document, on top of `HEAD` at `0b0b7e42` ("Story 9.1: Backend org-wide stats and Assignment Progress endpoint (FR-31/32)")

**Epic 9 status:** `in-progress`. Stories 9.1 and 9.2 are `done`; Stories 9.3 (Frontend: Skill Assignment Dashboard Landing Page), 9.4 (Frontend: Needs Attention Popover & Drill-Down), and 9.5 (Frontend: Nav Shell) remain `backlog`.
