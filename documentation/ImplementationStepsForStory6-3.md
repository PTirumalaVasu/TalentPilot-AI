# Implementation Steps for Story 6-3: Skill Edit & Delete — Permanent Lock Enforcement (FR-21/22)

**Story Key:** 6-3-skill-edit-and-delete-permanent-lock-enforcement
**Epic:** 6 (Admin-Assisted Content Sourcing)
**Status:** ✅ DONE
**Completed Date:** 2026-09-09

---

## Overview

Story 6-3 adds `PATCH`/`DELETE /api/admin/skills/{id}` on top of the `skills/` module Stories 6.1/6.2 built. An HR Admin can rename/re-describe or hard-delete a Skill, but only while it has never been assigned to an Employee (`ever_assigned = false`, AD-11's one-way lock flag) — both endpoints return `403 Forbidden` once that flag is set, never a silent no-op, never a 404. A rename runs the same case-insensitive duplicate check Story 6.2 established, excluding the Skill's own current name, and recomputes the embedding only when `name`/`description` actually change. A delete hard-removes the Skill row and cascades into any admin-approved `content_catalog` rows attached to it, atomically.

This story started life as a **command/argument mismatch**: the user invoked `/bmad-code-review` but the argument text read "implement the story 6-3-skill-edit-and-delete-permanent-lock-enforcement." Rather than either blindly follow the command name (and review a diff that didn't exist for 6-3) or blindly follow the argument text (and silently swap workflows), the session surfaced the contradiction to the user directly and asked which was intended. The user confirmed: create and implement the story. Only after that story was actually implemented did the user separately invoke `/bmad-code-review` for real, which is where the adversarial review — and one live, currently-exploitable gap it caught — happened.

---

## Agents Invoked

### 1. **Blind Hunter (Code Review Agent)**

**Purpose:** Adversarial general review — bugs, logic errors, contradictions with the code's own claims, architectural violations.

**When Invoked:** Step 02 of the second `/bmad-code-review` invocation
**Model Capability:** Sonnet 5 (session model)
**Input:** Instructed to reconstruct the diff itself (`git diff HEAD` plus two new untracked files) rather than receiving a pasted diff blob, and to invoke the `bmad-review-adversarial-general` skill against it

**Key Findings Identified:**
- **The headline finding, independently converged on by all 3 layers:** `assignments/service.py::create_assignment_service` (live at `POST /api/assignments`) never calls a flag-setter — `mark_ever_assigned` doesn't exist anywhere in the codebase (it's Story 6.4's scope, still `backlog`). Net effect: an HR Admin can assign a Skill via the existing live endpoint today, then still rename/delete that same "assigned" Skill via this story's brand-new endpoints, silently defeating AC2 for every Skill assigned since migration 004's backfill.
- `delete_skill_service` had no `IntegrityError` handling around the delete, unlike `update_skill_service`'s existing rename-race handling — reachable *because* of the finding above, and would surface as a raw 500 instead of a clean 403
- The cascade-delete's safety argument rests on an unenforced cross-table invariant (`assignments.content_id → content_catalog.id` is still plain `RESTRICT`) that the story's own prose asserts is safe but nothing in the diff guards
- No TOCTOU/row-count safety on the update/delete paths under real concurrency
- `update_skill_service` performed a real `UPDATE` even when nothing had actually changed, because the write-dict was gated on field *presence*, not value *change*
- Missing test coverage on the PATCH path for behavior already covered on POST/create (blank-name, >255 chars) and the one behavior `UpdateSkillRequest`'s own docstring calls out (explicit-`null`-clears-`description`) but never tests
- Migration 007's `downgrade()` silently implied a full rollback with no warning that already cascade-deleted `content_catalog` rows can't be un-deleted
- A documentation-tone observation about `sprint-status.yaml`/`project-context.md` reading as pre-emptively finalized despite self-flagging "not yet reviewed"
- No dedicated `test_skills_repository.py` coverage for the new repository functions

**Output:** 12 findings; after triage, the root cause of 4 of the 6 applied patches plus the primary decision-needed item, 1 dismissed as matching existing precedent, 1 dismissed as out-of-scope documentation tone

---

### 2. **Edge Case Hunter (Code Review Agent)**

**Purpose:** Boundary conditions, unhandled branches, race windows.

**When Invoked:** Step 02 of the second `/bmad-code-review` invocation (parallel with Blind Hunter)
**Model Capability:** Sonnet 5 (session model)
**Input:** Same self-reconstructed-diff instructions, targeting the `bmad-review-edge-case-hunter` skill

**Key Findings Identified (structured JSON, location/trigger/guard/consequence per item):**
- `UpdateSkillRequest.name` is typed `str | None`, and the blank-name validator only checked the non-`None` arm — an explicit `{"name": null}` sailed through untouched
- That `None` then defeated the case-insensitive duplicate check (SQL `lower(NULL)` never matches anything in a `WHERE` clause), flowed into `repository.update_skill`, and violated `skills.name`'s `NOT NULL` constraint at flush — raising a raw `IntegrityError` the race-handler's fallback re-query (also querying with `name=None`) couldn't resolve, bare-re-raising as an unhandled 500
- Independently confirmed the same reachable-`IntegrityError`-on-delete gap Blind Hunter found, tracing it to the exact same root cause (a stale `ever_assigned` flag)
- Independently confirmed the same no-op-write gate gap Blind Hunter found
- No row-count check on the `DELETE` statement itself — a second, racing delete of an already-gone row still reports `204` as if it succeeded

**Output:** 7 structured findings; 3 merged with Blind Hunter's independently-found duplicates into single unified findings, 1 became the null-name patch (also independently confirmed by the Acceptance Auditor), 1 folded into the TOCTOU-race deferral

---

### 3. **Acceptance Auditor (Code Review Agent)**

**Purpose:** Verify the diff against Story 6-3's literal Given/When/Then acceptance criteria and its own Scope Notes.

**When Invoked:** Step 02 of the second `/bmad-code-review` invocation (parallel with the other two layers)
**Model Capability:** Sonnet 5 (session model)
**Input:** Story spec file (full) + self-reconstructed diff + pointers to `epics.md` Story 6.3 and the architecture spine's AD-11 section for context

**Key Findings Identified:**
- **Real, literal AC violation:** the rename-conflict `409` reused `_conflict()` unmodified, attaching the same `existing_skill` redirect payload create's `409` carries — directly contradicting AC1's explicit "no redirect payload" requirement for rename (there is no sensible "use existing skill" merge action when renaming). The story's own tests had locked this wrong behavior in as an assertion.
- Independently confirmed the null-name `IntegrityError`→500 path Edge Case Hunter found, framing it as a spec-asymmetry issue (only `description` was ever documented as null-clearable)
- Explicitly confirmed everything else as correct against the spec: the `ever_assigned` lock check is a plain column read with no cross-module join (AD-11 point 2), not-found-vs-locked ordering is correct, self-name-exclusion and conditional-embedding-recompute match the Scope Notes, the `content_catalog` cascade via migration 007 correctly satisfies AC4/AD-1/AD-8

**Output:** 2 findings (both real, both merged into patches — the rename-payload violation became its own patch; the null-name finding merged with Edge Case Hunter's), plus an explicit correctness checklist covering every other AC clause

---

## Skills Invoked

### 1. **`/bmad-code-review` Skill — First Invocation (Redirected)**

**Purpose:** The user's original literal command.

**When Invoked:** Session start, command `/bmad-code-review` with argument text "implement the story 6-3-skill-edit-and-delete-permanent-lock-enforcement"
**Outcome:** Step 01 (Gather Context) surfaced the contradiction between the command name and the argument text, and confirmed via direct inspection that Story 6-3 was `backlog` in `sprint-status.yaml` with no story file, and the current uncommitted diff belonged entirely to the already-`done` Story 6.2 (confirmed via `deferred-work.md`/`sprint-status.yaml` cross-reference) — there was nothing that could be called "Story 6-3's changes" to review. Presented this to the user with three options (create+implement Story 6-3, review the current Story-6.2-shaped diff as literally requested, or something else); **user chose create+implement Story 6-3**.

---

### 2. **`/bmad-create-story` Skill**

**Purpose:** Generate a comprehensive story file with full context before implementation.

**When Invoked:** Immediately after the redirect above, args `6-3-skill-edit-and-delete-permanent-lock-enforcement`
**Workflow Steps Executed:**
1. Pulled Story 6.3's full literal AC text from `epics.md`, plus the surrounding Epic 6 framing and Story 6.4's text (which explicitly names itself as what makes 6.3's lock "actually engage")
2. Read the architecture spine's AD-11 section in full (all 5 points — sole ownership, local-flag-not-live-join, `assignments/` sets the flag, embedding-on-write, content-sourcing is lock-agnostic)
3. Read the actual current code directly: `skills/{models,repository,service,schemas,router}.py` (Story 6.1/6.2's existing state), `assignments/models.py` (the `content_catalog.skill_id`/`assignments.skill_id` FK definitions, both plain `RESTRICT`), `auth/service.py` (`require_hr_admin`'s exact gate shape), `core/db.py`/`core/errors.py` (transaction and error-contract conventions), and Story 6.2's own completed story file for its exact patterns (the `_conflict()` helper, the `IntegrityError`→409 race-conversion idiom, the live-DB test conventions)
4. Identified and resolved the story's one real, undocumented architecture gap during story-writing itself (not left for the dev pass): cascading a Skill delete into `content_catalog` without letting `skills/` depend on `content/` (AD-8 forbids it) — resolved as a DB-level `ON DELETE CASCADE` migration rather than a cross-module service call, and wrote this reasoning directly into Scope Note 3
5. Generated the story file with 10 Scope Notes recording every judgment call, then implemented it directly in the same session rather than stopping at `ready-for-dev`

**Output File:** `_bmad-output/implementation-artifacts/6-3-skill-edit-and-delete-permanent-lock-enforcement.md`
**Sprint Status:** `6-3-skill-edit-and-delete-permanent-lock-enforcement`: `backlog` → `review` (implemented in the same pass, not stopped at `ready-for-dev`)

---

### 3. **Direct Implementation (same session, no separate `/bmad-dev-story` invocation)**

**Purpose:** Implement the story per its own Tasks.

**When Invoked:** Immediately after story creation, in the same turn
**Steps Executed:**
1. Added `UpdateSkillRequest` to `skills/schemas.py` (extracted a shared `_reject_blank` helper from `CreateSkillRequest`'s existing validator)
2. Added `get_skill_by_id`, `update_skill`, `delete_skill` to `skills/repository.py` — `delete_skill` deliberately issues a Core-level `delete(Skill).where(...)` rather than `session.delete(<ORM object>)`, so the ORM's unit-of-work never touches the `content_items` relationship and the DB's own `ON DELETE CASCADE` does the cascade
3. Added `update_skill_service`/`delete_skill_service` to `skills/service.py`, plus `_not_found()`/`_locked()` error helpers alongside the existing `_conflict()`
4. Added `PATCH`/`DELETE /{skill_id}` routes to `skills/router.py`
5. Wrote `backend/alembic/versions/007_content_catalog_skill_cascade_delete.py` (drops and recreates `content_catalog_skill_id_fkey` with `ondelete='CASCADE'`), then **applied it live**: rebuilt the `talentpilot-ai-backend` Docker image, recreated the container, verified via `psql`'s `\d content_catalog` that the constraint now shows `ON DELETE CASCADE` and `alembic_version = 007`
6. Wrote 26 new tests (13 in `test_skills_service.py`, 13 in `test_skills_router.py`) covering the full AC matrix
7. Ran the full backend suite before and after, confirming the same 3 pre-existing, unrelated failures and zero regressions (413 passed, up from 388)

**Output:** Story file updated with completed Tasks, Dev Agent Record, File List, Change Log; status set to `review`
**Sprint Status:** `6-3-...`: `review`

---

### 4. **`/bmad-code-review` Skill — Second Invocation (The Actual Review)**

**Purpose:** Adversarial review of the finished implementation against the story's own spec, structured triage, and patch application.

**When Invoked:** User request: "do the code review for story 6-3" (a genuine, matching invocation this time)
**Workflow Steps Executed:**

- **Step 01 (Gather Context):** Spec file resolved via Tier 1 (explicit story-key argument). The story's own frontmatter `baseline_commit` (`3849efad`) was found to be **stale** — Story 6.2 had since been committed separately (`a078c80b`) — so diffing from it would have pulled Story 6.2's already-reviewed work back into this review. Overrode to the correct, precise target: uncommitted changes (`git diff HEAD` + 2 new untracked files, ~898 insertions/25 deletions across 10 files), which isolates exactly Story 6.3's work. Checkpoint presented and confirmed by the user before launching review agents.
- **Step 02 (Review):** Launched Blind Hunter, Edge Case Hunter, and Acceptance Auditor in parallel subagents (`review_mode = "full"`, story file as spec). Rather than pasting a diff blob into each prompt, each agent was instructed to reconstruct the diff itself (`git diff HEAD` + reading the two new files directly) — avoiding transcription risk on a ~1,100-line diff.
- **Step 03 (Triage):** Normalized 21 raw findings from the 3 layers. Verified every finding against the real, current source (not just the diff hunk) before rating — confirmed live, via `grep`/direct file reads, that `mark_ever_assigned` genuinely doesn't exist anywhere in the codebase and that `POST /api/assignments` really is live and mounted; confirmed via `test_skills_repository.py`'s actual contents that Story 6.2's own repository functions also got no dedicated repository-layer tests (settling the "missing repository tests" finding as matching precedent, not a new gap); confirmed via this codebase's own Story 3.7 precedent that an idempotent-204-on-repeat-delete is an established, deliberate convention, not a defect. Routed the result into 1 decision-needed, 6 patch, 1 defer (initially), 2 dismiss.
- **Step 04 (Present and Act):** Findings written to the story file's new "Review Findings" subsection. The 1 decision-needed item — the live, currently-exploitable `ever_assigned`-not-yet-set gap — was presented to the user with both options (ship as-is and do Story 6.4 next, or pull a minimal slice of 6.4 forward into this story); **user chose to ship as-is**, matching epics.md's own planned sequencing. That resolution was recorded as a second deferred item. User then chose "apply every patch" for the 6 patch findings.

**Decision Resolved:**
- `ever_assigned` is not yet set by the only live Assignment-creation path — **accepted as a known, intentionally-sequenced gap** (Story 6.4's own epics.md text: "so that Story 6.3's permanent lock actually engages the first time a Skill is assigned"), not a Story 6.3 defect to fix here. Logged to `deferred-work.md`; closes automatically once Story 6.4 ships.

**Patches Applied:**
1. `delete_skill_service` now wraps the delete in `try/except IntegrityError`, rolls back, and converts to the same clean `_locked()` 403 instead of letting a real FK violation surface as a raw 500 — defensive coverage for exactly the scenario the decision above describes
2. `UpdateSkillRequest.name`'s validator now explicitly rejects `None` (a clean 422) — only `description` remains null-clearable, per the story's own Scope Note 6
3. A new `_rename_conflict()` helper (no `extra` payload) replaces `_conflict()` at both rename-conflict call sites, matching AC1's explicit "no redirect payload" requirement; the two existing tests that had locked in the wrong (`existing_skill`-present) behavior were corrected
4. `update_skill_service`'s write-dict is now gated on `name_changed`/`description_changed` instead of mere field presence — a true no-op PATCH no longer performs a real `UPDATE`+`flush`+`refresh`
5. Added the missing PATCH-path test coverage: blank-name → 422, name over 255 chars → 422, `extra="forbid"` rejects an unknown field → 422, explicit `{"description": null}` actually clears the field — plus a new schema-level unit test for the null-name rejection and a new service-level test that **constructs the exact stale-flag scenario directly** (a committed `Assignment` referencing a Skill whose `ever_assigned` still reads `false`) to prove patch 1 actually converts the resulting `IntegrityError` to a 403 rather than a 500
6. Added a comment to migration 007's `downgrade()` noting the schema-only/data-loss asymmetry — any `content_catalog` rows already cascade-deleted while the migration was live can't be restored by a downgrade

**Output:** Story status → `done`; full suite re-verified at 422 passed (up from 388 before this story) / 2 skipped / same 3 pre-existing failures

**Documentation Generated:**
- Code review findings + resolutions written directly into the story file's Review Findings subsection
- 2 deferred items logged to `deferred-work.md` under a new dated heading (the `ever_assigned` sequencing gap; the TOCTOU/row-locking gap on concurrent update/delete)
- `project-context.md` updated with both the implementation and the review outcome, per this project's own mandatory-update convention
- Sprint status synced (`6-3-...`: `backlog` → `review` → `done`)

---

## Files Created/Updated

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/007_content_catalog_skill_cascade_delete.py` | `content_catalog.skill_id` FK gains `ON DELETE CASCADE` — resolves AC4's cascade requirement without a forbidden `skills/` → `content/` dependency; code-review patch added a data-loss-asymmetry comment on `downgrade()` |
| `backend/tests/test_skills_router.py` extensions | (extends the existing Story 6.2 file — see below, not a new file) |

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/skills/schemas.py` | `UpdateSkillRequest`; code-review patch: explicit `null` rejected for `name` |
| `backend/app/skills/repository.py` | `get_skill_by_id`, `update_skill`, `delete_skill` |
| `backend/app/skills/service.py` | `update_skill_service`, `delete_skill_service`, `_not_found`, `_locked`; code-review patches: `_rename_conflict()` helper (no redirect payload), `IntegrityError` handling on delete, write-dict gated on actual value change |
| `backend/app/skills/router.py` | `PATCH`/`DELETE /{skill_id}` routes |
| `backend/tests/test_skills_service.py` | 13 new tests for update/delete service functions; code-review patches: fixed the rename-conflict payload assertion, added null-name/null-description-clears/stale-flag-delete tests |
| `backend/tests/test_skills_router.py` | 13 new tests for the `PATCH`/`DELETE` routes; code-review patches: fixed the rename-conflict payload assertion, added null-name/blank-name/max-length/extra-forbid/null-description-clears tests |

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/6-3-skill-edit-and-delete-permanent-lock-enforcement.md` | Story file — ACs, Scope Notes, Dev Notes, Review Findings, Dev Agent Record |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `6-3-...`: `backlog` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | 2 items added under a new "Deferred from: code review of 6-3-..." heading |
| `_bmad-output/project-context.md` | Implementation + review outcome appended, per this project's own mandatory-update rule |
| `documentation/ImplementationStepsForStory6-3.md` | This file |

### Not Changed (by design)

- `backend/app/skills/models.py` — schema/flag already correct from Story 6.1; no ORM changes needed
- `backend/app/main.py` — router already mounted at `/api/admin/skills` in Story 6.2
- `backend/app/assignments/service.py::create_assignment_service` — deliberately **not** touched; wiring `mark_ever_assigned` into it is Story 6.4's explicit scope, not this story's, even though the code review flagged the resulting gap

---

## Implementation Workflow Summary

### Phase 0: Redirect
**Skill:** `/bmad-code-review` (first invocation)
- Command name and argument text contradicted each other (`/bmad-code-review` vs. "implement the story...")
- Confirmed directly that Story 6-3 had no story file and the current diff belonged to the already-`done` Story 6.2
- User chose to create and implement Story 6-3 instead

### Phase 1: Story Creation
**Skill:** `/bmad-create-story`
- Read Story 6.3's AC from `epics.md`, AD-11 from the architecture spine, and the live Story 6.1/6.2 code directly
- Identified and resolved the one real architecture gap (content-cascade vs. the AD-8 module boundary) during story-writing, not left for the dev pass
- Generated the story file with 10 Scope Notes

### Phase 2: Implementation
**(direct, same session, no separate skill invocation)**
- Implemented schemas, repository, service, router; wrote and applied migration 007 live against the running Docker Postgres
- 26 new tests; full regression pass — 413 passed, 2 skipped, same 3 pre-existing failures
- Story marked `review`

### Phase 3: Code Review
**Skill:** `/bmad-code-review` (second invocation)
- 3 parallel adversarial layers, single pass
- **Findings:** 21 raw → 10 after dedup → 1 decision-needed, 6 patch, 2 defer, 2 dismiss
- **Top issue:** `ever_assigned` is never set by the only live Assignment-creation path, independently found by all 3 layers — a real, live gap this story's own lock-check code can't see, but one that epics.md itself sequences as Story 6.4's job to close. User chose to ship as-is.
- **Action:** Decision resolved (defer to Story 6.4); all 6 patches applied, including a defensive fix (delete-path `IntegrityError` handling) and a genuine AC violation (rename's forbidden redirect payload)
- Output: 422 passed (up from 388 before this story), 2 skipped, same 3 pre-existing failures; story marked `done`

---

## Test Coverage

### New/Extended Test Files (35 tests total from this story)
- `test_skills_service.py` — 17 new tests: rename success + embedding recompute, unchanged-value no-recompute, partial-update semantics, self-name-exclusion, cross-skill 409 (no redirect payload), locked→403 on both endpoints, nonexistent→404 on both, delete-with-no-content, delete-cascades-content, EMPLOYEE→403 on both, schema-level null-name rejection, explicit-null-description-clears-it, and a dedicated stale-`ever_assigned`-flag delete test proving the `IntegrityError`→403 conversion against a real committed Assignment
- `test_skills_router.py` — 18 new tests: the same matrix at the HTTP layer (200/403/404/409/204), unauthenticated→401, partial-update leaves the other field untouched, explicit-null-description-clears-it, null-name→422, blank-name→422, name-over-255→422, unknown-field (`extra="forbid"`)→422

### Regression Verification
- Full suite run before implementation, after implementation, and after the code review's patches — 388 (pre-story baseline) → 413 (post-implementation) → 422 (post-review) passed, with the same 3 pre-existing, unrelated failures at every stage
- Every finding verified against the real, current source before being accepted — not rated from the diff hunk alone (per this codebase's own established review-triage discipline)

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AD-11 point 2: local-flag lock, not a live join** | `update_skill_service`/`delete_skill_service` check `skill.ever_assigned` as a plain column read — no query against `assignments` from `skills/` | `skills/service.py` |
| **AD-1/AD-8: module ownership + one-way dependency** | Resolved the content-cascade requirement (AC4) via a DB-level `ON DELETE CASCADE` migration instead of a `skills/` → `content/` service call, which AD-8 forbids | `backend/alembic/versions/007_content_catalog_skill_cascade_delete.py`, `skills/repository.py::delete_skill` |
| **AD-6: server-side HR_ADMIN gate** | Both new service functions call `require_hr_admin(current_user)` first, matching `create_skill_service`'s established pattern | `skills/service.py` |
| **Established `IntegrityError`→clean-error conversion idiom (Story 6.2 precedent)** | Applied to rename (pre-existing in the initial implementation) and, after code review, to delete as well | `skills/service.py` |

---

## Key Technical Achievements

✅ **Surfaced a command/argument contradiction instead of guessing** — asked the user which was actually intended rather than silently picking one interpretation
✅ **Resolved a real, undocumented architecture gap during story-writing** — cascading a Skill delete into a table owned by a module `skills/` is forbidden from depending on, closed with a DB-level referential action instead of bending the module boundary
✅ **A live, currently-exploitable gap found by 3 independent review layers, resolved via an explicit user decision rather than a unilateral judgment call** — `ever_assigned` isn't set by the only live Assignment-creation path yet; shipped as a documented, sequenced gap (closes with Story 6.4) rather than silently absorbed or silently left un-flagged
✅ **A genuine, literal AC violation caught by the Acceptance Auditor** — the rename 409 carried a redirect payload the spec explicitly said it must not, and the story's own tests had locked the wrong behavior in; both the code and the tests were corrected
✅ **A defensive fix that directly targets the live gap's blast radius** — even though the `ever_assigned`-not-yet-set gap itself was deferred, the delete path's missing `IntegrityError` handling (which that gap makes reachable *today*) was fixed and proven with a test that constructs the exact scenario directly, not just asserted in prose
✅ **Zero regressions across three full-suite runs** — 388 → 413 → 422 passed, identical 3 pre-existing failures at every stage

---

## Deferred Items (Not Story 6-3 Scope)

1. **`ever_assigned` is not yet set by the live Assignment-creation path** — closes automatically once Story 6.4 (`assignments/`'s `mark_ever_assigned` wiring) ships; a known, intentionally-sequenced gap per epics.md's own design, not a standalone follow-up item
2. **No row-level locking/TOCTOU guard on concurrent update/delete of the same Skill** — very low likelihood for this internal, admin-only, low-concurrency tool; no other endpoint in this codebase implements row-level locking either

---

## Conclusion

Story 6-3 is **✅ DONE** after a from-scratch story-creation-and-implementation cycle (triggered by resolving a command/argument mismatch) followed by one full adversarial code review pass:

- All 5 acceptance criteria satisfied, including the cascade-delete requirement resolved via a clean architectural decision (DB-level FK, not a cross-module call)
- 1 real, live gap found by all 3 review layers, resolved via an explicit user decision (ship as-is, close it with Story 6.4) rather than a unilateral call — but its immediate blast radius (an unhandled 500 on the delete path) was fixed regardless
- 6 patches applied, including a genuine literal AC violation (rename's forbidden redirect payload) and a null-input crash (`{"name": null}`)
- Zero regressions across three full-suite runs (388 → 413 → 422 passed)
- 2 items explicitly deferred rather than silently absorbed or ignored

**Ready for:** Story 6.4 (Wire `ever_assigned` Into Assignment Creation, AD-11 point 3) — the natural next pick, since it directly closes this review's deferred decision.
