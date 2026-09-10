# Implementation Steps for Story 6-4: Wire `ever_assigned` Into Assignment Creation (AD-11 point 3)

**Story Key:** 6-4-wire-ever-assigned-into-assignment-creation
**Epic:** 6 (Admin-Assisted Content Sourcing)
**Status:** ✅ DONE
**Completed Date:** 2026-09-10

---

## Overview

Story 6-4 closes a gap Story 6.3's own code review found: `assignments/`'s `create_assignment_service` (live at `POST /api/assignments`) never called a flag-setter, so Story 6.3's permanent Skill lock (`ever_assigned`, AD-11) was a no-op in practice — an HR Admin could assign a Skill and then still rename/hard-delete it via Story 6.3's own endpoints. This story wires `skills.service.mark_ever_assigned(skill_id)` into `create_assignment_service`, called after every successful Assignment creation, so the lock genuinely engages the first time a Skill is assigned.

The work happened in three passes in the same overall session: (1) story creation + full TDD implementation, invoked via `/bmad-agent-dev`, with the user explicitly confirming via `AskUserQuestion` that "create then implement together" was the intent, matching the precedent already set for Story 6.3; (2) an adversarial code review pass (`/bmad-code-review`) that found and fixed a real gap in the failure-isolation design; (3) commit and push to `origin/POC_Hackathon`.

---

## Agents Invoked

### 1. **Blind Hunter (Code Review Agent)**

**Purpose:** Adversarial general review — bugs, logic errors, contradictions with the code's own claims, architectural violations.

**When Invoked:** Step 02 of `/bmad-code-review`
**Model Capability:** Sonnet 5 (session model)
**Input:** Full diff (`git diff HEAD` against baseline `de827222`, ~210 insertions across 9 files), instructed to invoke the `bmad-review-adversarial-general` skill against it

**Key Findings Identified (11 items):**
- No auth check inside `skills.service.mark_ever_assigned` — enforced only by a docstring comment, not by code
- The code comment's "a missed flag-set is a data-quality issue to reconcile" claim has no actual reconciliation job/endpoint/metric/alert backing it
- The conditional `UPDATE`'s rowcount is never inspected — "already `True`" and "doesn't exist" are indistinguishable
- A race window exists where a concurrent transaction can still read `ever_assigned = False` before this request's own commit
- Import style (`from app.skills.service import mark_ever_assigned`) called inconsistent with `content/service.py`'s module-import pattern, and the resulting `monkeypatch.setattr(assignments_service, "mark_ever_assigned", ...)` called a "fragile test seam"
- The failure-path test only monkeypatches a synthetic `RuntimeError`, never a real DB-level error inside the SAVEPOINT
- No cleanup of test-created Skill rows in the shared dev DB (claimed to accumulate junk data)
- A trailing `await db.flush()` in `skills/repository.py::mark_ever_assigned` called out as dead/no-op code
- The blanket `except Exception` doesn't distinguish real bugs from expected transient failures
- A referential-integrity gap: a Skill hard-deleted concurrently with an in-flight `create_assignment_service` call for it
- No test asserts on the actual `logger.exception` call arguments

**Output:** 11 findings; after triage and direct verification against the real code, 1 became a genuine patch (merged with an Edge Case Hunter finding), 1 became a second patch (the no-op `flush()`), 3 routed to defer, 6 dismissed as false positives or matching established precedent (verified empirically, not just argued)

---

### 2. **Edge Case Hunter (Code Review Agent)**

**Purpose:** Boundary conditions, unhandled branches, race windows.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with Blind Hunter)
**Model Capability:** Sonnet 5 (session model)
**Input:** Same full diff, targeting the `bmad-review-edge-case-hunter` skill

**Key Findings Identified (structured JSON, location/trigger/guard/consequence per item):**
- `assignments/service.py:107-114`: the `except Exception` around `session.begin_nested()` assumes the session stays healthy after any failure — a connection-invalidating DB error there could break the session such that the later outer `session.commit()` in `get_db` also fails, losing the Assignment despite the code comment's explicit claim that this can't happen
- `skills/repository.py:112-114`: two concurrent `create_assignment_service` calls against the same never-before-assigned `skill_id` could have the second request's `UPDATE` block on a row lock with no timeout, until the first request's transaction commits
- `tests/test_assignments_service.py:142-145`: the failure test's `_boom` raises before any DB statement executes, so the actual SAVEPOINT-rollback-on-real-DB-error path is never exercised

**Output:** 3 structured findings; the first merged with a Blind Hunter finding into the SAVEPOINT session-health patch, the second routed to defer (matches Story 6.3's already-accepted row-locking precedent), the third merged with a Blind Hunter finding into the real-DB-error test patch

---

### 3. **Acceptance Auditor (Code Review Agent)**

**Purpose:** Verify the diff against Story 6-4's literal Given/When/Then acceptance criteria and its own Scope Notes.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with the other two layers)
**Model Capability:** Sonnet 5 (session model)
**Input:** Story spec file (full, read directly) + the same diff

**Key Findings Identified:**
- **None requiring remediation.** Explicitly confirmed every AC clause and every numbered Scope Note as correctly implemented: the SAVEPOINT-isolated call site and ordering (AC1, Scope Note 5/6), the idempotent conditional `UPDATE` (AC2, Scope Note 4), the no-auth-check pass-through shape mirroring `content.service.match_content_for_skill` (AC3, Scope Note 3), the one-way import direction (AD-1/AD-8), and the untouched router/schemas (Scope Note 8)
- Verified the `deferred-work.md` entry was marked resolved-with-strikethrough rather than deleted outright, and judged this a reasonable interpretation of "resolve the ledger entry," not a violation

**Output:** A fully clean pass — zero findings

---

## Skills Invoked

### 1. **`/bmad-agent-dev` (Amelia persona)**

**Purpose:** The user's entry point — "start development for the story 6-4-wire-ever-assigned-into-assignment-creation, refer the ux design if required."

**When Invoked:** Session start
**Outcome:** Loaded the `agent` block, greeted as Amelia, and dispatched directly to `bmad-dev-story` since the user's message already named a clear intent.

---

### 2. **`/bmad-dev-story` → Redirected to `/bmad-create-story`**

**Purpose:** Discover the target story and load its context.

**When Invoked:** Immediately after activation
**Outcome:** No story file existed for `6-4-wire-ever-assigned-into-assignment-creation` (still `backlog` in `sprint-status.yaml`). Rather than guessing, asked the user via `AskUserQuestion` whether to create-then-implement in one session (matching the exact precedent already set for Story 6.3) — **user chose "Create then implement."**

---

### 3. **`/bmad-create-story` Skill**

**Purpose:** Generate a comprehensive story file with full context before implementation.

**When Invoked:** Immediately after the confirmation above, args `6-4-wire-ever-assigned-into-assignment-creation`
**Workflow Steps Executed:**
1. Pulled Story 6.4's full literal AC text from `epics.md` (Epic 6, lines 2205-2223)
2. Read the architecture spine's AD-11 point 3 in full (`assignments/` sets the flag, same shape as its existing `content/` dependency)
3. Read the actual current code directly: `assignments/service.py::create_assignment_service` and `assignments/repository.py::create_assignment` (confirmed the flush-not-commit convention), `skills/service.py`/`skills/repository.py` (Story 6.1-6.3's existing state), `content/service.py::match_content_for_skill` (the precedent this story's `mark_ever_assigned` shape mirrors), `core/db.py::get_db` (the single-commit-per-request convention — the reason the SAVEPOINT isolation pattern was required), and `core/seeds.py` (seeded Skill IDs)
4. Cross-checked the Skills tab UX spec (`04.1-skills-content-sourcing.md`) and confirmed the 🔒 lock indicator already renders off `SkillResponse.ever_assigned` — no frontend work needed for this story
5. Identified and resolved the story's one real design decision during story-writing itself: how to satisfy AC1's "same request but not the same DB transaction as a hard dependency" clause given this codebase's one-commit-per-request architecture — resolved as a `session.begin_nested()` SAVEPOINT, written directly into Scope Note 5
6. Generated the story file with 10 Scope Notes, then implemented it directly in the same session rather than stopping at `ready-for-dev`

**Output File:** `_bmad-output/implementation-artifacts/6-4-wire-ever-assigned-into-assignment-creation.md`
**Sprint Status:** `6-4-...`: `backlog` → `ready-for-dev` (implemented in the same pass, not stopped there)

---

### 4. **Direct Implementation (`/bmad-dev-story`, same session)**

**Purpose:** Implement the story per its own Tasks, red-green-refactor.

**When Invoked:** Immediately after story creation
**Steps Executed:**
1. **Task 1 (RED → GREEN):** Wrote 3 failing tests for `skills/repository.py::mark_ever_assigned`, confirmed the `ImportError`, then implemented it as a single conditional Core-level `UPDATE ... WHERE ever_assigned = false` — idempotent by construction, never a SELECT-then-UPDATE
2. **Task 2 (RED → GREEN):** Wrote 2 failing tests for `skills/service.py::mark_ever_assigned`, then implemented it as a thin pass-through, same no-auth-check shape as `content.service.match_content_for_skill`
3. **Task 3 (RED → GREEN):** Wrote 3 failing tests for `assignments/service.py::create_assignment_service`'s new behavior (flag set on creation, idempotent on re-assignment, failure isolation via a monkeypatched exception), then wired the call in — isolated inside `async with session.begin_nested(): ... except Exception: logger.exception(...)`, never re-raising
4. Ran the full targeted test suite (8 new tests, all passing) and the full regression suite: `3 failed, 431 passed, 2 skipped, 10 deselected` — same 3 pre-existing, unrelated failures
5. **Live end-to-end verification, not just tests:** rebuilt the `talentpilot-ai-backend` Docker image, `docker compose up -d backend`, confirmed healthy. Logged in as Rita (HR_ADMIN) via `curl`, created a fresh Skill, assigned it to Casey via `POST /api/assignments`, then confirmed `PATCH /api/admin/skills/{id}` now genuinely returns `403 SKILL_LOCKED` — proving Story 6.3's lock, dormant since it shipped, now actually engages. Also confirmed AC2 live: a second `POST /api/assignments` against the now-locked Skill still returned `201`.
6. Resolved and struck through the corresponding `deferred-work.md` entry from Story 6.3's review

**Output:** Story file updated with completed Tasks, Dev Agent Record, File List, Change Log; status set to `review`
**Sprint Status:** `6-4-...`: `in-progress` → `review`

---

### 5. **`/bmad-code-review` Skill**

**Purpose:** Adversarial review of the finished implementation against the story's own spec, structured triage, and patch application.

**When Invoked:** User request: "do the code review for story 6-4-wire-ever-assigned-into-assignment-creation"
**Workflow Steps Executed:**

- **Step 01 (Gather Context):** Spec file resolved via Tier 1 (explicit story-key argument), `baseline_commit` (`de827222`) confirmed to match current `HEAD` exactly (nothing committed yet), so diff source = uncommitted changes (`git diff HEAD`, 210 insertions/6 deletions across 9 files). Checkpoint presented and confirmed by the user before launching review agents.
- **Step 02 (Review):** Launched Blind Hunter, Edge Case Hunter, and Acceptance Auditor in parallel background subagents (`review_mode = "full"`, story file as spec), each given the full diff inline. Both Blind Hunter and Edge Case Hunter stalled on their first attempt (no progress for 600s) and were automatically retried successfully; the Acceptance Auditor succeeded on the first attempt.
- **Step 03 (Triage):** Normalized 14 raw findings (11 Blind Hunter + 3 Edge Case Hunter; Acceptance Auditor returned zero). Verified every finding against the real, current source before rating, including writing and running a standalone throwaway script (not committed) to empirically confirm that a real `IntegrityError` inside `session.begin_nested()` leaves `session.is_active == True` and the outer transaction still commits cleanly — this directly validated (and refined) the SAVEPOINT design rather than accepting or dismissing the finding on reasoning alone. Also reasoned through Postgres's actual FK `RESTRICT` + `FOR KEY SHARE` row-locking semantics to evaluate the concurrent-delete finding, and confirmed via `grep` that `assignments/service.py` already uses the same direct-name-import style elsewhere (settling the "inconsistent import" finding as matching existing local precedent). Routed the result into 0 decision-needed, 3 patch, 3 defer, 6 dismiss.
- **Step 04 (Present and Act):** Findings written to the story file's new "Review Findings" subsection and the 3 deferred items appended to `deferred-work.md` under a new dated heading. User chose "fix all of them now" for the 3 patch findings.

**Patches Applied:**
1. The SAVEPOINT's `except Exception` now re-raises when `session.is_active` is `False` afterward — converts a genuinely broken session/connection into a clean request failure instead of silently proceeding on one that would likely fail `get_db`'s own final commit anyway; the realistic/recoverable failure class (a clean constraint violation) is still swallowed, per the empirical verification above
2. Added `test_real_db_error_inside_savepoint_does_not_lose_the_assignment` — patches `mark_ever_assigned` to attempt a genuine constraint-violating `UPDATE` (`skills.name = NULL`) rather than a synthetic Python exception, and confirms the Assignment still commits and `session.is_active` stays `True`
3. Removed the no-op trailing `await db.flush()` in `skills/repository.py::mark_ever_assigned` — a Core-level `UPDATE` is already sent synchronously, with no pending ORM-tracked object for `flush()` to synchronize; copied from `update_skill`'s pattern without checking it actually did anything here

**Environment interruption handled mid-review:** the first post-patch full test run produced 39 spurious failures across all three touched test files, including tests untouched by this story. Diagnosed by checking `docker ps` directly — Docker Desktop itself was not running (the daemon was unreachable), unrelated to the code changes. Restarted Docker Desktop, waited for the daemon and containers to come back healthy, re-ran clean.

**Output:** Story status → `done`; full suite re-verified at 432 passed (up from 431 pre-review) / 2 skipped / same 3 pre-existing failures. Backend Docker image rebuilt and redeployed a second time with the patches applied.

**Documentation Generated:**
- Code review findings + resolutions written directly into the story file's Review Findings subsection
- 3 deferred items logged to `deferred-work.md` under a new dated heading
- `project-context.md` updated with both the implementation and the review outcome, per this project's own mandatory-update convention
- Sprint status synced (`6-4-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`)

---

### 6. **Commit and Push**

**Purpose:** Land the finished, reviewed story on the shared branch.

**When Invoked:** User request: "commit and push the code with proper comments"
**Outcome:** Staged the 10 files belonging to this story explicitly (not a blanket `git add -A`), committed with a detailed message summarizing the design, the SAVEPOINT rationale, the review outcome, and test counts, then pushed to `origin/POC_Hackathon`.

**Commit:** `f065a93a` (`de827222..f065a93a`)

---

## Files Created/Updated

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/skills/repository.py` | `mark_ever_assigned` — single idempotent conditional `UPDATE`; code-review patch: removed a no-op trailing `flush()` |
| `backend/app/skills/service.py` | `mark_ever_assigned` — thin pass-through, no-auth-check shape mirroring `content.service.match_content_for_skill` |
| `backend/app/assignments/service.py` | Imports `mark_ever_assigned`; `create_assignment_service` calls it (SAVEPOINT-isolated) after creating the Assignment; code-review patch: re-raises if `session.is_active` is `False` after a caught failure |
| `backend/tests/test_skills_repository.py` | 3 new tests: flips `False → True`, idempotent no-op, no-raise on nonexistent `skill_id` |
| `backend/tests/test_skills_service.py` | 2 new tests: same matrix at the service layer |
| `backend/tests/test_assignments_service.py` | 4 tests total: flag set on creation, idempotent on re-assignment, synthetic-failure isolation, plus the code-review patch's real-DB-error-inside-SAVEPOINT test |

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/6-4-wire-ever-assigned-into-assignment-creation.md` | Story file — ACs, Scope Notes, Dev Notes, Review Findings, Dev Agent Record |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `6-4-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | Story 6.3's "`ever_assigned` is never set" entry marked resolved-with-strikethrough; 3 new items added under a new "Deferred from: code review of 6-4-..." heading |
| `_bmad-output/project-context.md` | Implementation + review outcome appended, per this project's own mandatory-update rule |
| `documentation/ImplementationStepsForStory6-4.md` | This file |

### Not Changed (by design)

- `backend/app/skills/router.py`, `backend/app/skills/schemas.py` — `mark_ever_assigned` is a service-to-service call only, never exposed via any HTTP route
- No new Alembic migration — `ever_assigned`'s column and one-way semantics were already correct from Story 6.1 (migration 004); this story only adds the write path
- No frontend files — the Skills tab's 🔒 lock indicator already reads `SkillResponse.ever_assigned` (Story 6.1/6.2)

---

## Implementation Workflow Summary

### Phase 0: Discovery and Confirmation
**Skill:** `/bmad-agent-dev` → `/bmad-dev-story`
- No story file existed yet for 6-4 (`backlog` status, no file)
- Asked the user via `AskUserQuestion` whether to create-then-implement together (matching Story 6.3's precedent) — confirmed

### Phase 1: Story Creation
**Skill:** `/bmad-create-story`
- Read Story 6.4's AC from `epics.md`, AD-11 point 3 from the architecture spine, and the live `assignments/`/`skills/`/`content/` code directly
- Identified and resolved the one real design decision (the SAVEPOINT isolation pattern) during story-writing, not left for the dev pass
- Generated the story file with 10 Scope Notes

### Phase 2: Implementation
**(direct, same session, TDD red-green-refactor per task)**
- 8 new tests across repository/service/integration layers, all red-then-green
- Full regression pass — 431 passed, 2 skipped, same 3 pre-existing failures
- Live end-to-end verification via `curl` against a rebuilt/redeployed backend container
- Story marked `review`

### Phase 3: Code Review
**Skill:** `/bmad-code-review`
- 3 parallel adversarial layers, single pass (2 of 3 layers auto-retried after an initial stall)
- **Findings:** 14 raw → 8 after dedup → 0 decision-needed, 3 patch, 3 defer, 6 dismiss
- **Real gap found and fixed:** the SAVEPOINT's blanket `except Exception` didn't verify the session stayed usable afterward — empirically verified (via a throwaway script) that the realistic/recoverable failure class is genuinely protected, then closed the gap for the unrecoverable case with an `is_active` re-raise guard
- **Action:** all 3 patches applied; environment interruption (Docker Desktop down) diagnosed and resolved mid-review, distinct from the code itself
- Output: 432 passed (up from 431 before review), 2 skipped, same 3 pre-existing failures; story marked `done`

### Phase 4: Commit and Push
- Staged the 10 story-specific files explicitly, committed with a detailed message, pushed to `origin/POC_Hackathon` (`f065a93a`)

---

## Test Coverage

### New/Extended Test Files (9 tests total from this story)
- `test_skills_repository.py` — 3 new tests: `mark_ever_assigned` flips `False → True`; idempotent no-op on an already-`True` Skill; silent no-raise on a nonexistent `skill_id`
- `test_skills_service.py` — 2 new tests: same matrix at the service layer
- `test_assignments_service.py` — 4 tests: flag set on Assignment creation (verified via `skills.repository.get_skill_by_id`); idempotent on a second Assignment against an already-locked Skill; a monkeypatched-`RuntimeError` failure isolation test; the code-review-added test exercising a genuine DB constraint violation inside the SAVEPOINT

### Regression Verification
- Full suite run after implementation (431 passed) and again after the code review's patches (432 passed) — same 3 pre-existing, unrelated failures at every stage
- Every review finding verified against the real, current source before being accepted or dismissed — including an empirical throwaway-script verification of the SAVEPOINT's session-health behavior under a real DB error, not reasoned from memory alone
- Live-verified end-to-end via `curl` against a rebuilt/redeployed backend container, both before and after the review's patches

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AD-11 point 3: `assignments/` sets the flag, not `skills/`** | `create_assignment_service` calls `skills.service.mark_ever_assigned(skill_id)` after a successful Assignment insert — `assignments/` never writes the `skills` table directly | `assignments/service.py` |
| **AD-1/AD-8: cross-module access via Service API only, same shape as the existing `content/` dependency** | `skills.service.mark_ever_assigned` mirrors `content.service.match_content_for_skill`'s exact `(db, id)`, no-auth-check shape | `skills/service.py`, `assignments/service.py` |
| **Single-commit-per-request convention (`core/db.py::get_db`)** | The flag-set call is isolated inside a `session.begin_nested()` SAVEPOINT so a failure there can't take the already-flushed Assignment down with it — a new pattern for this codebase, introduced specifically for this requirement, then hardened with a `session.is_active` guard during code review | `assignments/service.py` |
| **Idempotency by construction, not by a Python-side check** | `mark_ever_assigned`'s repository implementation is a single conditional `UPDATE ... WHERE ever_assigned = false`, never a SELECT-then-UPDATE round trip | `skills/repository.py` |

---

## Key Technical Achievements

✅ **Closed a real, live gap all 3 of Story 6.3's review layers independently flagged** — verified fixed not just by tests but live via `curl`: `PATCH /api/admin/skills/{id}` now genuinely returns `403 SKILL_LOCKED` after an Assignment is created
✅ **Introduced a new transactional-isolation pattern (`session.begin_nested()`) deliberately, with the reasoning written into the story's Dev Notes** — not copied from elsewhere in this codebase, because nothing else in it had this exact "secondary write must not endanger a primary write, same request, same session" requirement before
✅ **Verified the isolation design empirically, not just by reasoning** — wrote and ran a standalone script confirming a real `IntegrityError` inside the SAVEPOINT leaves the session healthy and the outer transaction still commits, then used that same finding to both validate the existing design and identify the one case it didn't yet cover (a genuinely broken session)
✅ **Code review dismissals backed by direct verification, not argument** — confirmed the "no test cleanup" claim was false by checking the test fixture never commits; confirmed the "inconsistent import style" claim was false by grepping the file's own existing imports; confirmed the "no auth check" claim matched established precedent by reading the precedent it claims to mirror
✅ **Diagnosed an environment failure (Docker Desktop down) as environmental, not a regression, before assuming the code broke** — checked `docker ps` directly rather than debugging the code first
✅ **Zero regressions across all full-suite runs** — 431 → 432 passed, identical 3 pre-existing failures at every stage

---

## Deferred Items (Not Story 6-4 Scope)

1. **A concurrent transaction reading the target Skill before this request's own commit still sees `ever_assigned = False`** — inherent to this codebase's single-commit-per-request model, true of every write in every endpoint here, not fixable without redesigning that shared architecture
2. **Two concurrent `create_assignment_service` calls against the same never-before-assigned `skill_id` could have the second request's `UPDATE` block on a row lock** — matches the exact class of gap already accepted in Story 6.3's review for this same low-concurrency internal admin tool
3. **A Skill hard-deleted concurrently with an in-flight `create_assignment_service` call for it** — reasoned to already be protected by Postgres's FK `RESTRICT` + `FOR KEY SHARE` row locking; any residual gap is a pre-existing, unrelated hole in `create_assignment_service`'s error handling, not introduced by this story

---

## Conclusion

Story 6-4 is **✅ DONE** after a from-scratch story-creation-and-implementation cycle followed by one full adversarial code review pass and a commit/push to the shared branch:

- All 3 acceptance criteria satisfied, including a genuinely new transactional-isolation pattern for this codebase, empirically verified rather than assumed correct
- The exact gap all 3 of Story 6.3's review layers flagged is now closed, confirmed live via `curl`, not just at the test level
- 3 patches applied from this story's own code review, including a real correctness gap in the failure-isolation design's edge case
- Zero regressions across every full-suite run (431 → 432 passed)
- 3 items explicitly deferred (all pre-existing/systemic characteristics of this codebase, not new gaps this story introduced) rather than silently absorbed or ignored
- An unrelated environment failure (Docker Desktop down) correctly diagnosed and resolved without being mistaken for a code regression
- Committed (`f065a93a`) and pushed to `origin/POC_Hackathon`

**Ready for:** Story 6.5 (Per-Admin & Org-Wide Credential Storage, FR-16/AD-10) — the next `backlog` story in Epic 6.
