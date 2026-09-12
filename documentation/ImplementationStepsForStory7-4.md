# Implementation Steps for Story 7-4: HR Admin Edits an Employee Record

**Story Key:** 7-4-hr-admin-edits-an-employee-record
**Epic:** 7 (Employee Roster Management) — **fourth story**
**Status:** ✅ DONE
**Completed Date:** 2026-09-11

---

## Overview

Story 7.4 adds the first mutation-of-an-existing-resource endpoint in the `employees/` module: `PATCH /api/admin/employees/{employee_id}` (FR-26), letting an HR Admin edit any Employee's profile fields. Employee ID/Code is immutable (UX-DR39); every other field from Story 7.2's create-time set (Name, Email, Phone, Experience, Technologies, Position, Project, Manager Name, Location, Department) is editable, with no Assignment-history lock (unlike a Skill's permanent identity-lock, FR-21/22) and no optimistic-lock/conflict detection on concurrent edits (last-write-wins, matching this PRD's precedent everywhere else).

No story file existed for 7.4 at the start of this session (it was `backlog` in `sprint-status.yaml`), so this session ran the full pipeline in one continuous pass: create the story, implement it end to end (API + UI), live-verify it twice against a rebuilt Docker backend and a real browser, run it through a 3-layer adversarial code review that found and fixed two genuine bugs, and commit + push the finished result.

The central technical wrinkle — flagged during story authoring and confirmed true during implementation and again during code review — was that this is the *first* story to ever change an existing Employee's email after creation, so every conflict check needed a **self-exclusion** Story 7.2's create-time checks never needed, and `Account.email` (a separate table, `auth/repository.py`) needed a brand-new sync path to avoid drifting from `Employee.email` — a gap Story 7.2's own code review had named this exact future story to close.

---

## Agents Invoked

### 1. **General-purpose research agent (context gathering for story creation)**

**Purpose:** Exhaustively read the real current code (not just prior story docs) before writing the story spec — schemas, repository, service, router, tests, frontend page/API client, the reusable modal pattern, and the UX spec — and report back a structured brief.

**When Invoked:** As the first step of `bmad-create-story`'s exhaustive-analysis phase.

**Key Findings Reported:** exact `CreateEmployeeRequest`/`EmployeeResponse` field shapes and the 409 dual-table conflict-check pattern to extend; that no PATCH/PUT "edit an existing resource" route existed elsewhere in this codebase to mirror exactly (Skills are permanently locked once assigned and never get one); that `auth/service.py::authenticate()` still only reads a hardcoded `_MOCK_ACCOUNTS` dict, so an `Account.email` sync would have no observable login effect yet; the exact `NewSkillModal.tsx`/`Dialog` frontend pattern to reuse for the new edit modal; and that the reference prototype's Edit modal is a simplified 3-field mock, while the markdown UX spec's 10-field list is authoritative.

### 2. **Fresh-context story validator (quality check before `ready-for-dev`)**

**Purpose:** Independently re-derive the story from scratch and catch anything the first pass missed, per `bmad-create-story`'s own checklist discipline.

**When Invoked:** Immediately after the draft story file was written, before marking it `ready-for-dev`.

**Key Findings Identified (2 real issues, both fixed before implementation began):** the planned `EditEmployeeModal.test.tsx` file was pointed at the wrong directory (colocated with the component instead of `frontend/src/tests/`, where `NewSkillModal.test.tsx`/`DeleteSkillModal.test.tsx` actually live); and Task 6/Task 10's test lists had no coverage at all for AC4 (concurrent edits, last-write-wins) despite the Completion Checklist claiming all 4 ACs were covered. A minor duplication note was also raised and addressed in prose: `assignments/repository.py::get_employee_by_id` already exists with an identical signature — confirmed as a deliberate, AD-1-consistent duplication, not an oversight.

### 3. **Blind Hunter (`bmad-review-adversarial-general` skill, via a background subagent)**

**Purpose:** Open-ended adversarial critique of the finished diff — no spec context, no priors.

**When Invoked:** Automatically, as part of the `code-review` workflow's 3-parallel-layer step, once the story reached `review` status.

**Key Findings Identified:** **two real bugs, both empirically reproduced against the live dev DB rather than reasoned about from the diff alone.** (1) `update_employee_service`'s `IntegrityError` backstop read `employee.id` *after* `await db.rollback()` — which expires every attribute on the session's ORM objects — crashing with `sqlalchemy.exc.MissingGreenlet` on a genuine concurrent-write race instead of returning the intended clean `409`; Blind Hunter identified this as a direct regression against an already-established, documented pattern this exact codebase follows elsewhere (`content/service.py` and `skills/service.py`'s own `IntegrityError` backstops both deliberately use a plain id parameter post-rollback for this exact reason). (2) A case-only email edit (e.g. `Jane@x.com` → `jane@x.com`) never synced `Account.email`, since the sync was gated on a case-*insensitive* comparison while the raw-cased value was always written to `Employee.email`. Also flagged, all later deferred or dismissed: an unguarded `db.get(Account, id)` with no `None` check; no blank/whitespace validator on 8 optional schema fields; no client-side email-format validation (a claim about the resulting error shape was later verified false — this codebase already normalizes every validation error into one envelope); no required-field markers on Name/Email; no `aria-describedby` on the duplicate-email notice; a "not truly concurrent" critique of the AC4 test; a single-field `extra="forbid"` test coverage critique; and a "missing success toast" critique.

### 4. **Edge Case Hunter (`bmad-review-edge-case-hunter` skill, via a background subagent)**

**Purpose:** Method-driven walk of every branching path and boundary condition — orthogonal to Blind Hunter's attitude-driven pass.

**When Invoked:** Same trigger, launched in parallel with Blind Hunter and the Acceptance Auditor.

**Key Findings Identified (3 items, JSON-formatted with location/trigger/guard/consequence):** independently confirmed the same case-only-email-drift bug Blind Hunter found; the same unguarded `db.get(Account, id)` None-check gap; and a note about `UpdateEmployeeRequest`'s optional fields silently defaulting to `null` when omitted — assessed during triage as matching the story's own explicit full-replace-body design (Scope Note 1), not a defect.

### 5. **Acceptance Auditor (custom prompt, via a background subagent)**

**Purpose:** Cross-check the diff against the story's own spec — 4 Acceptance Criteria and 11 Scope Notes — and sanity-check the Dev Agent Record's claims against what the diff actually contains.

**When Invoked:** Same trigger, `review_mode = "full"` since the story file was set as `{spec_file}`.

**Result:** **No AC or Scope Note violations found.** Independently caught the same case-only-email-drift bug (the third layer to find it). Also caught two real documentation-accuracy issues purely by checking the diff's actual content against the Dev Agent Record's prose: Task 4's own subtasks were left unchecked despite being fully implemented, and the frontend test-count arithmetic was wrong (stated "343-passed baseline + 21 new tests," but the real numbers were a 355 baseline + 9 new — the final 364 total happened to be correct regardless, since it was independently measured, not derived from the wrong arithmetic).

---

## Skills Invoked

### 1. **`bmad-create-story` (story creation)**

**Purpose:** Produce a comprehensive story file for 7.4 from scratch — none existed yet, only the epic's raw AC text.

**When Invoked:** Explicit user instruction via `/bmad-agent-dev`: "start development api and ui for the story 7-4-hr-admin-edits-an-employee-record and refer the ux design if required."

**Workflow Steps Executed:**
1. Confirmed via `sprint-status.yaml` and a glob of `implementation-artifacts/` that 7.1–7.3 were `done` and 7.4 had no story file yet — the natural next pick.
2. Read Epic 7's Story 7.4 AC text from `epics.md` (4 ACs plus a Dev Notes callout flagging this story as larger/riskier than typical single-module CRUD).
3. Dispatched a research subagent to read the real current code in full (schemas, repository, service, router, models, `auth/repository.py`, the frontend page/API client, `NewSkillModal.tsx`, `dialog.tsx`, and the existing test file) rather than relying on prior story docs alone.
4. Personally re-verified the highest-risk claims by reading the actual files directly (`employees/schemas.py`, `service.py`, `repository.py`, `router.py`, `models.py`, `auth/repository.py`, `EmployeesPage.tsx`, `employeesApi.ts`, `NewSkillModal.tsx`, `dialog.tsx`) before writing a single line of the story, per this skill's "read files being modified, non-negotiable" instruction.
5. Wrote 11 Scope Notes covering: the greenfield PATCH route shape, `employee_code` immutability as a schema-level omission, reusing `EmployeeResponse` as-is, the self-excluding dual-table email-conflict check, the deliberately-unfixed login-doesn't-read-Account gap, no Assignment-history lock, no optimistic lock, the `NewSkillModal`/`Dialog` frontend pattern to mirror, `refetch()`-not-reload for the list refresh, touching only the Edit action's handler, and the prototype's under-scoped 3-field mock vs. the markdown spec's authoritative 10-field list.
6. Ran a fresh-context validation pass against the draft story (see **Agents Invoked** #2 above) and applied both real fixes before finalizing.
7. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `7-4-...` entry updated from `backlog` to `ready-for-dev`.

**Output File:** `_bmad-output/implementation-artifacts/7-4-hr-admin-edits-an-employee-record.md`
**Sprint Status:** `7-4-...`: `backlog` → `ready-for-dev`

---

### 2. **Direct TDD implementation (Amelia persona, `bmad-dev-story` execution)**

**Purpose:** Execute the story's 10 tasks in sequence — backend PATCH endpoint, frontend edit modal, wiring, and tests for both.

**When Invoked:** Continuing directly from story creation in the same session (no separate user prompt needed).

**Workflow Steps Executed:**

1. **Red phase confirmed first:** wrote all 11 new `test_update_employee_*` router tests before touching any implementation code; ran them and confirmed all 11 failed with `404 Not Found` (no `PATCH /{employee_id}` route existed yet).
2. **Task 1 — Schema:** `UpdateEmployeeRequest` — `CreateEmployeeRequest`'s field set minus `employee_code`, same `max_length`s and `_reject_blank` validator, `extra="forbid"`.
3. **Task 2 — Repository:** `get_employee_by_id`, `get_employee_by_email_ci_excluding_id` (the self-exclusion Story 7.2 never needed), `update_employee` (plain `setattr` loop + flush/refresh, relying on the model's existing `onupdate=func.now()` for `updated_at`).
4. **Task 3 — Auth repository:** `get_account_by_email_ci_excluding_id` and `update_account_email` — the new cross-module write Story 7.2's own code review had named this story to add, following `create_account`'s established centralization pattern.
5. **Task 4 — Service:** `_not_found` (404 `EMPLOYEE_NOT_FOUND`) and `update_employee_service` — `require_hr_admin` gate, 404-on-missing, self-excluding conflict pre-check, apply the update, sync `Account.email` if it changed, an `IntegrityError` backstop re-checking both tables (self-excluded) mirroring `create_employee_service`'s exact shape.
6. **Task 5 — Router:** `PATCH "/{employee_id}"` → `update_employee_route`, `response_model=EmployeeResponse`.
7. **Green phase:** all 11 new backend tests passed on the first implementation attempt.
8. **Task 7 — Frontend API client:** `UpdateEmployeeRequest` TS interface + `updateEmployee(id, payload)` in `employeesApi.ts`.
9. **Task 8 — Edit modal:** `frontend/src/features/admin/EditEmployeeModal.tsx` — mirrors `NewSkillModal.tsx`'s `Dialog`/`requestIdRef`/409-branching pattern directly; Employee ID/Code renders as a disabled `Input`; all 10 other fields editable; a `data-testid="edit-employee-duplicate-notice"` block for the 409 case.
10. **Task 9 — Wire into `EmployeesPage.tsx`:** new `editingEmployee` state; `RowActions` gained an `onEdit` prop wired **only** to the Edit button (Regenerate Password/Delete-Archive untouched, still on the stub toast); `handleEmployeeSaved` calls the page's existing `refetch()` and closes the modal.
11. **Task 10 — Frontend tests:** 7 new tests in `EditEmployeeModal.test.tsx`, 2 new tests in `EmployeesPage.test.tsx`, plus 1 pre-existing `EmployeesPage.test.tsx` test rewritten (it had asserted Edit showed the stub toast — no longer true). All passed on the first run.
12. **Full regression:** backend 673 passed/2 skipped/0 failed (662-passed post-Story-7.3 baseline + 11 new); frontend 364 passed/0 failed; `tsc --noEmit` byte-identical to a 73-pre-existing-error baseline (verified via `git stash -u` A/B comparison — higher than Story 7.3's recorded 31 because `project-context.md`'s own update log has a gap across Stories 6.6–7.3, noted explicitly rather than silently ignored); `vite build` clean at 531 modules (up from 530).
13. **Live-verified twice, not just at the test level.** First via `curl` against a rebuilt `talentpilot-api` Docker container, logged in as the real seeded Rita account: confirmed `200` on a full field edit (with `updated_at` genuinely bumped), `422` on an `employee_code` in the body, `404 EMPLOYEE_NOT_FOUND` on a random UUID, `403 FORBIDDEN_NOT_HR_ADMIN` as Casey, and `401` unauthenticated — cleaning up the test row from the dev DB afterward. Second, an ad hoc Playwright/Chromium smoke test (disposable `playwright-core` install against a pre-existing local Chromium cache, uninstalled after use; the resulting `package-lock.json` metadata churn was reverted via `git checkout` so no net lockfile change was retained) against a real `vite` dev server proxying to the rebuilt backend: opened Edit on a real roster row, confirmed the ID/Code field is disabled, edited Name + Department, saved, confirmed the roster updated in place with no navigation/reload, then reverted the seeded employee back to its original values so the demo dataset wasn't left mutated. All 8 checks passed.
14. Filled in the story file's Dev Agent Record, File List, Completion Checklist, and Change Log; Status → `review`.

**Output File:** `_bmad-output/implementation-artifacts/7-4-hr-admin-edits-an-employee-record.md`
**Sprint Status:** `7-4-...`: `ready-for-dev` → `review`

---

### 3. **`bmad-code-review` (3-layer adversarial review + patch application)**

**Purpose:** Independent adversarial verification of the finished implementation, followed by resolving every finding.

**When Invoked:** `/bmad-code-review` command, no argument — resolved via Tier 2 (recent conversation: the just-finished Story 7.4 implementation).

**Workflow Steps Executed:**

- Constructed the diff from uncommitted changes (`git diff HEAD`, plus `git add -N` to include the 3 untracked new files in the diff without actually staging their content) — 1,509 lines total, well under the chunking threshold.
- Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor in parallel as background subagents (see **Agents Invoked** above); all three completed and reported back independently, each pointed at the raw `git diff HEAD` rather than a pasted diff string, to keep them genuinely cold and unbiased by the main session's framing.
- **Triaged 12 unique findings** (after deduplication — 3 layers independently found the same case-only-email-drift bug) by reading the actual current code at each location before rating severity, not from the diff hunk alone: `0 decision-needed`, `4 patch`, `4 defer`, `4 dismiss`.
- **Patches, user chose "apply every patch":**
  1. Fixed the `IntegrityError` backstop to use the already-available `employee_id` function parameter instead of the post-rollback-expired `employee.id` — closing the `MissingGreenlet` crash. A new regression test (`test_update_employee_account_side_email_conflict_returns_409_not_500`) deterministically reaches this exact path using the same account-side-desync technique Story 7.2's own test already established, rather than needing genuine concurrency.
  2. Fixed the email-sync condition to compare the raw (case-sensitive) email value captured *before* `repository.update_employee` mutates the ORM object in place, so a case-only edit now correctly syncs `Account.email` too. A new regression test (`test_update_employee_case_only_email_change_still_syncs_account_email`) covers this exactly.
  3. Corrected the story file's own Task 4 checkboxes (implemented and tested, but left unchecked).
  4. Corrected the Dev Agent Record's frontend test-count arithmetic (stale 343-baseline → the real 355; mislabeled 21-new → the real 9-new; the final 364 total was already right).
- **Dismissed as false positives, each verified rather than argued away:** a claim that a `422` from an invalid `EmailStr` reaches the frontend in FastAPI's raw `{"detail": [...]}` shape — checked against `core/errors.py` directly and found false, since `register_exception_handlers` already normalizes every validation error codebase-wide; a "not truly concurrent" critique of the AC4 test that matches the story's own Scope Note 7 and this codebase's universal precedent for last-write-wins testing; a misunderstanding of `extra="forbid"`'s uniform, model-level (not per-field) scope; and a "missing success toast" critique that AC3's own text explicitly rules out.
- **4 items deferred** to `deferred-work.md`, each tagged with why: an unguarded `db.get(Account, id)` (currently unreachable — AR-24 guarantees every Employee has a paired Account, no delete path exists yet); no blank-string validator on 8 optional schema fields (pre-existing, mirrors `CreateEmployeeRequest`); no required-field marker and no `aria-describedby` on the modal (both pre-existing, mirror `NewSkillModal.tsx`'s identical patterns).
- Re-ran the full regression suite after all patches: backend 675 passed/2 skipped/0 failed (673 + 2 new regression tests), frontend unchanged at 364 passed/0 failed.
- **Both real-bug fixes re-verified live a second time** against a freshly rebuilt Docker backend, not just the test suite: a case-only email `PATCH` now shows `Account.email` genuinely updated (confirmed via a direct `psql` query), and the same account-side-desync technique that previously crashed with `MissingGreenlet` now returns a clean `409 EMPLOYEE_EMAIL_CONFLICT`.

**Output:** Story file gained a "### Review Findings" subsection (4 checked-off patches, 4 checked-off defers with reasons, 4 dismissed noted in prose) and a "### Code Review Patches" completion-notes addendum; `deferred-work.md` gained a new `7-4-hr-admin-edits-an-employee-record` heading with all 4 deferred items in the ledger's established format. Story status → `done`; `sprint-status.yaml` updated to match.

**Documentation Generated:**
- The story file's Review Findings section, Code Review Patches notes, corrected Test Results block, and updated File List
- A new heading in `deferred-work.md` with 4 fully-described, `**How to apply:**`-tagged entries
- `project-context.md` gained two new entries (story creation + implementation, and code review) documenting the session's work and its real findings
- Sprint status synced (`7-4-...`: `backlog` → `ready-for-dev` → `review` → `done`)

---

### 4. **Git commit and push**

**Purpose:** Persist the finished, reviewed story to the shared branch.

**When Invoked:** Explicit user instruction: "commit and push the changes with proper comments."

**Workflow Steps Executed:**
- Reviewed `git status`/`git diff` to confirm exactly which files belonged to this story (15 files: 3 new, 12 modified) — no stray or unrelated changes included.
- Staged all 15 files explicitly by name (not `git add -A`).
- Committed with a message following this repo's established convention: an imperative summary line naming the FR, a paragraph on what was built and what precedent it mirrors, and a paragraph naming the code-review outcome (layers used, real bugs found and fixed, items deferred/dismissed, final test counts).
- Pushed to `origin/POC_Hackathon_V1`.

**Output:** Commit `672d9d77` (`1c8f45b7..672d9d77`), pushed to `origin/POC_Hackathon_V1`, working tree clean.

---

## Files Created/Updated

### Backend — New Files

*(none — this story extended the existing `employees/`/`auth/` module scaffold and test file from Stories 7.1/7.2/7.3)*

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/employees/schemas.py` | `UpdateEmployeeRequest` added |
| `backend/app/employees/repository.py` | `get_employee_by_id`, `get_employee_by_email_ci_excluding_id`, `update_employee` added |
| `backend/app/employees/service.py` | `_not_found`, `update_employee_service` added; code review: `IntegrityError` backstop now uses `employee_id` instead of the post-rollback-expired `employee.id`; email-sync condition changed to a pre-mutation raw comparison so case-only edits sync `Account.email` too |
| `backend/app/employees/router.py` | `PATCH "/{employee_id}"` → `update_employee_route` added |
| `backend/app/auth/repository.py` | `get_account_by_email_ci_excluding_id`, `update_account_email` added |
| `backend/tests/test_employees_router.py` | 13 new `test_update_employee_*` tests: 11 at implementation covering all 4 ACs plus 404/403/401/archived-employee/extra-forbid cases, + 2 code-review regression tests |

### Frontend — New Files

| File | Purpose |
|------|---------|
| `frontend/src/features/admin/EditEmployeeModal.tsx` | The Edit panel — read-only Employee ID/Code, all 10 editable fields, 409-duplicate-email notice, `requestIdRef` staleness guard |
| `frontend/src/tests/EditEmployeeModal.test.tsx` | 7 tests covering AC1 (pre-fill, read-only ID), AC2 (409 notice), submit payload shape, reset-on-reopen, close behavior |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/api/employeesApi.ts` | `UpdateEmployeeRequest` interface, `updateEmployee()` added |
| `frontend/src/pages/hr/EmployeesPage.tsx` | `editingEmployee` state, `handleEmployeeSaved`, `RowActions`'s `onEdit` prop wired only to the Edit button, `EditEmployeeModal` rendered |
| `frontend/src/tests/EmployeesPage.test.tsx` | 1 pre-existing test rewritten (Edit no longer shows the stub toast) + 2 new Story 7.4 tests |

### Not Changed (by design)

- `backend/app/employees/models.py` — Story 7.1's schema already has everything this story needs (`updated_at`'s `onupdate=func.now()` already bumps automatically)
- `backend/app/auth/models.py`, `backend/app/auth/service.py` — `authenticate()` deliberately untouched (still `_MOCK_ACCOUNTS`-only); no schema change needed on `Account`
- `backend/app/main.py` — `employees_router` already mounted (Story 7.2)

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/7-4-hr-admin-edits-an-employee-record.md` | Story file — 4 ACs, 11 Scope Notes, Dev Notes, Dev Agent Record, Review Findings section |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `7-4-...`: `backlog` → `ready-for-dev` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | New `7-4-hr-admin-edits-an-employee-record` heading, 4 deferred findings |
| `_bmad-output/project-context.md` | Two new entries: story creation + implementation, and code review |
| `documentation/ImplementationStepsForStory7-4.md` | This file |

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `bmad-create-story`
- Dispatched a research subagent to read the real current code in full before writing a single line of the spec, rather than relying on prior story docs
- Personally re-verified the highest-risk claims by reading `schemas.py`/`service.py`/`repository.py`/`router.py`/`models.py`/`auth/repository.py`/`EmployeesPage.tsx`/`employeesApi.ts`/`NewSkillModal.tsx`/`dialog.tsx` directly
- A fresh-context validator caught and fixed a wrong test-file location and a missing AC4 test task before the story was marked ready
- Status → `ready-for-dev`

### Phase 2: Implementation
**Execution:** Direct TDD (Amelia persona)
- Red phase confirmed (11 failing tests, all `404`) before any implementation code was written
- 10 tasks executed in sequence: schema → repository → auth-repository → service → router → tests → frontend API client → modal → page wiring → frontend tests
- All 21 new/rewritten tests (11 backend + 10 frontend) passed on the first run
- Full regression clean; `tsc`/`vite build` unchanged against baseline
- Live-verified twice — once via `curl` against a rebuilt Docker backend, once via an ad hoc Playwright browser smoke test — including reverting the seeded demo employee back to its original values afterward
- Story marked `review`

### Phase 3: Code Review + Patches
**Skill:** `bmad-code-review`
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor) — Blind Hunter reproduced two real bugs live against the dev DB rather than reasoning about them; all three independently converged on the same case-only-email-drift bug
- 12 unique findings triaged: 0 decision-needed, 4 patches (all applied), 4 deferred (logged with reasons), 4 dismissed as false positives or already-documented design choices
- Both real bugs fixed with new regression tests and re-verified live a second time against a rebuilt Docker backend
- Full regression re-verified after patches: zero new failures
- Story marked `done`

### Phase 4: Commit and Push
- 15 files staged explicitly by name, committed with a message following this repo's established convention, pushed to `origin/POC_Hackathon_V1`

---

## Test Coverage

### New/Extended Test Files (21 tests at implementation, 23 after the code-review patches)

- `test_employees_router.py` — 13 new: full-field edit (AC1), edit regardless of real Assignment history (AC1/no-lock), `employee_code`-in-body rejection (422), duplicate-email 409 (AC2), self-exclusion on unchanged email (AC2), email-change syncs `Account.email` (AC2), 404 on a nonexistent id, 403 (EMPLOYEE session), 401 (unauthenticated), archived-employee edit still succeeds, two-sequential-edits last-write-wins (AC4), plus 2 code-review regression tests (case-only email sync, account-side `IntegrityError` backstop)
- `EditEmployeeModal.test.tsx` — 7 new: read-only pre-filled Employee ID/Code, submitted payload never includes `employee_code`, 409 duplicate-email notice, generic non-409 error message, reset-on-reopen-for-a-different-employee, close-button behavior, renders nothing when closed/no employee
- `EmployeesPage.test.tsx` — 2 new (Edit opens the modal pre-filled; a successful save updates the roster live without a full page reload) + 1 rewritten (Regenerate Password/Delete-Archive still show the stub toast; Edit no longer does)

### Regression Verification

- Backend: 673 passed after implementation → 675 passed after the code-review patches (662-passed post-Story-7.3 baseline + 11 implementation tests + 2 code-review regression tests), 2 skipped, 0 failed throughout
- Frontend: 364 passed, 0 failed — both after implementation and unchanged after the code-review patches (both patches were backend-only)
- `tsc --noEmit`: 73 pre-existing errors, byte-identical before and after this story's entire change set (verified via `git stash -u` A/B comparison)
- `vite build`: clean, 531 modules, both before and after patches
- Live verification, twice: a `curl`-driven pass against a rebuilt Docker backend confirming exact `200`/`422`/`404`/`403`/`401` behaviors, and an ad hoc Playwright browser smoke test confirming the full edit→save→roster-updates-live flow — each real-bug fix from code review was independently re-verified live a second time after the patches landed

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **Greenfield PATCH route, full-replace body** | `PATCH /api/admin/employees/{employee_id}` takes a complete editable-field body every time — not JSON-merge-patch partial semantics — since the Edit modal always submits the full form | `employees/router.py`, `employees/schemas.py` |
| **AD-1 — single-owner data module, one documented exception** | All new `employees` table writes/reads stay in `employees/repository.py`; the one new `accounts` table write (`update_account_email`) mirrors `create_account`'s existing, explicitly-named exception — the second and last planned use of it | `employees/repository.py`, `auth/repository.py` |
| **AD-6/FR-14 role gate** | `update_employee_service` calls `require_hr_admin(current_user)` before any query, matching every other `/api/admin/*` mutation endpoint | `employees/service.py` |
| **Self-exclusion on every conflict check** | Both the pre-check and the `IntegrityError` backstop exclude the Employee/Account being edited by id — the one genuinely new wrinkle vs. Story 7.2's create-time checks, which never had a prior row to exclude | `employees/service.py`, `employees/repository.py`, `auth/repository.py` |
| **No lock, unlike Skills** | The update service never queries `assignments`/`assignment_overrides` at all — verified end-to-end with a real Assignment fixture, not just by absence of code | `employees/service.py` |
| **Reuse, don't reinvent, the modal pattern** | `EditEmployeeModal.tsx` mirrors `NewSkillModal.tsx`'s `Dialog`/`requestIdRef`/409-branching idioms directly | `EditEmployeeModal.tsx` |

---

## Key Technical Achievements

✅ **Ran the full create → implement → review → patch → commit pipeline in one continuous session**, starting from a story that didn't exist yet and a sprint-status entry still at `backlog`
✅ **Identified and closed a cross-story gap by name** — `auth/repository.py::update_account_email`, which Story 7.2's own code review had flagged months earlier as this exact future story's job
✅ **A fresh-context validation pass caught two real story-quality issues before a single line of implementation code was written** — a wrong test-file location and a missing AC4 test task
✅ **All 21 new/rewritten tests passed on the first implementation run** — a direct result of thorough story authoring against real, freshly-read code rather than assumptions
✅ **Live-verified end-to-end twice, in two different ways** — a `curl`-driven API pass and a real-browser Playwright pass — and reverted the seeded demo data cleanly afterward both times
✅ **Blind Hunter found two real bugs by empirically reproducing them against the live dev database**, not by reasoning about the diff — a `MissingGreenlet` crash on a genuine concurrent-write race, and a case-only email edit silently drifting `Employee.email` and `Account.email` apart
✅ **All three review layers independently converged on the same email-drift bug**, giving high confidence it was real and worth fixing rather than a single reviewer's misreading
✅ **Both real bugs were fixed with dedicated, deterministic regression tests** (no need for genuine concurrency — the same account-side-desync technique already established by Story 7.2's own test suite reliably reaches the `IntegrityError` path) and **re-verified live a second time** after the patches landed
✅ **Zero regressions across every regression run** — implementation, both live verifications, and the code-review re-verification
✅ **Two documentation-accuracy errors in the Dev Agent Record's own self-reported numbers were caught and corrected** by the Acceptance Auditor, rather than the story quietly shipping with a wrong test-count claim

---

## Deferred Items (Not Story 7-4 Scope)

All 4 logged to `deferred-work.md` under a new `7-4-hr-admin-edits-an-employee-record` heading:

1. **`auth/repository.py::update_account_email`'s unguarded `db.get(Account, id)`** — would crash with a raw `AttributeError` (500) if no matching `Account` row existed. Currently unreachable: AR-24 guarantees every Employee gets a paired Account atomically at creation, and no delete/archive path exists yet (Story 7.5).
2. **`UpdateEmployeeRequest`'s 8 optional string fields have no blank/whitespace validator** — pre-existing, mirrors `CreateEmployeeRequest`'s identical gap from Story 7.2, not introduced or worsened here.
3. **Name/Email carry no visual or `aria-required` marker** distinguishing them as required in the Edit modal — pre-existing, mirrors `NewSkillModal.tsx`'s identical gap.
4. **The duplicate-email notice has no `aria-describedby`/`role="alert"` association** with the Email input — pre-existing, mirrors `NewSkillModal.tsx`'s identical pattern verbatim.

Carried forward from earlier Epic 7 stories, still open, unaffected by this story:
- `auth/repository.py::authenticate()` still does not read `Account` — an edited Employee's new email has no observable effect on login until a future story wires that path for real.
- `project-context.md`'s update log still has a documented gap across Stories 6.6–7.3 (noted, not backfilled).

---

## Conclusion

Story 7-4 is **✅ DONE** after a full create-then-implement-then-verify-then-review-and-patch-then-ship cycle, run start to finish in one session:

- All 4 acceptance criteria satisfied, verified by 23 dedicated tests (13 backend + 10 frontend) plus two independent live-verification passes (API-level `curl` and a real-browser Playwright smoke test)
- Code review found 12 unique issues across 3 parallel layers; 4 real fixes applied (2 genuine bugs with dedicated regression tests, 2 documentation corrections), 4 correctly deferred with reasons, 4 correctly dismissed as false positives or as matching deliberate, already-documented design choices
- Zero regressions across every regression run in the session
- Both real bugs found by code review were re-verified live against a rebuilt Docker backend after being fixed, not just re-tested at the unit level
- Committed (`672d9d77`) and pushed to `origin/POC_Hackathon_V1`

**Epic 7 status:** Stories 7.1, 7.2, 7.3, and 7.4 are all `done`. Story 7.5 (HR Admin Deletes or Archives an Employee Record) is next in the backlog.
