# Implementation Steps for Story 10-1: Seeded HR Admin's Login Identity Becomes Sails Admin

**Story Key:** 10-1-persona-rename-and-id-only-identity-references
**Epic:** 10 (Post-MVP Admin & Roster Refinements) — 1 of 16 stories, **epic now in-progress**
**Status:** ✅ DONE (code-reviewed; not yet committed to git)
**Completed Date:** 2026-09-16

---

## Overview

Story 10.1 is the first story in Epic 10 and, per the Sprint Change Proposal's own build order, deliberately sequenced first (alongside Story 10.10) so that later Epic 10 stories' fixtures target the final seed shape rather than the old one. The story renames the seeded HR Admin's *real* login identity — `rita@sails.example.com` / "Rita the Recommender" → `admin@sails.example.com` / "Sails Admin" — so the shipped system's real account doesn't read as a demo/prototype artifact. The PRD's own *narrative* persona name "Rita" (§2.1, UJ-1, UJ-3) is explicitly untouched; only the concrete seeded `Employee`/`Account` rows and their real login/display values change.

No story file existed yet for 10.1 (Epic 10 had only been added to `sprint-status.yaml` as `backlog` blocks during `bmad-correct-course`, per the 2026-09-15 Sprint Change Proposal). This session ran `bmad-create-story` first, then `bmad-dev-story`, then `bmad-code-review`, all in one continuous pass.

The user's request was explicit: "start implementation for both API and UI ... if required refer the UX design." A full-codebase grep for the old identity (case-insensitive `rita`) during story creation found **32 backend files and 15+ frontend files** referencing it — the epics.md AC's own estimate ("~15 backend test files") was confirmed as approximately, not exactly, right, and the session enumerated the exact final list (15 backend test files, none more or fewer) before implementation started, exactly as the AC itself demanded ("full list enumerated in this story's Dev Notes before implementation starts, not discovered mid-story"). No dedicated UX-scenario doc exists for this story (confirmed via the Sprint Change Proposal's own §"UI/UX" note — "no formal UX-scenario doc covers any of these 11 items"), so the story's UI scope was derived directly from a full-codebase grep rather than a design artifact.

Two real, undocumented gaps were found during implementation that the epics.md AC text never mentioned:

1. **A live UI contact link and nav literal both hardcoded the old identity.** `AssignmentCard.tsx`'s "no recommended content" empty state renders a real `mailto:rita@sails.example.com` link with visible text "Contact Rita" — a genuine contact affordance pointing at the real seeded admin, not narrative content, so in scope. `HrAppShell.tsx`'s top-right user menu hardcodes literal text "Rita" and avatar initial "R" — confirmed via `AskUserQuestion` to be a static literal, not derived from the logged-in user's real identity at all (the login response carries only `role`/`user_id`, no name). The user was asked whether to do a minimal literal rename or wire the nav to the real authenticated user's name (a bigger, auth-contract-touching change); **chose the minimal literal rename**, keeping this story inside its documented boundary.
2. **A real idempotency bug in `create_default_accounts()`,** found only by actually running the full backend suite after making the seed change: the existence check was keyed on `Account.email`, which silently breaks the moment the checked email itself changes — a pre-existing row under the old email no longer matches, and the insert then collides on `accounts_pkey` (same `id`). Fixed by keying on `Account.id` instead, consistent with `seed_employees()`'s own pattern.

Code review then found the fix above was incomplete: the id-keyed check stops the crash, but it still never *corrects* an already-seeded row's stale fields — meaning the rename only actually took effect on a brand-new database, not on this repo's own persistent local dev DB (the exact database the implementation session had already hit the crash against). All three independent review layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor) converged on this same finding. Presented to the user as a decision-needed item with three options (Alembic data migration / make the seed functions self-correcting / accept as a documented local-pilot limitation); **user chose the Alembic data migration**, matching this project's own existing convention (migration 011's scoped `password_hash` backfill).

---

## Agents Invoked

### 1. Blind Hunter (`bmad-review-adversarial-general` skill, background subagent)

**Purpose:** Open-ended adversarial critique of the finished diff — no spec context, no priors.

**When Invoked:** Part of `bmad-code-review`'s 3-parallel-layer step, once the story reached `review` status.

**Key Findings Identified:** The seed-rename-doesn't-propagate bug (see Overview) — independently arrived at the same root cause as the other two layers. Also flagged: a stale `seed_ids.py` module docstring still listing "Rita" among the demo account names; unverifiable self-reported regression numbers (no external CI); the fact that the clean regression run depended on an out-of-band manual DB password-hash fix documented in the Debug Log; the PRD/product persona split having no cross-reference (investigated and found to already be documented in AC1 and the story's own Dev Notes — dismissed as a false positive); AC4's "live resolution" claim being asserted by a literal-string test rather than proven (investigated and found to already be proven by a *different*, pre-existing test that logs in as two distinct real admins — dismissed as a false positive); the new `AssignmentCard.tsx` contact link reproducing the same hardcoded-identity pattern as the bug being fixed (an architecturally valid observation, but explicitly in-scope per AC5 and consistent with the same-session `HrAppShell.tsx` precedent — deferred as a future-story concern, not a defect in this diff); the `HrAppShell.tsx` literal misrepresenting any future second HR_ADMIN (the exact tradeoff the user had just confirmed via `AskUserQuestion` — dismissed, not new information); "cosmetic" leftover "Rita" variable names in two test files actually misleading a future reader (upheld as a real, if low-severity, documentation-accuracy issue); the story's own status transition having no separate reviewer step reflected in the diff (dismissed — this code-review pass *is* that step); reworded (not 1:1 substituted) comments in `test_admin_api_keys_router.py` (investigated and confirmed meaning-preserving — dismissed); no direct regression test for the exact idempotency bug fixed (upheld).

### 2. Edge Case Hunter (`bmad-review-edge-case-hunter` skill, background subagent)

**Purpose:** Method-driven walk of every branching path and boundary condition — orthogonal to Blind Hunter's attitude-driven pass.

**When Invoked:** Same trigger, launched in parallel with Blind Hunter and the Acceptance Auditor.

**Key Findings Identified:** One precise, independently-derived finding matching the other two layers exactly — `create_default_accounts()` at `backend/app/core/seeds.py:274-283` doesn't update an already-existing row's email/name when the check passes, with a concrete guard-snippet suggestion (update the row's fields inside the `if existing.scalar():` branch rather than returning unchanged). Its narrow, single-finding output was the most surgically precise of the three layers and became the base finding the other two layers' prose was merged into during triage.

### 3. Acceptance Auditor (custom prompt, background subagent)

**Purpose:** Cross-check the diff against the story file's own ACs, Tasks, and Dev Notes (full `review_mode`, spec file read directly).

**When Invoked:** Same trigger, full review mode against the story file as spec.

**Key Findings Identified:** The same seed-rename-doesn't-propagate gap, framed explicitly as an AC1 violation ("only satisfied for a brand-new database... not for the story's own dev/test environment as described in its Debug Log") — the third independent corroboration of this finding. Also found a genuine internal-consistency defect the other two layers missed: **Task 9's own "zero remaining matches" completion claim was factually false** — `frontend/src/tests/Login.test.tsx:88` and `frontend/src/tests/authApi.test.ts:20,23` both still contained the literal old email, and neither was listed in the Dev Notes "Out of scope" section or the File List. Confirmed via direct inspection that both are functionally harmless (both mock the `login`/`authApi` calls rather than hitting the real seed), but the story's own audit trail was simply wrong — the auditor also explicitly checked that no production-facing `Login.tsx` component code hardcodes the email (confirmed clean) before settling on this being purely a documentation-accuracy gap.

---

## Skills Invoked

### 1. `bmad-agent-dev` (Amelia persona activation)

**Purpose:** Activate the Senior Software Engineer persona for test-first implementation.

**When Invoked:** `start implementation for both API and UI for the story 10-1-persona-rename-and-id-only-identity-references if required refer the UX desing`. The user's initial message already named a clear intent mapping to the `bmad-dev-story` menu item, so the greeting/menu was skipped and dispatch happened directly — but `bmad-dev-story` immediately found no story file existed yet and the sprint-status entry was `backlog`, not `ready-for-dev`, so `bmad-create-story` was run first.

### 2. `bmad-create-story`

**Purpose:** Produce a comprehensive, implementation-ready story file for 10.1, since none existed yet.

**When Invoked:** Immediately after discovering no story file/`ready-for-dev` status existed.

**Workflow Steps Executed:**
1. Read Epic 10's Story 10.1 section directly from `epics.md` (lines 2936–2958) — 5 ACs already fully authored there (the sprint-status.yaml's own note confirmed `bmad-create-epics-and-stories` had already given every Epic 10 story full ACs before this session started).
2. Read the 2026-09-15 Sprint Change Proposal for background/rationale on item #1, and noted the proposal's original suggestion to update the PRD glossary had been deliberately narrowed away by the time `epics.md`'s final AC1 was written — the PRD's narrative persona is explicitly out of scope.
3. Ran an exhaustive case-insensitive `grep -ri rita` across the entire `backend/` and `frontend/src/` trees (found 32 and 15+ files respectively) and classified every single hit as in-scope (real seed-identity coupling — `_login()` defaults, literal email assertions, live UI text) or out-of-scope (synthetic Employee objects, fabricated JWT test payloads, unused mock fixture fields, the PRD's own narrative persona, the `seed_ids.py` symbol name) before writing a single line of Dev Notes.
4. Read `backend/app/core/seeds.py`, `backend/app/core/seed_ids.py`, and a sample of the affected test files directly to confirm the exact literal values and line-level shape of every planned change.
5. Found, during this grep pass (not from the AC text), the two live UI surfaces later confirmed via `AskUserQuestion` (`AssignmentCard.tsx`'s contact link, `HrAppShell.tsx`'s nav literal).
6. Wrote a Tasks/Subtasks list enumerating all 9 tasks with exact before/after literal values per file, and a Dev Notes "Out of scope — do NOT touch" section listing every file deliberately excluded with its reasoning.
7. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `epic-10` and `10-1-...` entries updated `backlog` → `in-progress`/`ready-for-dev`.

**Output File:** `_bmad-output/implementation-artifacts/10-1-persona-rename-and-id-only-identity-references.md`
**Sprint Status:** `epic-10`: `backlog` → `in-progress`; `10-1-...`: `backlog` → `ready-for-dev`

---

### 3. `bmad-dev-story` (implementation, Amelia persona)

**Purpose:** Execute the story's 9 tasks in sequence: seed rename, 15 backend test files, 2 frontend files + their tests, full regression.

**When Invoked:** Immediately after the story file was created and marked `ready-for-dev`.

**Workflow Steps Executed:**
1. **Task 1 — `core/seeds.py`:** `RITA_ID` Employee's `name`/`email` changed to `"Sails Admin"`/`"admin@sails.example.com"`; `create_default_accounts()`'s `RITA_ID` Account email changed the same way.
2. **Tasks 2–6 — 15 backend test files:** 10 files needed only their `_login()` helper's default email parameter changed; `test_assignments_router.py` and `test_admin_api_keys_router.py` needed the default plus additional literal-string assertions (email-in-response-body checks, search-by-email params, `configured_by` display-name assertions); `test_assignments_service.py` needed one direct `get_account_by_email_ci(...)` call literal changed; `test_login.py` and `test_seed_employee_identity_alignment.py` needed full fixture rewrites (parametrized credential tables, case-insensitive-email regression tests).
3. **Task 7 — `AssignmentCard.tsx`:** the `mailto:rita@sails.example.com` link and "Contact Rita" text changed to `mailto:admin@sails.example.com`/"Contact Sails Admin"; matching update to `ContentDiscovery.test.tsx`'s accessible-name assertion and test title.
4. **Task 8 — `HrAppShell.tsx`:** avatar-initial text "R"→"S" and button text "Rita"→"Sails Admin" (minimal literal rename, per the `AskUserQuestion` resolution described in Overview); matching update to `HrAppShell.test.tsx`'s `getByRole` assertion.
5. **Task 9 — Full regression, in three passes:**
   - First full backend run: **294 failed / 100 errors** — root cause was the `create_default_accounts()` email-keyed idempotency bug (see Overview) crashing on `accounts_pkey`. Fixed by keying the check on `Account.id`.
   - Second full backend run: **4 failed** — traced to unrelated pre-existing password-hash drift on the shared local dev DB for morgan/jordan/sam (hashes no longer matched `demo123`, unrelated to this story, likely leftover state from an earlier password-regeneration story's test run). Reset via a one-off local DB data fix, explicitly noted as not part of this story's diff.
   - Third full backend run: **719 passed, 2 skipped, 0 failed.**
   - Full frontend suite (`npm run test -- --run`): **424 passed, 0 failed**, 41 files.
   - `npx tsc --noEmit`: 31 errors, identical count/location to the documented pre-existing baseline.
   - A final grep sweep for `rita@sails.example.com` across `backend/`/`frontend/src/` confirmed only the explicitly-documented out-of-scope files still carried the literal (later found during code review to have missed two more mocked-API test files — see Acceptance Auditor findings above).
6. Story's Dev Agent Record, Completion Notes, Change Log, and File List filled in; Status → `review`.

**Output Files:**
- `backend/app/core/seeds.py` (modified)
- 15 backend test files (modified — see full list in Files Created/Updated below)
- `frontend/src/components/AssignmentCard.tsx`, `frontend/src/components/layout/HrAppShell.tsx` (modified)
- `frontend/src/tests/ContentDiscovery.test.tsx`, `frontend/src/tests/HrAppShell.test.tsx` (modified)
- `_bmad-output/implementation-artifacts/10-1-persona-rename-and-id-only-identity-references.md`

**Sprint Status:** `10-1-...`: `ready-for-dev` → `in-progress` → `review`

---

### 4. `bmad-code-review` (3-layer adversarial review + decision resolution + patch application)

**Purpose:** Independent adversarial verification of the finished implementation, followed by resolving every finding.

**When Invoked:** User explicitly said "continue" immediately after the checkpoint following context-gathering, confirming the review target (recent conversation — Story 10.1's uncommitted implementation).

**Workflow Steps Executed:**
- Constructed the diff against uncommitted working-tree changes (`git diff HEAD`, 21 files changed, 51 insertions / 47 deletions), confirmed scope via checkpoint (`review_mode = "full"`, spec file = the story file itself, `baseline_commit: a8e21cd5` matching current `HEAD`).
- Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor in parallel as background subagents, the Acceptance Auditor given the story file's full path and told to read it directly rather than being handed its content inline.
- Normalized and deduplicated 15 raw findings across the three layers down to 5 unique findings, merging the 3-way-corroborated seed-rename-propagation finding into one (using the Edge Case Hunter's precise `location`/`guard_snippet` as the base, per the workflow's own dedup rule).
- Triaged into: **1 decision-needed, 4 patch, 0 defer, 8 dismiss.**
- **Decision-needed item resolved by the user:** the already-seeded-database backfill strategy. Presented three options (Alembic data migration / self-correcting seed functions / documented limitation); **user chose the Alembic data migration.** Implemented as `backend/alembic/versions/014_backfill_seeded_hr_admin_identity_rename.py` — a narrowly-scoped, symmetric (`upgrade`/`downgrade`) one-time `UPDATE` for both `employees` and `accounts`, gated on the *old* values matching exactly (mirroring migration 011's own scoped `password_hash` backfill precedent, so a manually-customized identity on any other environment is never silently overwritten). **Verified live, not just written:** reverted the seeded row to old values → `alembic upgrade head` corrected it to the new identity → `alembic downgrade -1` correctly restored the old values → `alembic upgrade head` reapplied, leaving the DB at `014 (head)` with the correct final identity.
- **All 4 patches applied** (unambiguous, low-risk, no per-finding confirmation needed since the user chose "apply every patch"):
  1. `seed_ids.py`'s module docstring updated to name "Sails Admin" and cross-reference the Story 10.1 rename, without touching the `RITA_ID` symbol itself (still explicitly out of scope per AC3).
  2. Misleading "Rita" comments/variable names renamed in `test_dashboard.py` (`rita_id`→`hr_admin_id`) and `test_employees_router.py` (`rita_token`/`rita_id`→`hr_admin_token`/`hr_admin_id`, plus the adjacent code-review comment) — pure renames, no behavior change.
  3. **A new regression test added** — `test_create_default_accounts_is_idempotent_when_row_predates_an_email_rename` in `test_seed_employee_identity_alignment.py`, which mutates the seeded account's email to an arbitrary stale value mid-transaction, re-runs `create_default_accounts()`, and asserts it neither raises nor commits the mutation. **Verified the test actually catches the bug it claims to**, not just trusting its shape: temporarily reverted `seeds.py`'s fix back to the email-keyed check, confirmed the new test failed and reproduced the exact original `accounts_pkey` `UniqueViolationError`, then restored the fix and confirmed green again.
  4. The story file's own Task 9 completion note and Dev Notes "Out of scope" list corrected to actually name `Login.test.tsx`/`authApi.test.ts` instead of falsely claiming zero remaining matches.
- **Dismissed 8 findings after verification**, each checked rather than waved off: unverifiable self-reported regression numbers (a process complaint about the workflow's own inherent lack of external CI, not an actionable code issue — the same numbers were independently re-verified after every patch in this same review pass); the manual DB password-hash fix being "undocumented" (it was documented, in the Debug Log, and is subsumed by the now-fixed idempotency bug); the PRD/product-persona split "having no cross-reference" (already documented in AC1 and the Dev Notes — false positive); AC4's "live resolution" claim being unproven (disproven — a pre-existing, unrelated test already proves it by logging in as two distinct real admins and observing `configured_by` differ); the new `AssignmentCard.tsx` contact link reproducing a hardcoded-identity pattern (a valid future-story architecture observation, already effectively resolved for the more consequential `HrAppShell.tsx` case via the same-session `AskUserQuestion`, not a defect in this diff); the `HrAppShell.tsx` literal misrepresenting a future second HR_ADMIN (the exact tradeoff already confirmed by the user this session); the story's status transition having "no separate reviewer step" (this code-review pass *is* that step); reworded (not 1:1) comment edits (verified meaning-preserving).
- Re-ran the full backend suite after all patches — **720 passed** (719 baseline + 1 net new), 2 skipped, 0 failed. Confirmed `alembic current` at `014 (head)`.
- Story Status → `done`; `sprint-status.yaml` synced (`10-1-...`: `done`).

**Output:** Story file's "### Review Findings" subsection (1 checked-off decision with resolution note, 4 checked-off patches with inline "Fixed:" notes); Change Log entry; corrected Dev Notes/Task 9 text; a new Alembic migration file.

**Documentation Generated:**
- The story file's Review Findings section, Change Log, Status field, and self-corrected Dev Notes/Completion Notes
- Sprint status synced (`10-1-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`; `epic-10`: `backlog` → `in-progress`)
- This implementation-steps document (`documentation/ImplementationStepsForStory10-1.md`)

---

## Files Created/Updated

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/core/seeds.py` | `RITA_ID` Employee/Account `name`/`email` renamed to "Sails Admin"/`admin@sails.example.com`; `create_default_accounts()`'s idempotency check re-keyed from `Account.email` to `Account.id` (code-review-caught bug fix) |
| `backend/app/core/seed_ids.py` | Code-review patch only: module docstring updated to name "Sails Admin" and cross-reference the Story 10.1 rename |
| `backend/tests/test_admin_content_router.py` | `_login()` default email changed |
| `backend/tests/test_assignments_create_route.py` | `_login()` default email changed |
| `backend/tests/test_assignment_cancel_no_orphan.py` | `_login()` default email changed |
| `backend/tests/test_assignment_delete.py` | `_login()` default email changed |
| `backend/tests/test_content_router.py` | `_login()` default email changed |
| `backend/tests/test_dashboard_router.py` | `_login()` default email changed |
| `backend/tests/test_drill_down_endpoint.py` | `_login()` default email changed |
| `backend/tests/test_override_endpoint.py` | `_login()` default email changed |
| `backend/tests/test_skills_router.py` | `_login()` default email changed |
| `backend/tests/test_employees_router.py` | `_login()` default email changed; code-review patch renamed `rita_token`/`rita_id`→`hr_admin_token`/`hr_admin_id` and their comment |
| `backend/tests/test_assignments_router.py` | `_login()` default plus `emails` set / search-by-email param literals changed |
| `backend/tests/test_admin_api_keys_router.py` | `_login()` default plus two `configured_by == "Rita the Recommender"` assertions changed to "Sails Admin"; adjacent comments reworded |
| `backend/tests/test_assignments_service.py` | One direct `get_account_by_email_ci(...)` call literal changed |
| `backend/tests/test_login.py` | Parametrized credential table + 4 other literal email occurrences + case-insensitive-email regression test, all changed |
| `backend/tests/test_seed_employee_identity_alignment.py` | `_DEMO_ACCOUNTS` tuple + case-insensitive test literals changed; code-review patch added a new regression test for the idempotency-key bug |
| `backend/tests/test_dashboard.py` | Code-review patch only: renamed `rita_id`→`hr_admin_id` and its comment |

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/014_backfill_seeded_hr_admin_identity_rename.py` | Code-review patch (resolving the decision-needed finding): one-time, scoped, symmetric data migration backfilling the identity rename onto any database seeded before this change |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/components/AssignmentCard.tsx` | "No recommended content" empty-state `mailto:` link and text changed from `rita@sails.example.com`/"Contact Rita" to `admin@sails.example.com`/"Contact Sails Admin"; adjacent comment updated |
| `frontend/src/components/layout/HrAppShell.tsx` | Top-right user-menu literal changed from "R"/"Rita" to "S"/"Sails Admin" (minimal literal rename, user-confirmed scope) |
| `frontend/src/tests/ContentDiscovery.test.tsx` | Updated the "Contact Rita" link test title and accessible-name assertion to match |
| `frontend/src/tests/HrAppShell.test.tsx` | Updated the `getByRole('button', { name: /rita/i })` assertion to `/sails admin/i` |

### Planning/Tracking — Modified Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `epic-10`: `backlog` → `in-progress`; `10-1-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |

### Documentation Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/10-1-persona-rename-and-id-only-identity-references.md` | Story file — 6 ACs, 9 Tasks, Dev Notes with an exhaustive "Out of scope" list, Dev Agent Record, Review Findings section |
| `documentation/ImplementationStepsForStory10-1.md` | This file |

### Not Changed (by design)

- `backend/app/core/seed_ids.py`'s `RITA_ID` symbol name and UUID value — only the docstring's human-readable name reference changed (AC3)
- The PRD's own narrative persona "Rita" (§2.1, UJ-1, UJ-3) — AC1 explicitly excludes it
- Any `Role.HR_ADMIN`/`Role.EMPLOYEE` authorization check anywhere in the codebase — AC3
- `content/admin_api_keys_router.py` — already resolves `configured_by_name` live from `employee.id`, needed zero code change (AC4)
- Fabricated JWT `user_id="rita"` test payloads in `test_current_user.py`, `test_require_hr_admin.py`, `test_security.py` — synthetic, unrelated to the real seeded identity
- `test_provenance_detail.py`'s inline synthetic `Employee(name="Rita Martinez", ...)` — a throwaway object for generic override-attribution rendering tests, not the real seed
- Unused mock `name`/`configured_by`/`override_set_by_name` fixture fields in `EmployeesPage.test.tsx`, `SkillAssignmentDashboard.test.tsx`, `SkillsPage.test.tsx`, `ApiKeysModal.test.tsx`, `ContentLookupPanel.test.tsx`, `DashboardPage.test.tsx`, `ProvenanceDrillDownModal.test.tsx`, `HrAppShell.test.tsx`'s own mock, `Login.test.tsx`, `authApi.test.ts` — all mock arbitrary display names/emails never read from the real backend seed

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `bmad-create-story`
- Read `epics.md`'s already-authored Story 10.1 AC text and the 2026-09-15 Sprint Change Proposal for background
- Ran an exhaustive case-insensitive grep for "rita" across the entire backend and frontend trees, classifying every hit in/out of scope before writing a line of Dev Notes
- Found two real live-UI surfaces (a contact link, a nav literal) not mentioned anywhere in the epics.md AC text
- Status → `ready-for-dev`; `epic-10` → `in-progress`

### Phase 2: Implementation
**Execution:** Amelia persona
- 9 tasks executed in sequence: seed rename → 15 backend test files (in 4 groupings by shape of change) → 2 frontend files + their tests → full regression
- One judgment call surfaced to the user via `AskUserQuestion` before proceeding (`HrAppShell.tsx`'s nav literal: minimal rename vs. wiring to real auth identity) — user chose minimal rename
- Found and fixed a real idempotency bug (`create_default_accounts()`'s email-keyed existence check) only by actually running the full suite, not from static analysis
- Also found and fixed unrelated pre-existing local-DB password-hash drift (data-only, not part of this story's diff)
- Full regression: 719/719 backend, 424/424 frontend, tsc unchanged at 31 pre-existing errors
- Story marked `review`

### Phase 3: Code Review + Decision + Patches
**Skill:** `bmad-code-review`
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor — the auditor given the story file directly as spec) against the uncommitted diff
- 15 raw findings deduplicated to 5 unique findings: 1 decision-needed (all 3 layers independently converged on the same root cause), 4 patched, 0 deferred, 8 dismissed after direct verification
- The decision-needed finding was a genuine gap the implementation phase's own regression testing had already brushed up against (the manual DB fix) without turning into a lasting code fix — resolved by the user choosing an Alembic migration, then verified live via a full upgrade/downgrade/upgrade cycle
- The most surgically useful single finding came from the narrowest reviewer (Edge Case Hunter's one precise JSON finding with a concrete guard-snippet), while the Acceptance Auditor caught a self-inflicted documentation-accuracy defect (Task 9's false "zero remaining matches" claim) neither of the other two layers found
- Full regression re-verified after patches: 720/720 backend (0 masked failures), tsc unchanged
- Story marked `done`

---

## Test Coverage

### New/Extended Test Files

- `test_seed_employee_identity_alignment.py` — 14 total tests (13 pre-existing/updated + 1 net new): `_DEMO_ACCOUNTS` tuple and the case-insensitive-email test updated to the new identity; new `test_create_default_accounts_is_idempotent_when_row_predates_an_email_rename` added during code review, verified RED against the pre-fix code and GREEN with the fix restored.
- `test_login.py` — 9 total tests, all pre-existing, 6 with literal-value updates (parametrized credential table, session-cookie test, 2 wrong-password tests, case-insensitive regression test, missing-password-field test).
- `test_assignments_router.py`, `test_admin_api_keys_router.py` — pre-existing tests with both their shared `_login()` default and additional literal assertions updated.
- `ContentDiscovery.test.tsx` — 1 pre-existing test's title and accessible-name assertion updated to match the renamed contact link.
- `HrAppShell.test.tsx` — 1 pre-existing test's `getByRole` assertion updated to match the renamed nav literal.

### Regression Verification

- Backend: 294 failed/100 errors (first run, real bug found) → 4 failed (second run, unrelated pre-existing data drift found) → 719 passed (third run, clean baseline) → 720 passed (after code-review patches, 1 net new test), 2 skipped throughout, 0 failed at the final two checkpoints
- Frontend: 424 passed, 0 failed, 41 files (unchanged across the review — no frontend files were touched during code review)
- `tsc --noEmit`: 31 pre-existing errors at every checkpoint, none in this story's files
- Alembic: new migration `014` verified via a live `upgrade → downgrade → upgrade` cycle against the real local dev DB, confirming both directions correctly transition the seeded identity

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AC1: seeded identity rename** | `Employee.name`/`email` and `Account.email` literal values changed for `RITA_ID`; `RITA_ID`'s UUID/symbol and the PRD narrative persona left untouched | `backend/app/core/seeds.py` |
| **AC2/AC3: exhaustive, ID-only-checks-preserved test fixture updates** | 15 backend test files updated to the new literal, zero role-based authorization checks touched | 15 files under `backend/tests/` |
| **AC4: live display-name resolution needs no code change** | Verified `content/admin_api_keys_router.py`'s `configured_by_name` already resolves live from `employee.id` — confirmed by an existing, unrelated test that logs in as two distinct real admins and observes the value differ | (verification only, no file changed) |
| **AC5: live contact-link rename** | `AssignmentCard.tsx`'s `mailto:`/text literal changed | `frontend/src/components/AssignmentCard.tsx`, `frontend/src/tests/ContentDiscovery.test.tsx` |
| **AC6: nav-shell literal rename, scope confirmed via `AskUserQuestion`** | `HrAppShell.tsx`'s avatar/button literal changed; explicitly not wired to real auth identity | `frontend/src/components/layout/HrAppShell.tsx`, `frontend/src/tests/HrAppShell.test.tsx` |
| **Idempotency-check bug fix (found during implementation)** | `create_default_accounts()`'s existence check re-keyed from `Account.email` to `Account.id` | `backend/app/core/seeds.py` |
| **Already-seeded-database backfill (found during code review, decision-needed, user-resolved)** | New Alembic migration, scoped `UPDATE ... WHERE id = RITA_ID AND email/name = <old values>`, symmetric `downgrade()` | `backend/alembic/versions/014_backfill_seeded_hr_admin_identity_rename.py` |

---

## Key Technical Achievements

✅ **Ran the full create → implement → review → decide → patch pipeline in one continuous session**, correctly discovering the missing story file/status before any implementation work began
✅ **Enumerated the exact, exhaustive scope before implementation started** — a full-codebase grep classified every one of 32+ backend and 15+ frontend "rita" hits as in/out of scope, per the AC's own explicit demand, rather than discovering scope mid-story
✅ **Found and fixed a real production-code bug via actually running the test suite, not static analysis alone** — `create_default_accounts()`'s email-keyed idempotency check, caught by a 294-failure regression run
✅ **A genuine scope-boundary question was surfaced to the user rather than silently resolved either way** — `HrAppShell.tsx`'s nav literal: minimal rename vs. wiring to real auth identity, resolved explicitly via `AskUserQuestion`
✅ **Code review's 3 independent layers converged on the same root-cause finding from three different methods** (adversarial prose, edge-case JSON with a guard-snippet, AC-text cross-reference) — the single strongest signal in the whole review
✅ **The decision-needed fix was verified live, not just written** — a full Alembic `upgrade → downgrade → upgrade` cycle run against the real local dev DB, confirming both directions actually transition the data correctly
✅ **A new regression test was verified to actually catch the bug it claims to**, not just trusting its shape — the fix was temporarily reverted, the test confirmed RED reproducing the exact original crash, then the fix restored and the test confirmed GREEN
✅ **A self-inflicted documentation-accuracy defect was caught and corrected** — the story's own Task 9 completion note had falsely claimed zero remaining matches, found by the Acceptance Auditor's direct spec-vs-diff cross-check
✅ **Zero regressions across every regression run in the session's final two checkpoints** — 719 → 720 passed, with the same 31 pre-existing `tsc` errors throughout

---

## Deferred Items (Not Story 10-1 Scope)

None formally deferred to `deferred-work.md` — all findings this session were either resolved (the decision-needed item, all 4 patches) or dismissed as non-issues after verification. Two dismissed findings are recorded here as legitimate future-story considerations rather than defects in this diff:

- **`AssignmentCard.tsx`'s new contact link still hardcodes an identity** (`mailto:admin@sails.example.com`, "Contact Sails Admin") rather than deriving it dynamically from whichever HR Admin is actually configured. Explicitly in scope for *this* story (AC5) and consistent with the same-session `HrAppShell.tsx` precedent, but a future story introducing a real "contact support" flow or a second HR_ADMIN identity should revisit both hardcoded surfaces together.
- **`HrAppShell.tsx`'s nav-shell identity display will misrepresent any second real HR_ADMIN** introduced by a later Epic 10 story — an explicit, user-confirmed tradeoff for this story's narrow scope, not a defect, but worth remembering once Epic 10's roster-management stories land.

---

## Conclusion

Story 10-1 is **✅ DONE** after a full create-then-implement-then-review-decide-and-patch cycle, run start to finish in one session:

- All 6 acceptance criteria satisfied — the seeded HR Admin's real login email/display name is `admin@sails.example.com`/"Sails Admin" everywhere it's checked (backend seed, 15 test files, a live contact link, and the nav shell), with zero change to any role-based authorization check, the `RITA_ID` UUID/symbol, or the PRD's narrative persona — verified by a 720-test backend regression pass (0 masked failures) and a 424-test frontend regression pass, both before and after the code-review patches
- Code review surfaced 5 unique findings after deduplicating 15 raw ones: 1 requiring a human decision (resolved — an Alembic data migration, verified live via a full upgrade/downgrade cycle), 4 patched (a stale docstring, two misleading test variable names, a new verified-effective regression test, and a self-corrected documentation claim), 0 deferred, 8 dismissed after direct verification
- Zero regressions across every regression run in the session's final checkpoints (719 → 720 passed)
- **Not yet committed to git** — working tree still uncommitted as of this document, on top of `HEAD` at `a8e21cd5` ("docs: Epic 9 retrospective (bmad-retrospective)")

**Epic 10 status:** `in-progress` — 1 of 16 stories (10.1) done; next in the documented build order is Story 10.2 (Employee Grid Columns), sequenced together with 10.10 as the identity/seed-data foundation this story completes.
