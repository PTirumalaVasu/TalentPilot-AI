# Implementation Steps for Story 7-5: HR Admin Deletes or Archives an Employee Record

**Story Key:** 7-5-hr-admin-deletes-or-archives-an-employee-record
**Epic:** 7 (Employee Roster Management) — **fifth story**
**Status:** ✅ DONE (code-reviewed; not yet committed to git)
**Completed Date:** 2026-09-12

---

## Overview

Story 7.5 adds `DELETE /api/admin/employees/{employee_id}` (FR-27): an HR Admin can remove an Employee who has left. If the Employee has zero Assignment history ever (active or soft-deleted), the record is **hard-deleted**; if they have any history, the record is **archived** instead (`archived_at` set) — history is preserved, but the Employee drops off the default roster view and every Employee picker.

Epics.md itself flagged this story in advance as unusually large — "do not estimate or review it as routine" — because it genuinely spans three separate modules and three separate correctness mechanisms, none buildable in isolation from the others:

1. **`employees/`** — an atomic check-then-act (hard-delete vs. archive) that can't race a concurrent Assignment creation.
2. **`auth/`** — AR-25's requirement that an archived identity's still-valid session gets rejected on its very next request, not just re-checked at login (touches `get_current_user`, which every protected route in the app depends on).
3. **`assignments/`** — the already-shipped, `done` `create_assignment_service` needed a new pre-write check so a stale employee-picker submission against a since-archived Employee is rejected at confirm time, not just picker-load time.

The session ran the full pipeline in one continuous pass: create the story (via three parallel research agents), implement it end to end (API + UI), live-verify it against a rebuilt Docker backend and a real browser, run it through a 3-layer adversarial code review that surfaced one genuine design gap requiring a user decision plus eight other real, fixable issues, and re-verify everything live a second time after the fixes landed.

Two design corrections were made *during* the session, not left for a future story to discover — both driven by actually running the full test suite / a real adversarial review rather than reasoning from the diff alone:

- **AC4's session-revalidation check had to be narrowed mid-implementation.** The first design (reject any session whose `Account` row is missing, not just archived ones) broke 10 pre-existing tests across 8 files that rely on a wide, deliberate codebase convention: minting JWTs for fabricated non-existent UUIDs or plain non-UUID strings (`"rita"`, `"casey"`) purely to exercise role/identity logic, with no backing `Account` row at all. Fixed by rejecting only when a **real, existing** `Account` is found archived — which also correctly re-scoped AC4 to archived (not hard-deleted) employees, matching its literal wording.
- **`has_assignment_history`'s scope had to be expanded during code review.** It originally only reflected `Assignment.employee_id` (was this employee ever an assignment *target*) — it never accounted for an employee's own actions as an assigner, deleter, override-setter/reverser, API-key admin, or content-attacher. For any employee who had acted in one of those roles (in this app's real usage, the one interactive HR Admin), the confirm dialog would always predict "Remove Employee" while the server actually archived them — not a rare race, a structural predictor gap. The user chose to expand the check rather than accept the narrow blast radius.

---

## Agents Invoked

### 1. **General-purpose research agent — backend surfaces (context gathering for story creation)**

**Purpose:** Exhaustively read the real current backend code across three modules before writing the story spec.

**When Invoked:** In parallel with two other research agents, as the first step of story authoring.

**Key Findings Reported:** `archived_at` already exists on `Employee` (Story 7.1); the critical, load-bearing fact that `auth/service.py::get_current_token_payload`/`get_current_user` take **no `db` dependency at all** today — the single most architecturally significant fact for AC4; `Assignment.active`/`deleted_at`/`deleted_by` is the exact soft-delete shape FR-15's "active or soft-deleted" language maps to; no existing helper checks "did this employee ever have an Assignment," and every existing employee-scoped query filters `active.is_(True)` (wrong shape for this story's AC1); `create_assignment_service`'s exact insertion point for a new pre-write check; the `Account`/`Employee` shared-PK design (AR-24) and the pre-existing mock-login-vs-real-Account split-brain.

### 2. **General-purpose research agent — frontend surfaces (context gathering for story creation)**

**Purpose:** Exhaustively read the real current frontend code and identify the established pattern(s) for server-decided, conditional confirm-dialog copy.

**When Invoked:** In parallel with the backend research agent and the UX research agent.

**Key Findings Reported:** `RowActions`' Delete/Archive button is still wired to the shared "not available yet" stub (Story 7.4 left it untouched); `DeleteSkillModal.tsx`'s copy is **static**, not conditional, because Skills gate deletability by hiding the button entirely for a locked Skill — a materially different (and insufficient-as-is) precedent for this story, where the button always renders and the dialog itself must branch; the codebase's two existing conditional-copy precedents (`SkillCard.tsx`'s `ever_assigned`, `DeleteAssignmentModal.tsx`'s `hasRecordedProgress`) both derive their copy from a field already present in an already-fetched list payload, never a fresh per-click network call — establishing the pattern this story's `has_assignment_history` field would follow; no `deleteEmployee`-shaped API function exists yet; and, critically, that the Skill Assignment Flow's employee picker calls a **different** `listEmployees()` (from `assignmentsApi.ts`, hitting `GET /api/assignments/employees`) than the HR roster page's own `listEmployees()` (from `employeesApi.ts`, hitting `GET /api/admin/employees`) — the two are independently duplicated reads, and only the former is "every Employee picker."

### 3. **General-purpose research agent — UX design docs (context gathering for story creation)**

**Purpose:** Pull the exact, verbatim confirmation-dialog copy and object-ID naming from the formal UX scenario spec and the reference prototype.

**When Invoked:** In parallel with the two code-research agents.

**Key Findings Reported:** The full verbatim object-ID/copy table for the Delete/Archive Confirmation modal (`delete-employee-heading`/`-summary-hard`/`-summary-archive`/`-btn-cancel`/`-btn-confirm`, plus the exact success-toast strings); confirmation that UX-DR38 (branching copy, server-decided) and UX-DR42 (aria-labels) are the two UX-DR entries governing this story; that the reference prototype's Delete/Archive modal is **not** a stub (unlike its badly-oversimplified Edit modal) — it implements the full branching logic, just via a client-side mock field the real build cannot rely on; that AR-25 exists **only** as an `epics.md`-level requirement with no corresponding architecture-spine AD entry yet; and FR-15's exact wording, which AC1's "active or soft-deleted" phrasing depends on structurally.

### 4. **Blind Hunter (`bmad-review-adversarial-general` skill, via a background subagent)**

**Purpose:** Open-ended adversarial critique of the finished diff — no spec context, no priors.

**When Invoked:** Automatically, as part of the `code-review` workflow's 3-parallel-layer step, once the story reached `review` status.

**Key Findings Identified:** The single most consequential finding of the whole review — that `has_assignment_history`'s narrow scope means the confirm dialog would **routinely**, not rarely, mispredict the outcome for any employee who has acted as an assigner/deleter/overrider/API-key-admin/content-attacher (four real FK columns across three tables, one of which the story's own Scope Note 6 had actually gotten wrong by name). Also independently found: the unguarded `db.get()` reintroduced in the new `update_account_archived_at`, mirroring a bug class the same diff explicitly fixed one function away; no self-deletion guard (a plausible, unrecoverable self-lockout given this app's single real HR Admin and no un-archive feature); no idempotency guard on re-archiving an already-archived employee (silently clobbers the audit timestamp FR-27 exists to protect); a stale comment on `OrgApiCredential.configured_by` this story's new endpoint directly invalidated; the overly-broad, unlogged `except IntegrityError` silently converting any DB defect into a reported success; `_archived_or_missing` never using its own `employee_id` parameter; and (correctly flagged, but already fully documented and reasoned in the story's own Dev Notes) that a hard-deleted employee's session isn't specifically revoked until natural JWT expiry.

### 5. **Edge Case Hunter (`bmad-review-edge-case-hunter` skill, via a background subagent)**

**Purpose:** Method-driven walk of every branching path and boundary condition — orthogonal to Blind Hunter's attitude-driven pass.

**When Invoked:** Same trigger, launched in parallel with Blind Hunter and the Acceptance Auditor.

**Key Findings Identified (JSON-formatted with location/trigger/guard/consequence):** Independently converged on several of the same real issues (the unguarded `db.get()`, no self-deletion guard, the broad `except IntegrityError`, the missing/archived conflation in the 409); also raised a claimed frontend pagination "empty page after deleting the last row" bug (verified false during triage — `EmployeesPage.tsx`'s `currentPage` is a derived value that self-clamps every render) and a low-confidence claim about `get_current_user`'s signature change risking a direct non-`Depends` caller (verified false — no such caller exists anywhere in the codebase).

### 6. **Acceptance Auditor (custom prompt, via a background subagent)**

**Purpose:** Cross-check the diff against the story's own spec — 5 Acceptance Criteria and 15 Scope Notes — and sanity-check the Dev Agent Record's claims against what the diff actually contains.

**When Invoked:** Same trigger, `review_mode = "full"` since the story file was set as `{spec_file}`.

**Result:** Reported the diff as "unusually faithful" to the story's own Scope Notes overall — the `FOR UPDATE` mechanism, the `Account.archived_at` mirror, the picker-vs-roster distinction, and the verbatim UX copy all matched exactly, and the Dev Agent Record's test-count arithmetic checked out (unlike Story 7.4's own review, which had caught a wrong-arithmetic claim). Still found 4 genuine gaps: the unguarded `db.get()` (independently, the third layer to catch it); `create_employee_service` not using the shared `_with_assignment_history` helper (confirmed stylistic-only, not a bug); the AC1 concurrency test using a source-text grep instead of the compiled-SQL inspection Task 10 actually specified; and — the most substantive of its four — **zero test coverage for the `IntegrityError`-fallback-to-archive branch**, which Scope Note 6 itself calls "the load-bearing correctness mechanism," despite the story explicitly and deliberately excusing the *other* untestable gap (AC1's genuine concurrency) with a documented reason and not doing the same here.

---

## Skills Invoked

### 1. **`bmad-create-story` (story creation)**

**Purpose:** Produce a comprehensive story file for 7.5 from scratch — only the epic's raw AC text and a size warning existed beforehand.

**When Invoked:** Explicit user instruction via `/bmad-agent-dev`: "start development api and ui for the story 7-5-hr-admin-deletes-or-archives-an-employee-record refer the ux design if required."

**Workflow Steps Executed:**
1. Confirmed via `sprint-status.yaml` that 7.1–7.4 were `done` and 7.5 had no story file yet.
2. Read Epic 7's Story 7.5 AC text from `epics.md` — 5 ACs plus a Dev Notes callout flagging this story's unusual, cross-epic size and suggesting AC4 could be split into its own story if tighter sizing were preferred.
3. Dispatched three research subagents in parallel (backend surfaces, frontend surfaces, UX design docs — see **Agents Invoked** #1–3) rather than reading everything sequentially in the main session.
4. Personally re-verified the single highest-risk claim by reading the actual code directly: confirmed `GET /api/assignments/employees` (not the HR roster's own endpoint) is the real "Employee picker," and read `assignments/service.py::create_assignment_service`'s full body to find AC5's exact insertion point.
5. Made five explicit, load-bearing design decisions the epic text had left open, writing each into a numbered Scope Note rather than leaving them for the dev pass to improvise: the `SELECT ... FOR UPDATE` atomicity mechanism (and *why* it works, via Postgres's FK-driven `FOR KEY SHARE` lock); the `Account.archived_at` mirror to avoid a circular import between `auth` and `employees` for AC4; the has-assignment-history preview-vs-confirm-time split to reconcile UX-DR38 with AC1/AC2's atomicity requirement; the IntegrityError-falls-back-to-archive handling for the HR-Admin-as-assigner edge case; and the exact new-response-shape departure from `deleteSkill`'s bodyless convention.
6. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `7-5-...` entry updated from `backlog` to `ready-for-dev`.

**Output File:** `_bmad-output/implementation-artifacts/7-5-hr-admin-deletes-or-archives-an-employee-record.md`
**Sprint Status:** `7-5-...`: `backlog` → `ready-for-dev`

---

### 2. **Direct TDD implementation (Amelia persona, `bmad-dev-story` execution)**

**Purpose:** Execute the story's 15 tasks in sequence — backend delete/archive endpoint plus two cross-cutting changes (`auth/`, `assignments/`), and the frontend confirm modal plus its wiring.

**When Invoked:** Continuing directly from story creation in the same session.

**Workflow Steps Executed:**

1. **Task 1 — Migration:** `013_add_accounts_archived_at.py` — `accounts.archived_at`, mirroring `employees.archived_at`.
2. **Task 2 — Schema:** `EmployeeResponse.has_assignment_history: bool = False`; new `DeleteEmployeeResponse`.
3. **Task 3 — Employees repository:** `get_employee_for_update` (the `FOR UPDATE` lock, with the FK/lock-conflict reasoning documented inline), `hard_delete_employee`, `archive_employee`.
4. **Task 4 — Assignments repository/service:** `assignment_exists_for_employee`/`distinct_employee_ids_with_assignments` (unfiltered on `active`, per FR-15); the picker's `list_employees` gained an `archived_at.is_(None)` filter.
5. **Task 5 — Auth repository:** `get_account_by_id`, `update_account_archived_at`, `delete_account` (guarded for `None`, unlike an existing sibling function's known-deferred gap).
6. **Task 6 — Auth service (AC4):** `get_current_user` gained a `db: AsyncSession = Depends(get_db)` dependency and an archived-Account check.
7. **Task 7 — Employees service:** `delete_or_archive_employee_service` (the core logic — lock, check history, attempt hard-delete inside a try/except IntegrityError, fall back to archive) and `assert_employee_active_for_assignment` (AC5's check, reusing the same lock for race-safety).
8. **Task 8 — Router:** `DELETE "/{employee_id}"` added to the existing `employees_router`.
9. **Task 9 — Assignments service (AC5):** `create_assignment_service` calls `assert_employee_active_for_assignment` immediately after `require_hr_admin`, before any write.
10. **Task 10 — Backend tests:** 12 new tests written together with the implementation (given this story's scale) covering all 5 ACs plus 404/403/401.
11. **Mid-implementation regression caught and fixed:** running the *full* backend suite (not just the story's own new tests) surfaced that the first AC4 design broke 10 pre-existing tests across 8 files — see **Overview** above. Fixed by narrowing the check; re-ran the full suite clean.
12. **Tasks 11–14 — Frontend:** `employeesApi.ts` gained `has_assignment_history`/`deleteOrArchiveEmployee()`; new `DeleteArchiveEmployeeModal.tsx` (mirrors `DeleteSkillModal.tsx`'s `Dialog`/`requestIdRef` shape, but branches its copy dynamically); wired into `EmployeesPage.tsx`'s previously-stubbed Delete/Archive action at both table and card call sites; `AssignmentModal.tsx` gained a distinct re-pick-guidance message for a `409 EMPLOYEE_ARCHIVED` response.
13. **Task 15 — Frontend tests:** new `DeleteArchiveEmployeeModal.test.tsx` (6 tests); `EmployeesPage.test.tsx`'s pre-existing combined stub-toast test split in two, plus 4 new tests; 1 new test in `AssignmentModal.test.tsx`.
14. **Full regression:** backend 687 passed/2 skipped/0 failed (675 baseline + 12 new); frontend 375 passed/0 failed (364 baseline + 11 new); `tsc --noEmit` at 31 pre-existing errors, none in any touched file; `vite build` clean at 532 modules (up from 531).
15. **Live-verified twice.** First via `curl` against a rebuilt `talentpilot-api` Docker container, as Rita: hard-delete (`{"action":"deleted"}`, both `Employee`/`Account` rows confirmed gone), archive (`{"action":"archived"}`), picker-exclusion vs. roster-inclusion, and AC5's `409 EMPLOYEE_ARCHIVED` — all confirmed with exact expected bodies. Minted a JWT directly inside the container to confirm AC4's `401 "Account has been archived"` for an archived session, and the documented `404` (not `401`) for a hard-deleted one. Second, a 14-check ad hoc Playwright/Chromium smoke test against a real `vite` dev server proxying to the rebuilt backend, covering both the hard-delete and archive UI branches end to end in an actual browser — all 14 checks passed. All live test data cleaned up from the dev DB afterward.
16. Filled in the story file's Dev Agent Record, File List, Completion Checklist, and Change Log; Status → `review`.

**Output File:** `_bmad-output/implementation-artifacts/7-5-hr-admin-deletes-or-archives-an-employee-record.md`
**Sprint Status:** `7-5-...`: `ready-for-dev` → `in-progress` → `review`

---

### 3. **`bmad-code-review` (3-layer adversarial review + decision + patch application)**

**Purpose:** Independent adversarial verification of the finished implementation, followed by resolving every finding — including one genuinely ambiguous design question requiring the user's own call.

**When Invoked:** `/bmad-code-review` command, no argument — resolved via Tier 2 (recent conversation: the just-finished Story 7.5 implementation), confirmed against the story file's `baseline_commit` matching `HEAD` exactly (nothing committed yet).

**Workflow Steps Executed:**

- Constructed the diff via `git add -N .` (intent-to-add, to include untracked new files without staging their content) + `git diff HEAD` — 1,902 lines across 22 files, well under the chunking threshold; reset the intent-to-add afterward.
- Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor in parallel as background subagents, each pointed at the raw diff file rather than a pasted string, to keep them cold and unbiased.
- **Triaged the findings** by reading the actual current code at each location before rating severity, not from the diff hunk alone: `1 decision-needed`, `8 patch`, `1 defer`, `6 dismiss`.
- **Resolved the one decision-needed finding via `AskUserQuestion`:** whether to expand `has_assignment_history`'s scope now (broader query, more accurate dialog) or accept the narrow blast radius given only one real interactive HR Admin exists in this app's usage. **User chose to expand it now.**
- **Implemented the expansion:** `employees/service.py::_has_any_history_for_employee`/`_get_employee_ids_with_any_history`, unioning three new cross-module service calls added for this purpose — `assignments.service` (extended `assignment_exists_for_employee`/`distinct_employee_ids_with_assignments` to also cover `assigned_by`/`deleted_by`), `progress.service.ProgressService` (new `has_override_actor_history_for_employee`/`get_employee_ids_with_override_actor_history`, backed by new `ProgressRepository` methods checking `AssignmentOverride.set_by`/`reversed_by`), and `content.service` (new `has_admin_actor_history_for_employee`/`get_employee_ids_with_admin_actor_history`, backed by new `content/repository.py` functions checking `AdminApiKey.admin_id`/`ContentCatalog.attached_by`). This single expanded check now drives both the dialog's prediction *and* the actual delete-vs-archive decision, so an admin-actor employee is archived directly instead of attempting (and failing) a hard-delete first — and the `IntegrityError` catch became a defensive-only backstop.
- **Applied all 8 patches:**
  1. Self-deletion/self-archive guard — `409 CANNOT_DELETE_SELF` immediately after the role gate.
  2. Fixed the unguarded `db.get()` in the new `update_account_archived_at` (the exact bug class a sibling function in the same diff had explicitly guarded against).
  3. Idempotency guard on re-archiving an already-archived employee — short-circuits before touching either timestamp again.
  4. Fixed the 409 conflating "missing" with "archived," and the dead `employee_id` parameter — renamed to `_archived_conflict`, now interpolates the id into an accurate message.
  5. Narrowed the `except IntegrityError` to the actual FK-violation SQLSTATE (`23503`), re-raising anything else, and added `logger.exception(...)` before falling through.
  6. Added the missing test coverage for the (now largely superseded) `IntegrityError`-fallback branch: one real end-to-end test (an employee who's never a target but *is* an assigner), plus two monkeypatch-based tests directly exercising the now-defensive-only backstop (FK-violation SQLSTATE → falls back to archive; any other SQLSTATE → re-raises, proving an unrelated DB defect is never silently reported as success).
  7. Corrected the stale `OrgApiCredential.configured_by` comment this story's new endpoint invalidated.
  8. Corrected the story file's own Scope Note 6, which had miscounted the FK inventory and gotten one column name wrong (`created_by` vs. the real `set_by`) — rewritten to document the final expanded-pre-check design.
- **Dismissed 6 findings, each verified rather than argued away:** a pagination "empty page" claim (verified false by reading the derived `currentPage` clamp); a `get_current_user` direct-caller risk claim (verified false, no such caller exists); a `create_employee_service`-should-use-the-shared-helper claim (confirmed stylistic-only); a weaker-than-specified concurrency-test-assertion claim (accepted as equivalent practical assurance); a dialog-copy-staleness claim (confirmed already an explicitly documented, accepted tradeoff in the story's own Scope Note 4); and the hard-delete-session-not-revoked claim (confirmed already fully documented and reasoned as a deliberate scope correction earlier in the same story).
- **1 item deferred** to `deferred-work.md`: `assert_employee_active_for_assignment`'s `FOR UPDATE` lock is stronger than necessary for a read-only check, unnecessarily serializing concurrent assignments to the same employee across different skills — real but low-urgency at this app's actual concurrency scale, matching its existing no-optimistic-locking precedent elsewhere.
- Re-ran the full backend regression suite after all patches: 692 passed/2 skipped/0 failed (687 + 5 new). Frontend re-confirmed unaffected (all fixes were backend-only).
- **Re-verified live a second time**, not just at the test level: rebuilt and recreated the Docker backend again, confirmed via `curl` that Rita cannot delete her own account (`409 CANNOT_DELETE_SELF`) and that calling `DELETE` twice on the same already-archived employee returns the *exact same* `archived_at` timestamp both times (2-second gap between calls) — the idempotency fix genuinely holds outside the test suite too.
- Story Status → `done`; `sprint-status.yaml` synced.

**Output:** Story file gained a "### Review Findings" subsection (the resolved decision, 8 checked-off patches, 1 checked-off defer with reason, 6 dismissed noted in prose); `deferred-work.md` gained a new `7-5-hr-admin-deletes-or-archives-an-employee-record` heading; `project-context.md` gained a code-review entry.

**Documentation Generated:**
- The story file's Review Findings section, corrected Scope Note 6, updated Test Results block and File List
- A new heading in `deferred-work.md` with a fully-described, `**How to apply:**`-tagged entry
- `project-context.md` gained two new entries (story creation + implementation, and code review)
- Sprint status synced (`7-5-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`)

---

## Files Created/Updated

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/013_add_accounts_archived_at.py` | `accounts.archived_at` column (AR-25) |

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/auth/models.py` | `Account.archived_at` column added |
| `backend/app/auth/repository.py` | `get_account_by_id`, `update_account_archived_at` (guarded, code review), `delete_account` added |
| `backend/app/auth/service.py` | `get_current_user` gained `db` dependency + narrowed archived-Account rejection (AC4) |
| `backend/app/employees/repository.py` | `get_employee_for_update`, `hard_delete_employee`, `archive_employee` added |
| `backend/app/employees/schemas.py` | `EmployeeResponse.has_assignment_history` added; new `DeleteEmployeeResponse` |
| `backend/app/employees/service.py` | `delete_or_archive_employee_service`, `assert_employee_active_for_assignment`, `_has_any_history_for_employee`/`_get_employee_ids_with_any_history` added; self-deletion guard, re-archive idempotency, narrowed/logged `IntegrityError` handling (all code review) |
| `backend/app/employees/router.py` | `DELETE "/{employee_id}"` route added |
| `backend/app/assignments/repository.py` | `list_employees` now excludes archived employees; `assignment_exists_for_employee`/`distinct_employee_ids_with_assignments` added, then broadened (code review) to also cover `assigned_by`/`deleted_by` |
| `backend/app/assignments/service.py` | `has_assignment_history_for_employee`, `get_employee_ids_with_assignment_history` added; `create_assignment_service` calls `assert_employee_active_for_assignment` (AC5) |
| `backend/app/assignments/models.py` | Code review: stale comment on `OrgApiCredential.configured_by` corrected |
| `backend/app/progress/repository.py` | Code review: `ProgressRepository.override_actor_exists_for_employee`/`distinct_employee_ids_with_override_actor_history` added |
| `backend/app/progress/service.py` | Code review: `ProgressService.has_override_actor_history_for_employee`/`get_employee_ids_with_override_actor_history` added |
| `backend/app/content/repository.py` | Code review: `admin_actor_exists_for_employee`/`distinct_employee_ids_with_admin_actor_history` added |
| `backend/app/content/service.py` | Code review: `has_admin_actor_history_for_employee`/`get_employee_ids_with_admin_actor_history` added |
| `backend/tests/test_employees_router.py` | 12 new tests at implementation (all 5 ACs plus 404/403/401) + 5 new tests from code review (self-deletion, re-archive idempotency, assigner-history coverage, 2 `IntegrityError`-backstop tests) |

### Frontend — New Files

| File | Purpose |
|------|---------|
| `frontend/src/features/admin/DeleteArchiveEmployeeModal.tsx` | The Delete/Archive confirmation dialog — branching hard-delete/archive copy per the UX spec's verbatim table, `DeleteEmployeeResponse`-driven success callback |
| `frontend/src/tests/DeleteArchiveEmployeeModal.test.tsx` | 6 tests |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/api/employeesApi.ts` | `EmployeeResponse.has_assignment_history`, `deleteOrArchiveEmployee()` added |
| `frontend/src/pages/hr/EmployeesPage.tsx` | `deletingEmployee` state, `handleDeleteOrArchiveCompleted`, `RowActions`' `onDeleteOrArchive` prop wired at both table and card call sites, `DeleteArchiveEmployeeModal` rendered |
| `frontend/src/features/assignments/AssignmentModal.tsx` | `handleAssign`'s catch branch distinguishes `EMPLOYEE_ARCHIVED` (AC5) with dedicated re-pick guidance copy |
| `frontend/src/tests/EmployeesPage.test.tsx` | 1 pre-existing test split into 2 + 4 new tests (net +4) |
| `frontend/src/tests/EditEmployeeModal.test.tsx` | `has_assignment_history` added to the local `makeEmployee` factory (no behavior change) |
| `frontend/src/tests/AssignmentModal.test.tsx` | 1 new test (AC5's `EMPLOYEE_ARCHIVED` branch) |

### Not Changed (by design)

- `backend/app/employees/models.py` — `archived_at` already existed (Story 7.1)
- `backend/app/main.py` — `employees_router` already mounted (Story 7.2)
- `backend/app/core/db.py`, `backend/app/core/security.py` — used as-is, not modified
- `backend/app/auth/repository.py::authenticate()`/`find_account()` — still only reads `_MOCK_ACCOUNTS`, unrelated to this story's AC4 mechanism

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/7-5-hr-admin-deletes-or-archives-an-employee-record.md` | Story file — 5 ACs, 15 Scope Notes, Dev Notes, Dev Agent Record, Review Findings section |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `7-5-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | New `7-5-hr-admin-deletes-or-archives-an-employee-record` heading, 1 deferred finding |
| `_bmad-output/project-context.md` | Two new entries: story creation + implementation, and code review |
| `documentation/ImplementationStepsForStory7-5.md` | This file |

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `bmad-create-story`
- Three research subagents dispatched in parallel (backend surfaces, frontend surfaces, UX design docs) rather than one sequential pass
- Personally re-verified the single highest-risk claim (the real "Employee picker" endpoint) by reading `assignments/service.py`/`repository.py` directly
- Five explicit, load-bearing design decisions written into numbered Scope Notes rather than left for the dev pass to improvise
- Status → `ready-for-dev`

### Phase 2: Implementation
**Execution:** Direct TDD (Amelia persona)
- 15 tasks executed across three modules in sequence: migration → schemas → employees repository → assignments repository/picker filter → auth repository → auth service (AC4) → employees service (core logic) → router → assignments service (AC5) → backend tests → frontend API client → modal → page wiring → `AssignmentModal.tsx` → frontend tests
- **A real, app-wide-blast-radius regression was caught and fixed mid-implementation**, not left for review: running the full backend suite (not just this story's own new tests) surfaced that the first AC4 design broke 10 pre-existing tests relying on a wide, deliberate "fabricated session identity" testing convention — narrowed the check, confirmed clean
- Full regression clean; live-verified twice — `curl` against a rebuilt Docker backend, and a 14-check ad hoc Playwright browser smoke test covering both UI branches
- Story marked `review`

### Phase 3: Code Review + Decision + Patches
**Skill:** `bmad-code-review`
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor) — Blind Hunter's single most consequential finding (the `has_assignment_history` predictor gap) required a genuine user decision, not just a mechanical fix
- **User chose to expand `has_assignment_history`'s scope now**, implemented as three new cross-module service calls unioned together — the single expanded check now drives both the dialog's prediction and the real decision identically
- 8 other real, fixable issues found and patched: a self-lockout risk (no self-deletion guard), an audit-integrity bug (re-archive not idempotent), a reintroduced known-bug-class (unguarded `db.get()`), a masked-error-class bug (overly broad `except IntegrityError`), a missing test-coverage gap, a dead-parameter/misleading-message bug, and two documentation-accuracy corrections
- 6 findings dismissed, each verified against the actual code rather than taken at face value
- 1 item deferred with reasoning (lock-strength optimization, low urgency at this app's scale)
- Full regression re-verified after patches; both new safeguards (self-deletion, re-archive idempotency) re-verified live against a rebuilt Docker backend a second time
- Story marked `done`

---

## Test Coverage

### New/Extended Test Files (23 tests at implementation, 28 after the code-review patches)

- `test_employees_router.py` — 12 new at implementation: hard-delete (AC1), a unit-level `FOR UPDATE` source-inspection check, archive (AC2), soft-deleted-Assignment-still-counts (AC2), picker-exclusion-vs-roster-inclusion (AC2), `has_assignment_history` accuracy (AC3), two AC4 session-revalidation tests (archive path, and the documented hard-delete scope decision), AC5's stale-picker rejection, role gate (403), and 404 on a nonexistent id — plus 5 new from code review: self-deletion rejection, re-archive idempotency (identical timestamp), an employee who is never a target but *is* an assigner (real end-to-end coverage of the expanded pre-check), and two monkeypatch-based tests directly exercising the now-defensive-only `IntegrityError` backstop
- `DeleteArchiveEmployeeModal.test.tsx` — 6 new: hard-delete copy/button rendering, archive copy/button rendering, confirm calls the API and fires `onCompleted`+`onClose` with the response's action, cancel calls `onClose` without calling the API, a rejected confirm shows an inline error and doesn't close, renders nothing when `employee` is `null`
- `EmployeesPage.test.tsx` — split 1 pre-existing test into 2 (Regenerate Password/+New Employee still stubbed; Delete/Archive no longer is) + 3 new (opens the real modal pre-filled; a completed hard-delete refetches and shows the "removed" toast; a completed archive shows the "archived" toast driven by the response, not the dialog's prediction)
- `AssignmentModal.test.tsx` — 1 new: a `409 EMPLOYEE_ARCHIVED` response shows the re-pick guidance text, not the generic error

### Regression Verification

- Backend: 687 passed after implementation → 692 passed after the code-review patches (675-passed post-Story-7.4 baseline + 12 implementation tests + 5 code-review tests), 2 skipped, 0 failed throughout
- Frontend: 375 passed, 0 failed — unchanged after the code-review patches (all patches were backend-only)
- `tsc --noEmit`: 31 pre-existing errors, none in any file this story touched (confirmed by direct file-list comparison — the touched-file set and the erroring-file set are disjoint)
- `vite build`: clean, 532 modules (up from 531, for the new `DeleteArchiveEmployeeModal.tsx`)
- Live verification, twice, each covering both the implementation and the code-review round: a `curl`-driven pass against a rebuilt Docker backend confirming exact status codes/bodies for all 5 ACs (plus, after the review round, the new self-deletion and idempotency guards), and an ad hoc Playwright browser smoke test confirming the full delete/archive flow in an actual browser for both UI branches

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **Atomic check-then-act via row locking, not SERIALIZABLE isolation** | `get_employee_for_update` takes a `FOR UPDATE` lock, relying on Postgres's FK-driven `FOR KEY SHARE` lock on concurrent Assignment inserts to make the check-then-act race-safe | `employees/repository.py`, `employees/service.py` |
| **`Account.archived_at` mirror to avoid a circular import** | Rather than importing `Employee` into `auth/` for AC4's check, `Account` (auth's own table) gained its own `archived_at`, kept in sync by `employees/service.py`'s archive path — the third and final planned use of the "employees writes into auth's table" exception Story 7.4 first established | `auth/models.py`, `auth/repository.py`, `employees/service.py` |
| **Two-read split to reconcile UX-DR38 with AC1/AC2's atomicity** | `has_assignment_history` (roster-fetch-time preview) and the `DELETE` endpoint's own atomic re-decision are deliberately separate reads — the response's `action` field, not the dialog's prediction, drives the success toast | `employees/schemas.py`, `employees/service.py`, `DeleteArchiveEmployeeModal.tsx`, `EmployeesPage.tsx` |
| **Cross-module reads via each module's service layer, not a repository reach-around (AD-1)** | The expanded `has_assignment_history` check (code review) unions three separate cross-module service calls (`assignments.service`, `progress.service.ProgressService`, `content.service`), each a thin wrapper over its own owned table(s) | `employees/service.py`, `assignments/service.py`, `progress/service.py`, `content/service.py` |
| **AD-6/FR-14 role gate + self-protection** | `delete_or_archive_employee_service` calls `require_hr_admin` first, then rejects self-targeting outright (code review) before any query | `employees/service.py` |
| **Defensive-only backstop, not the primary mechanism** | The `IntegrityError` catch (code review) is narrowed to the actual FK-violation SQLSTATE and logged — a safety net for a future, not-yet-covered FK, not the load-bearing check it originally was | `employees/service.py` |

---

## Key Technical Achievements

✅ **Ran the full create → implement → review → decide → patch → re-verify pipeline in one continuous session**, for a story `epics.md` itself had flagged in advance as unusually large and risky
✅ **Three parallel research agents front-loaded story authoring**, surfacing the single most load-bearing architectural fact (`get_current_user` had no `db` dependency at all) before a line of code was written
✅ **Caught and fixed a real, app-wide-blast-radius regression mid-implementation** by running the full test suite rather than just the story's own new tests — a design that would have broken 10 pre-existing tests across 8 files never shipped
✅ **Code review surfaced a genuine, non-mechanical design gap** (the confirm dialog's predictor was structurally incomplete, not just occasionally stale) and routed it to the user for a real decision rather than silently picking one side
✅ **The chosen fix improved both correctness and elegance simultaneously** — expanding `has_assignment_history` didn't just fix the dialog's copy, it let the actual delete-vs-archive decision skip a guaranteed-to-fail hard-delete attempt for admin-actor employees entirely
✅ **All three review layers independently converged on several of the same real issues** (the unguarded `db.get()`, no self-deletion guard, the broad `except IntegrityError`), giving high confidence they were worth fixing
✅ **Every dismissed finding was verified against the actual code, not taken at face value** — including one (the pagination "empty page" claim) that turned out to be a false positive only visible by reading the derived-state math directly
✅ **Both new safeguards from code review (self-deletion block, re-archive idempotency) were live-re-verified against a rebuilt Docker backend**, not just re-tested at the unit level — including confirming a byte-identical `archived_at` timestamp across two calls
✅ **Zero regressions across every regression run in the session** — implementation, both live verifications, and the code-review re-verification

---

## Deferred Items (Not Story 7-5 Scope)

Logged to `deferred-work.md` under a new `7-5-hr-admin-deletes-or-archives-an-employee-record` heading:

1. **`assert_employee_active_for_assignment` takes a full exclusive `FOR UPDATE` lock for a read-only check**, held for the rest of that request's transaction — two HR Admins concurrently assigning *different* skills to the same, healthy employee now serialize through this lock where they previously wouldn't have. Real but low-urgency given this app's actual concurrency profile; a weaker `FOR KEY SHARE` lock would likely suffice if this is ever revisited.

Carried forward from earlier Epic 7 stories, still open, unaffected by this story:
- `auth/repository.py::authenticate()` still does not read `Account` — unrelated to this story's AC4 mechanism, which works independently of the login path.
- The PRD's own open assumption that a hard-deleted Employee has no restore path while an archived one theoretically could be un-archived — this story deliberately builds no un-archive capability at all (out of scope by design, not an oversight).

---

## Conclusion

Story 7-5 is **✅ DONE** after a full create-then-implement-then-verify-then-review-and-decide-and-patch-then-reverify cycle, run start to finish in one session:

- All 5 acceptance criteria satisfied, verified by 28 dedicated tests (17 backend + 11 frontend) plus two independent live-verification passes (API-level `curl` and a real-browser Playwright smoke test), each pass repeated after the code-review round
- Code review surfaced one genuinely ambiguous design gap (routed to and resolved by the user) plus 8 other real, fixable issues — 6 findings correctly dismissed as false positives or as matching deliberate, already-documented design choices, 1 correctly deferred with reasoning
- Zero regressions across every regression run in the session
- Both code-review safeguards were re-verified live against a rebuilt Docker backend after being fixed, not just re-tested at the unit level
- **Not yet committed to git** — working tree still uncommitted as of this document (`HEAD` at `672d9d77`, same as the story's own `baseline_commit`)

**Epic 7 status:** Stories 7.1, 7.2, 7.3, 7.4, and 7.5 are all `done`. Story 7.6 (HR Admin Regenerates an Employee's Password) is next in the backlog.
