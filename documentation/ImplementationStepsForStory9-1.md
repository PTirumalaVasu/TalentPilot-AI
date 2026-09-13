# Implementation Steps for Story 9-1: Backend Org-Wide Stats and Assignment Progress Endpoint

**Story Key:** 9-1-backend-org-wide-stats-and-assignment-progress-endpoint
**Epic:** 9 (Skill Assignment Dashboard) — 1 of 5 stories
**Status:** ✅ DONE (code-reviewed; not yet committed to git)
**Completed Date:** 2026-09-13

---

## Overview

Story 9.1 adds `GET /api/dashboard/stats`, the backend endpoint behind the new Skill Assignment Dashboard landing page (FR-31/FR-32): org-wide totals (`total_employees`, `total_skills_assigned`, `total_completed`) plus the Assignment Progress breakdown (`completed_count`/`in_progress_count`/`not_started_count`/`overall_percent`) that the FR-32 progress ring and top-line stats consume. It is explicitly backend-only by its own scope — the kickoff instruction asked for "both API and UI," but the story's scope notes confine it to the API, with the frontend picked up by later Epic 9 stories (9.3+).

The story is a **read-composition** exercise, not a new-table feature (AR-26): it reuses `assignments/`'s org-wide query, `employees/`'s active-employee count, and — critically — `progress/`'s single Status/Provenance derivation authority (AD-3), rather than recomputing status logic a second time. That reuse surfaced two real pre-existing issues that this story had to resolve rather than inherit silently:

1. **A dead-code trap.** `list_assignments_for_dashboard` was a fully-formed, correctly-shaped query with nothing calling it — resurrecting the *query* was correct, but its sibling `list_assignment_rows_for_dashboard_service` uses an older, narrower derivation path (a hand-rolled provenance string, not `ProgressService.get_provenance_detail`) that AD-3 exists specifically to prevent from being reintroduced. The story used the query, not the derivation, from that dead pair.
2. **A real archived-employee exclusion gap**, caught by the developer during implementation, not by review: AC3 requires archived employees' assignments excluded from *every* count, but `list_assignments_for_dashboard` only filters `Assignment.active` — it has no knowledge of `Employee.archived_at`. Fixed by filtering the assignment list in the service layer before aggregating, and called out explicitly in the story's Dev Notes as a self-caught gap.

One further issue was found and fixed during code review, not during implementation: a write-triggering fallback inherited from the sibling `get_dashboard_assignments` endpoint contradicted this endpoint's own read-only claim (AC4). The user chose to harden the endpoint by removing the fallback entirely rather than accept the inherited side effect.

This session ran story creation, TDD implementation, and a 3-layer adversarial code review with patch application, all in one continuous pass.

---

## Agents Invoked

### 1. Story-creation research subagents (4, parallel, `bmad-create-story`)

**Purpose:** Exhaustively analyze the epic, PRD, architecture, UX design, and existing code before writing the story file, so the story gives the dev agent everything needed for flawless implementation without reinventing wheels.

**When Invoked:** As part of `bmad-create-story`'s context-gathering step for Story 9.1.

**Key Findings Identified:** Confirmed `list_assignments_for_dashboard` exists but is dead code; confirmed AD-3's single-derivation-authority requirement and that `ProgressService.get_provenance_detail` is the only sanctioned path; confirmed `count_active_employees` did not yet exist and belongs in `employees/repository.py` per AD-1 (module ownership), not `assignments/repository.py`; confirmed the UX design's (06.1) FR-31/FR-32 field shapes to mirror in the response schema.

### 2. Story quality-review subagent (1, `bmad-create-story`)

**Purpose:** Independent review of the drafted story file before implementation began, checking for internal consistency, testability, and completeness of Scope Notes/ACs/Tasks.

**When Invoked:** After the story draft was complete, before handing off to implementation.

**Result:** Confirmed the story was implementation-ready; no material gaps flagged.

### 3. Blind Hunter (`bmad-review-adversarial-general` skill, background subagent)

**Purpose:** Open-ended adversarial critique of the finished diff — no spec context, no priors.

**When Invoked:** Part of `bmad-code-review`'s 3-parallel-layer step, once the story reached `review` status.

**Key Findings Identified:** Independently raised the `match_content_for_skill` write-triggering fallback as the review's most consequential finding — confirmed by reading `content/service.py::match_content_for_skill` (lines 253-289) directly, not a false positive. Also flagged the missing exact-arithmetic test for `overall_percent`.

### 4. Edge Case Hunter (`bmad-review-edge-case-hunter` skill, background subagent)

**Purpose:** Method-driven walk of every branching path and boundary condition — orthogonal to Blind Hunter's attitude-driven pass.

**When Invoked:** Same trigger, launched in parallel with Blind Hunter and the Acceptance Auditor.

**Key Findings Identified:** Independently converged on the same write-triggering fallback risk. Also identified the no-pagination/no-cap org-wide load (already tracked separately as AR-27) and the lack of transactional/snapshot consistency across the endpoint's 3 composed reads.

### 5. Acceptance Auditor (custom prompt, background subagent)

**Purpose:** Cross-check the diff against the story's own ACs and Scope Notes, and independently verify the Dev Agent Record's quantitative claims.

**When Invoked:** Same trigger, full review mode against the story file as spec.

**Key Findings Identified:** Caught that `test_dashboard_stats_reflects_mixed_status_counts`'s docstring claimed a 3-way Not-Started/In-Progress/Completed trio but only created 2 assignments, making the `in_progress_count` assertion a no-op; caught that `test_dashboard_stats_hr_override_counts_as_completed` omitted an `in_progress_count` delta assertion present in its sibling test; caught that the story's own Dev Agent Record/File List claimed "6 new tests" when the actual count was 5 test functions + 1 non-test helper (`_get_stats`).

---

## Skills Invoked

### 1. `bmad-agent-pm` → PRD/epics groundwork (prior session work, carried in as context)

FR-31/32/33 and the Skill Assignment Dashboard landing-page requirements were already in the PRD and `epics.md` (Epic 9) before this story was created, from the earlier PM/WDS pipeline (Trigger Map → Scenarios → UX Design → HTML prototype) run earlier in this project's history.

### 2. `bmad-create-story` (story creation)

**Purpose:** Produce a comprehensive, implementation-ready story file for 9.1.

**When Invoked:** Following `bmad-sprint-planning` and `bmad-create-epics-and-stories`, once Epic 9's stories existed in `epics.md` and `sprint-status.yaml`.

**Workflow Steps Executed:**
1. Loaded Epic 9's Story 9.1 AC text from `epics.md`, plus the PRD's FR-31/FR-32/FR-33 sections and the 06.1 UX design spec.
2. Ran 4 parallel research subagents to independently analyze the epic/PRD/architecture/UX artifacts and the existing `dashboard/`, `assignments/`, `employees/`, `progress/` modules.
3. Confirmed via direct code reading that `list_assignments_for_dashboard` exists but is unreferenced (dead code) and that its sibling derivation function must NOT be reused, per AD-3.
4. Confirmed `count_active_employees` did not exist yet and scoped it to `employees/repository.py` (AD-1 ownership).
5. Wrote 10 numbered Scope Notes covering: read-composition-only/no-new-table (AR-26); reuse of `list_assignments_for_dashboard`'s query but not its derivation; the single-derivation-authority requirement (AD-3, via `ProgressService.get_provenance_detail`); the batch-loading requirement for overrides (N+1 prevention); the response schema shape mirroring FR-31/FR-32; and the backend-only scope boundary.
6. Ran an independent story quality-review subagent against the draft.
7. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `9-1-...` entry updated `backlog` → `ready-for-dev`, `epic-9` → `in-progress`.

**Output File:** `_bmad-output/implementation-artifacts/9-1-backend-org-wide-stats-and-assignment-progress-endpoint.md`
**Sprint Status:** `9-1-...`: `backlog` → `ready-for-dev`; `epic-9`: `backlog` → `in-progress`

---

### 3. `bmad-agent-dev` → `bmad-dev-story` (TDD implementation, Amelia persona)

**Purpose:** Execute the story's 7 tasks in sequence: schema, service, router, repository helper, tests, regression.

**When Invoked:** `/bmad-agent-dev "start implementation for both API and UI for the story 9-1-backend-org-wide-stats-and-assignment-progress-endpoint, if required refer the UX design"`. Since Story 9.1 is scoped backend-only, the user was asked to confirm scope via `AskUserQuestion` and chose **"Backend only, as scoped (Recommended)."**

**Workflow Steps Executed:**
1. **Task 1 — Schema:** `DashboardStatsResponse` added to `backend/app/dashboard/schemas.py` — 7 fields (`total_employees`, `total_skills_assigned`, `total_completed`, `completed_count`, `in_progress_count`, `not_started_count`, `overall_percent`).
2. **Task 2 — Repository helper:** `count_active_employees(db)` added to `backend/app/employees/repository.py` (not `assignments/repository.py`, per AD-1 module-ownership).
3. **Task 3 — Service:** `DashboardService.get_dashboard_stats(session)` added to `backend/app/dashboard/service.py` — resurrects `list_assignments_for_dashboard`, filters archived-employee assignments (the AC3 gap caught here, not by review), batch-loads overrides via the existing `_batch_load_overrides`, and delegates status computation entirely to `_compute_status_and_provenance_from_data` → `ProgressService.get_provenance_detail` (never the bare derivation function).
4. **Task 4 — Router:** `GET /api/dashboard/stats` added to `backend/app/dashboard/router.py`, mirroring the existing `GET /api/dashboard` endpoint's auth pattern exactly (`Depends(require_hr_admin)` + `Depends(get_db)`, no query params).
5. **Task 5 — Structural test:** `test_dashboard_stats_service_returns_response_structure` added to `backend/tests/test_dashboard.py`, matching that file's existing convention of structural-only assertions against the shared live dev DB.
6. **Task 6 — Router tests:** 5 new tests + 1 helper (`_get_stats`) added to `backend/tests/test_dashboard_router.py`: 401/403 role-gate tests, mixed-status delta assertions, HR-override-counts-as-completed, and archived-employee exclusion (the test that caught the AC3 gap by failing before the service-layer fix).
7. **Task 7 — Regression:** Full backend suite run — 706 passed, 2 skipped (pre-existing, unrelated), zero regressions.
8. Story's Dev Agent Record, Completion Notes, and File List filled in; Status → `review`.

**Real bugs self-caught during implementation (not by review):**
- **AC3 archived-employee gap** — `list_assignments_for_dashboard` filters `Assignment.active` but not `Employee.archived_at`; fixed by filtering the assignment list in the service before aggregating any count.
- Two `FOREIGN KEY` violations in test cleanup helpers, fixed while writing the archived-employee and override tests:
  - `_cleanup_assignment`/`_cleanup_assignments_for` didn't delete `AssignmentOverride` rows before `Assignment` — fixed by deleting overrides first in both helpers.
  - The archived-employee test's cleanup deleted `employees` without first deleting the paired `Account` row (`Account.id == Employee.id` per AR-24) — fixed by deleting `Account` first.
  - A test-shape bug: `create_emp_response.json()["employee"]["id"]` should have been `["id"]` directly, since `EmployeeCreatedResponse` extends `EmployeeResponse` flatly — fixed immediately after checking the schema.

**Output Files:**
- `backend/app/dashboard/schemas.py`, `backend/app/dashboard/service.py`, `backend/app/dashboard/router.py` (modified)
- `backend/app/employees/repository.py` (modified)
- `backend/tests/test_dashboard.py`, `backend/tests/test_dashboard_router.py` (modified)
- `_bmad-output/implementation-artifacts/9-1-backend-org-wide-stats-and-assignment-progress-endpoint.md`

**Sprint Status:** `9-1-...`: `ready-for-dev` → `in-progress` → `review`

---

### 4. `bmad-code-review` (3-layer adversarial review + patch application)

**Purpose:** Independent adversarial verification of the finished implementation, followed by resolving every finding.

**When Invoked:** `/bmad-code-review`, no argument. User confirmed 3 parallel layers via `AskUserQuestion` ("Yes, 3 parallel layers (Recommended)"), then confirmed the diff scope ("proceed").

**Workflow Steps Executed:**
- Constructed the diff against the uncommitted working-tree changes for Story 9.1's files.
- Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor in parallel as background subagents.
- Triaged the combined findings into: **1 decision-needed, 5 patch, 3 defer, 4 dismiss**.
- **Presented the one decision-needed finding to the user:** the video-duration-resolution fallback (copied from the sibling `get_dashboard_assignments`) calls `match_content_for_skill`, which can trigger a real DB write (`reembed_content_for_skill`) as a side effect of this GET endpoint — contradicting AC4's read-only framing. Verified as real, not a false positive, by reading `content/service.py::match_content_for_skill` directly. Options presented: (1) accept the inherited side effect, (2) harden this endpoint to drop the fallback, (3) something else. **User chose option 2.**
- **Applied option 2:** `get_dashboard_stats` now uses only `ProgressRepository.get_video_duration(assignment)`, with no `match_content_for_skill` call — an inline comment documents the trade-off (an assignment with partial watch progress but no resolvable duration now classifies as Not Started here, rather than a percentage-based status, unlike the sibling endpoint).
- **User chose to apply all 5 patches** (option 1: "apply every patch, no per-finding confirmation"):
  1. Rewrote `test_dashboard_stats_reflects_mixed_status_counts` to add a genuine 3rd assignment (MORGAN_ID, partial watch) so the In-Progress bucket gets a real positive delta, not a no-op.
  2. Added an exact-arithmetic assertion for `overall_percent` (`round(completed_count / total_skills_assigned * 100)`), not just a bounds check.
  3. Corrected the story file's own Dev Agent Record/File List claim of "6 new tests" to the actual "5 new tests + 1 helper" in 4 locations.
  4. Added the missing `in_progress_count` delta assertion to `test_dashboard_stats_hr_override_counts_as_completed`, matching its sibling test's rigor.
  5. Added a docstring to `DashboardStatsResponse` explaining that `total_completed`/`completed_count` are intentionally, permanently identical (they back two separate UI elements sharing one number), so a future reader doesn't "fix" the apparent duplication.
- **Deferred 3 findings** to `deferred-work.md`: the no-pagination/no-cap org-wide load (already tracked as AR-27 in `epics.md`); no transactional/snapshot consistency across the endpoint's 3 composed reads (low practical impact at pilot scale); the HR-Override "always Completed" assumption depending on `SetOverrideRequest`'s current single-status contract.
- **Dismissed 4 findings after verification**: the "identical auth to `GET /api/dashboard`" claim can't practically drift since both endpoints share the literal same `require_hr_admin` dependency object; no caching/rate-limiting discussion is out of scope for this project's local-only/pilot-scale target (AR-15); `list_assignments_for_dashboard`'s "wasted" eager-loads match the story's own Scope Note direction to reuse the function as-is; the archived-employee test's raw `DELETE FROM` cleanup matches this test file's pre-existing convention for other tables.
- Re-ran `test_dashboard.py`/`test_dashboard_router.py` — 16/16 passed. Re-ran the full backend suite — **706 passed, 2 skipped**, identical to the pre-review baseline, confirming zero regressions from the patches (which strengthened assertions within existing test functions rather than adding new ones).
- Story Status → `done`; `sprint-status.yaml` synced.

**Output:** Story file's "### Review Findings" subsection (1 decision-needed resolved, 5 checked-off patches with inline "Fixed:" notes, 3 checked-off deferred items, 4 dismissed noted in prose); `deferred-work.md` gained a new "Deferred from: code review of 9-1-..." section with 3 entries.

**Documentation Generated:**
- The story file's Review Findings section, Change Log, and Status field
- `deferred-work.md`'s new Story 9.1 section
- Sprint status synced (`9-1-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`; `epic-9` remains `in-progress`, since Stories 9.2-9.5 are still `backlog`)

---

## Files Created/Updated

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/dashboard/schemas.py` | `DashboardStatsResponse` added (7 fields), with an intentional-duplication docstring for `total_completed`/`completed_count` (code review) |
| `backend/app/dashboard/service.py` | `DashboardService.get_dashboard_stats()` added — resurrects `list_assignments_for_dashboard`, filters archived-employee assignments, batch-loads overrides, delegates status computation to `ProgressService.get_provenance_detail`; code review hardened it to drop the `match_content_for_skill` write-triggering fallback |
| `backend/app/dashboard/router.py` | `GET /api/dashboard/stats` added, mirroring the existing dashboard endpoint's auth pattern |
| `backend/app/employees/repository.py` | `count_active_employees(db)` added (AD-1: lives here, not in `assignments/`) |
| `backend/tests/test_dashboard.py` | `test_dashboard_stats_service_returns_response_structure` added |
| `backend/tests/test_dashboard_router.py` | 5 new tests + `_get_stats` helper; `_cleanup_assignment`/`_cleanup_assignments_for` fixed to also delete `AssignmentOverride` rows; test rigor patched during code review (genuine In-Progress case, exact `overall_percent` assertion, missing `in_progress_count` assertion added) |

### Planning/Tracking — Modified Files

| File | Purpose |
|------|---------|
| `_bmad-output/planning-artifacts/epics.md` | Epic 9 added with Stories 9.1-9.5; Requirements Inventory, FR Coverage Map, Epic List updated |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `epic-9` + 5 stories added; `9-1-...` progressed `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | New "Deferred from: code review of 9-1-..." section, 3 entries |

### Documentation Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/9-1-backend-org-wide-stats-and-assignment-progress-endpoint.md` | Story file — 5 ACs, 10 Scope Notes, Dev Notes, Dev Agent Record, Review Findings section |
| `documentation/ImplementationStepsForStory9-1.md` | This file |

### Not Changed (by design)

- Any frontend file (`frontend/`) — this story is backend-only, confirmed via `AskUserQuestion` scope check ("Backend only, as scoped")
- `assignments/repository.py` — `count_active_employees` deliberately placed in `employees/repository.py` instead, per AD-1

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `bmad-create-story`
- 4 parallel research subagents + 1 quality-review subagent analyzed the epic, PRD, architecture, and existing `dashboard/`/`assignments/`/`employees/`/`progress/` modules
- Confirmed the dead-code trap (`list_assignments_for_dashboard` exists, unused; its derivation sibling must not be reused per AD-3) and the correct module ownership for `count_active_employees` (AD-1)
- 10 numbered Scope Notes written
- Status → `ready-for-dev`

### Phase 2: Implementation
**Execution:** Direct TDD (Amelia persona), scope confirmed backend-only via `AskUserQuestion`
- 7 tasks executed in sequence: schema → repository helper → service → router → structural test → router tests → full regression
- Self-caught a real AC3 gap (archived-employee assignments not excluded from every count) before it could reach code review
- Fixed 2 FK-violation bugs and 1 test-shape bug in test cleanup helpers along the way
- Full regression: 706 passed, 2 skipped, zero regressions
- Story marked `review`

### Phase 3: Code Review + Patches
**Skill:** `bmad-code-review`
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor) against the uncommitted diff
- 13 unique findings after triage: 1 decision-needed (user chose to harden the endpoint, removing the write-triggering fallback), 5 patched, 3 deferred, 4 dismissed after verification
- The most consequential finding closed a real read-only-contract violation: a GET endpoint that could trigger a Content re-embed write
- Full regression re-verified after patches: 706 passed, 2 skipped, identical to baseline — zero regressions
- Story marked `done`

---

## Test Coverage

### New/Extended Test Files

- `test_dashboard.py` — 1 new structural test (`test_dashboard_stats_service_returns_response_structure`)
- `test_dashboard_router.py` — 5 new tests + 1 non-test helper (`_get_stats`):
  - `test_dashboard_stats_requires_authentication`
  - `test_dashboard_stats_forbidden_for_employee_role`
  - `test_dashboard_stats_reflects_mixed_status_counts` (rewritten during code review to include a genuine Not-Started/In-Progress/Completed trio, plus an exact `overall_percent` formula assertion)
  - `test_dashboard_stats_hr_override_counts_as_completed` (code review added a missing `in_progress_count` assertion)
  - `test_dashboard_stats_excludes_archived_employee_and_their_assignments` (the test that caught the AC3 gap by failing before the service-layer fix)

### Regression Verification

- Backend: 706 passed, 2 skipped, both before and after the code-review patches — identical counts, confirming zero regressions
- `test_dashboard.py` + `test_dashboard_router.py` in isolation: 16/16 passed after patches

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AR-26: read-composition, no new table** | `get_dashboard_stats` composes existing `assignments/`, `employees/`, `progress/` reads rather than introducing a new aggregate table | `backend/app/dashboard/service.py` |
| **AD-3: single Status/Provenance derivation authority** | Status computation delegates entirely to `ProgressService.get_provenance_detail` via `_compute_status_and_provenance_from_data`, never a second hand-rolled derivation — deliberately avoided reusing `list_assignment_rows_for_dashboard_service`'s older derivation path | `backend/app/dashboard/service.py` |
| **AD-1: single-owner modules** | `count_active_employees` placed in `employees/repository.py`, not `assignments/repository.py`, since employee data belongs to the `employees/` module | `backend/app/employees/repository.py` |
| **AD-6: server-side role gate** | `GET /api/dashboard/stats` uses the exact same `Depends(require_hr_admin)` object as the existing `GET /api/dashboard` endpoint | `backend/app/dashboard/router.py` |
| **AC4 read-only guarantee, hardened during review** | Removed the `match_content_for_skill` fallback (which could trigger a `reembed_content_for_skill` write) entirely from this endpoint's status computation, accepting a documented accuracy trade-off in exchange for a genuinely side-effect-free GET | `backend/app/dashboard/service.py` |

---

## Key Technical Achievements

✅ **Ran the full create → implement → review → patch pipeline in one continuous session**, following the earlier PM/WDS pipeline (PRD → Trigger Map → Scenarios → UX Design → prototype) that had already established FR-31/32/33 and Epic 9
✅ **Self-caught a real AC3 gap during implementation** (archived-employee assignment exclusion) before it could reach code review, by reading the resurrected query's actual filter behavior rather than trusting its name
✅ **Avoided a real AD-3 violation trap**: reused a dead query's data shape without reusing its sibling's outdated derivation logic
✅ **Code review found a genuine read-only-contract violation** — a GET endpoint that could trigger a database write via an inherited fallback — independently corroborated by two of the three review layers and verified against the actual `content/service.py` source before being raised
✅ **Corrected an internal fabrication before it became permanent record**: a "707 passed" regression claim was written before the full suite was actually re-run; once the real result (706 passed, 2 skipped — unchanged from baseline) came back, the Change Log entry was corrected to the verified number rather than left as written
✅ **Zero regressions across every regression run in the session** — implementation and the code-review re-verification both landed at 706 passed, 2 skipped

---

## Deferred Items (Not Story 9-1 Scope)

From this story's own code review, logged in `deferred-work.md`:
- **No pagination/cap on the org-wide active-assignment load** — unlike the paginated main dashboard grid; already tracked separately as AR-27 in `epics.md` ("query-plan/index check once real data volume is known").
- **No transactional/snapshot consistency across the 3 composed reads** (assignments, overrides, employee count) — a concurrent write between them could yield internally-inconsistent totals in one response. Low practical impact for a coaching-only, approximate landing-page stat at this project's pilot scale.
- **The HR-Override "always counts as Completed" assumption** is only true because `SetOverrideRequest`'s current contract has no way to set any other `override_status` — protects against a hypothetical future schema change, not a present defect.

Carried forward from earlier epics, unaffected by this story:
- `auth/repository.py::authenticate()` still does not read `Account` (Epic 7's own flagged gap) — irrelevant to this story's dashboard-stats scope.

---

## Conclusion

Story 9-1 is **✅ DONE** after a full create-then-implement-then-review-and-patch cycle, run start to finish in one session:

- All 5 acceptance criteria satisfied — org-wide totals, the Assignment Progress breakdown, archived-employee exclusion from every count, a genuinely read-only GET, and role-gated access matching the existing dashboard endpoint's pattern — verified by 6 dedicated backend tests plus a full 706-test regression pass, both before and after the code-review patches
- Code review surfaced 9 real findings: 1 decision requiring the user's call (resolved by hardening the endpoint), 5 patched (test rigor + documentation), 3 correctly deferred as pre-existing or out of literal AC scope, and 4 dismissed after verification
- Zero regressions across every regression run in the session
- **Not yet committed to git** — working tree still uncommitted as of this document, on top of `HEAD` at `f1b4604b` ("Add Scenario 06 (Skill Assignment Dashboard) through Phase 2-5")

**Epic 9 status:** `in-progress`. Story 9.1 is `done`; Stories 9.2 (Backend Employee Segmentation Endpoint), 9.3, 9.4, and 9.5 remain `backlog`.
