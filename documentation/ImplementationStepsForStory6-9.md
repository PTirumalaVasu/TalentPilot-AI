# Implementation Steps for Story 6-9: Reject the Currently Approved Content Link (FR-23)

**Story Key:** 6-9-reject-the-currently-approved-content-link
**Epic:** 6 (Admin-Assisted Content Sourcing)
**Status:** ✅ DONE
**Completed Date:** 2026-09-10

---

## Overview

Story 6.9 gives an HR Admin the explicit "undo" half of Story 6.8's approve action: `DELETE /api/admin/content/{content_id}/reject`. It hard-deletes a `content_catalog` row that was written with `origin: "ADMIN_LOOKUP"` (Story 6.8's own signal, named as the exact filter Story 6.9 would need back when Story 6.8 was implemented), returns `204 No Content`, requires no confirmation, and is never gated by the owning Skill's `ever_assigned` lock — rejecting a bad or outdated link is exactly as valid for an actively-assigned Skill as an unassigned one (PRD FR-23, AD-11 point 5).

Per explicit user instruction ("start development api and ui for the story 6-9 ... refer the ux design if required"), scope was deliberately API + a narrow frontend slice pulled forward from Story 6.10 — the same category of deviation Stories 6.7 and 6.8 already made. Unlike Story 6.8, though, there was no existing disabled button to wire up: Story 6.10 has not yet built any "Currently Approved" UI at all, so this story built a brand-new standalone `CurrentlyApprovedContent.tsx` component directly from the UX spec's object IDs, exercised via a new dev-only route rather than the real (not-yet-built) Content Lookup Panel.

The most consequential part of this story was not in the epics text at all: reading `assignments.content_id`'s actual foreign-key definition revealed it had no `ON DELETE` action, meaning a hard-delete of a `content_catalog` row still referenced by a live `Assignment` would raise an unhandled Postgres `IntegrityError` (500) instead of the story's own promised `204`. This was found and fixed during story creation — before a line of implementation code was written — as a new migration (010, `ON DELETE SET NULL`, mirroring migration 007's identical precedent) and a new AC6, then explicitly live-verified end-to-end via a real `Assignment` row inserted through `psql`.

The work happened in three passes in the same overall session: (1) story creation, grounded in a direct read of `epics.md`'s Story 6.9 AC, the PRD's FR-23 text, the UX spec's "Currently Approved" section, the architecture spine's Consistency Conventions table (which literally names `/api/admin/content/{id}/reject [FR-23]`), and the live code Story 6.8 left behind; (2) full TDD implementation, task by task, including a live `pg_constraint` query to confirm the real FK name before writing the migration; (3) an adversarial code review pass that found and fixed two smaller but real correctness gaps — a Toast-message fallback bug and a test-cleanup ordering hazard — while correctly dismissing a long list of findings that turned out to be explicit spec decisions or precedent already shipped and reviewed in earlier stories.

---

## Agents Invoked

No dedicated research subagent was used during story creation — the live codebase (`content/schemas.py`, `content/service.py`, `content/repository.py`, `content/admin_content_router.py`, `assignments/models.py`, the architecture spine, the PRD, the UX spec, and Story 6.8's own story file) was read directly, since Story 6.8 had already established the exact module/router/service composition this story needed to extend.

### 1. **Blind Hunter (Code Review Agent)**

**Purpose:** Adversarial general review — bugs, logic errors, contradictions with the code's own claims, reliability/security concerns.

**When Invoked:** Step 02 of `/bmad-code-review`
**Model Capability:** Sonnet 5 (session model), isolated worktree
**Input:** Full diff (uncommitted changes against baseline `786b1aa4`, matching current `HEAD`) embedded directly in the prompt, ~734 net new lines across 12 files, instructed to invoke the `bmad-review-adversarial-general` skill against it

**Key Findings Identified (16 items):**
- Irreversible hard delete with no audit trail or `rejected_by`/`rejected_at` columns, unlike `Assignment`'s existing soft-delete pattern
- No confirmation prompt before an irreversible delete
- Migration 010's `ON DELETE SET NULL` silently nulls a live Assignment's `content_id` with no test against dashboard/Content Discovery rendering
- No `skill_id` scoping on the reject endpoint — any HR_ADMIN with a `content_id` can reject any Skill's content
- `origin == "ADMIN_LOOKUP"` as a bare string literal with no shared constant/enum
- Deploy-ordering hazard if the API ships before migration 010 actually runs
- Repository-level "hazard" of a prior `get_content_by_id` fetch followed by a Core-level bulk `delete()` in the same session
- Uniform 404 for "doesn't exist" vs. "not admin-sourced," with no distinguishing code
- Feature only reachable via a dev-only demo route, not a real end-user UI
- Hardcoded UI copy ("Approving a new link below will also replace this") presuming a specific parent layout
- Generic, non-differentiated frontend error handling across 403/404/500 failure modes
- Test-cleanup fragility in the AC6 test — manual `Assignment` cleanup only runs after its own assertion
- No isolated migration-only test of the raw Postgres FK constraint
- No structured logging on the hard-delete action
- Migration docstring's claimed precedent (migration 007) unverifiable from the diff alone
- No test exercises the adjacent reject-then-reattach workflow

**Output:** 16 findings; after triage — including verifying several claims directly against the actual live code and git history rather than the diff alone — 1 became a real patch (test-cleanup ordering), 6 became deferred items, 9 were dismissed as matching explicit spec/AC decisions or precedent already shipped and reviewed in Stories 6.3/6.7/6.8

---

### 2. **Edge Case Hunter (Code Review Agent)**

**Purpose:** Boundary conditions, unhandled branches, race windows.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with Blind Hunter)
**Model Capability:** Sonnet 5 (session model), isolated worktree
**Input:** Same diff, embedded in the prompt, targeting the `bmad-review-edge-case-hunter` skill

**Key Findings Identified (structured JSON, location/trigger/guard/consequence per item, 6 items):**
- Two concurrent reject calls for the same `content_id` race past the existence check — the "losing" request gets a `204` for an already-gone row instead of a `404`
- A hypothetical other FK referencing `content_catalog.id` without its own `ON DELETE SET NULL`/`CASCADE`
- `CurrentlyApprovedContent.tsx`'s `handleReject` has no `isMounted` guard — a component unmount mid-request risks a React state update on an unmounted component
- A `404` from a since-rejected-elsewhere race shows the same generic retryable error as any other failure, inviting an endless retry loop
- `skillName ?? 'this skill'` doesn't catch an empty string, only `null`/`undefined` — an empty-string `skillName` would render a Toast with a trailing blank
- Non-numeric text in the dev demo page's duration input produces `NaN` in the days-to-complete display

**Output:** 6 structured findings; the `??` vs `||` Toast-fallback bug was the one genuinely new, high-value finding that became this review's second patch (independently corroborating what Blind Hunter's error-handling finding gestured at, but with the exact reproducible trigger); the "other FK" finding was checked directly via `grep` and confirmed false (no other FK references `content_catalog.id` in this codebase today)

---

### 3. **Acceptance Auditor (Code Review Agent)**

**Purpose:** Verify the diff against Story 6.9's literal Given/When/Then acceptance criteria (including the new AC6) and its 12 numbered Scope Notes.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with the other two layers, background)
**Model Capability:** Sonnet 5 (session model)
**Input:** Story spec file (read directly, full, via its file path) + the same diff

**Key Findings Identified:**
- **One cosmetic, zero-behavioral-impact deviation:** the dev demo page renders `source` as a `<select>` dropdown rather than the literal "plain text `Input`" Scope Note 11 describes — a defensible implementation choice for a 3-value union-typed field, explicitly rated cosmetic by the auditor itself
- **One documentation-precision note, not a defect:** Task 6's own checklist wording ("removes the card's action controls") undersells that the whole card unmounts on success, though the actual behavior matches Scope Note 9 exactly
- **Explicitly confirmed compliant:** AC1 (hard delete via Core-level `delete()`, `204`, no body), AC2 (no confirmation), AC3 (not gated by `ever_assigned`), AC4 (uniform 404), AC5 (403 for EMPLOYEE, fetch-then-delete ordering), AC6 (migration 010's FK behavior, verified via the dedicated router test), Toast/error copy matching `ManualContentEntryForm.tsx`'s established convention, component props shape (Scope Note 8), route/prefix placement (Scope Note 4), and AD-1 router/service/repository layering

**Output:** Two low-severity, non-blocking observations; both dismissed after review (cosmetic implementation judgment call, and a checklist-wording nuance the auditor itself confirmed was not an actual defect)

---

## Skills Invoked

### 1. **`/bmad-agent-dev` (Amelia persona)**

**Purpose:** The user's entry point — "start development api and ui for the story 6-9-reject-the-currently-approved-content-link and refer the ux design if required."

**When Invoked:** Session start
**Outcome:** Loaded the `agent` block, recognized no story file existed yet for `6-9-...` (sprint-status showed `backlog`), read the epics AC, PRD FR-23 text, and the UX spec's "Currently Approved" section directly, and dispatched into `/bmad-create-story` before implementation.

---

### 2. **`/bmad-create-story` → `/bmad-dev-story` (story creation + implementation)**

**Purpose:** Ground the story in the real spec/architecture/UX/code, create the story file, then implement it in the same pass.

**When Invoked:** Immediately after Amelia activation
**Workflow Steps Executed:**
1. Pulled the full literal AC text for Story 6.9 from `epics.md` (lines 2369-2397) and FR-23's full text/consequences from the PRD (lines 365-374); read the architecture spine's AD-6/AD-11 (point 5's explicit "not gated by `ever_assigned`" rule) and its Consistency Conventions table (which explicitly names `/api/admin/content/{id}/reject [FR-23]`); read the full UX spec section for the "Currently Approved" card's exact object IDs and page-state copy (`content-lookup-current-approved`, `content-lookup-btn-reject`, lines 190-191, 276, 329, 378-383)
2. Read the actual current code directly: `content/service.py` (`attach_content`'s exact composition to sit alongside, `_not_found_skill()`'s pattern to mirror for a new `_not_found_content()`), `content/repository.py` (`get_content_by_id`'s existing reusability, confirming only a new `delete_content` was needed), `content/admin_content_router.py` (Story 6.8's file, confirming the new route belongs in the same file/prefix, not a new router), `content/schemas.py`, `assignments/models.py` (`ContentCatalog`'s `origin` column, `Assignment.content_id`'s FK definition), `skills/repository.py::delete_skill` and `skills/service.py::delete_skill_service` (the exact Core-delete/fetch-then-delete pattern to mirror), `frontend/src/features/admin/ManualContentEntryForm.tsx` and `frontend/src/components/ui/toast.tsx` (the frontend conventions to reuse)
3. **Discovered a real system gap by reading the schema directly, not from the epics text:** `backend/alembic/versions/001_initial_schema.py`'s `assignments.content_id` FK had no `ondelete=` action (defaults to Postgres `NO ACTION`) — confirmed live against the running dev Postgres container via a `pg_constraint` query (`assignments_content_id_fkey`, `confdeltype = 'a'`) before writing anything
4. Resolved 12 real design decisions during story-writing, written directly into 12 numbered Scope Notes: (a) API + a new standalone frontend component pulled forward from Story 6.10, by explicit user instruction — unlike Story 6.8, there was no existing disabled button to wire, since Story 6.10 has built no "Currently Approved" UI at all yet; (b) the endpoint is a flat resource route with no `skill_id` anywhere in it, so the epics AC's "does not belong to the given Skill" phrasing is read literally as just "was not admin-sourced"; (c) the `assignments.content_id` FK gap and its fix (migration 010, `ON DELETE SET NULL`), including the instruction to verify the live constraint name rather than assume it; (d) the new route belongs in the existing `content/admin_content_router.py`, not a new router file; (e) `reject_content`'s exact fetch-then-check-origin-then-delete shape, mirroring `delete_skill_service`; (f) `delete_content`'s Core-level-delete-not-ORM-delete reasoning, mirroring `skills/repository.py::delete_skill`; (g) no response body on success (`204`); (h) the new `CurrentlyApprovedContent.tsx` component's exact props shape — props-driven, not self-fetching, since no read endpoint exists yet for "give me a Skill's current approved Content" (that's Story 6.10's job); (i) the no-confirmation, immediate-call Reject behavior with the UX spec's exact Toast copy; (j) the new dev-route-ahead-of-its-page precedent, mirroring Stories 6.5/6.7; (k) no UX addendum needed — the existing object IDs already cover this
5. Generated the story file with 12 Scope Notes and a new AC6 (the Assignment-FK case), then implemented it directly in the same session, task by task, TDD red-green-refactor: migration 010 (verified live via `pg_constraint`, applied via `alembic upgrade head`, re-verified `confdeltype` changed from `'a'` to `'n'`) → `content/repository.py::delete_content` → `content/service.py::_not_found_content` + `reject_content` → `content/admin_content_router.py`'s new `DELETE /{content_id}/reject` route → `adminContentApi.ts::rejectContent` → `CurrentlyApprovedContent.tsx` → `CurrentlyApprovedContentDemo.tsx` + `App.tsx` route
6. Confirmed RED (missing-symbol `ImportError`) before every backend implementation step; frontend component tests passed 6/6 on first run
7. Full backend regression (621 passed, 2 skipped, 1 of the 3 documented pre-existing failures manifested — the other two confirmed passing both in this full run and in isolation, consistent with this codebase's already-documented test-order-dependent flakiness); full frontend regression (306/306); `tsc --noEmit` unchanged at 31 pre-existing errors; rebuilt and redeployed both Docker images; live-verified via `curl`: reject happy path (204, `psql`-confirmed hard delete), 404 nonexistent, 403 EMPLOYEE, plus **a dedicated live test of AC6 itself** — a real `Assignment` row inserted via `psql`, rejected via the API, re-queried via `psql` to confirm `content_id` became `NULL`, not a 500
8. Noted honestly, rather than overclaiming: interactive real-browser verification of the Reject-click → Toast flow was not performed (no Playwright/browser-automation tool available this session) — covered instead by `CurrentlyApprovedContent.test.tsx`'s automated assertions of the same behavior

**Output File:** `_bmad-output/implementation-artifacts/6-9-reject-the-currently-approved-content-link.md`
**Sprint Status:** `6-9-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` (created and implemented in the same pass)

---

### 3. **`/bmad-code-review` Skill**

**Purpose:** Adversarial review of the finished implementation against the story's own spec, structured triage, and patch application.

**When Invoked:** User request: "do the code review for s story 6-9-reject-the-currently-approved-content-link"
**Workflow Steps Executed:**

- **Step 01 (Gather Context):** Spec file resolved from the explicit story name in the user's request (Tier 1). `baseline_commit` (`786b1aa4`) confirmed to match current `HEAD` exactly, so diff source = uncommitted changes. Combined `git diff HEAD` (tracked modifications) with `git diff --no-index /dev/null <path>` per untracked new file (migration 010, `CurrentlyApprovedContent.tsx`, `CurrentlyApprovedContentDemo.tsx`, `CurrentlyApprovedContent.test.tsx`) into one saved diff (~888 lines, 12 files), read directly and embedded in each review-agent prompt. Checkpoint presented and confirmed before launching review agents.
- **Step 02 (Review):** Launched Blind Hunter and Edge Case Hunter as parallel isolated-worktree background subagents, plus the Acceptance Auditor as a third parallel background subagent given the story spec's file path directly (`review_mode = "full"`). All three returned independently.
- **Step 03 (Triage):** Normalized 24 raw findings (16 Blind Hunter + 6 Edge Case Hunter + 2 Acceptance Auditor observations) down to 23 distinct findings after dedup (two independent findings — the generic-error-handling observation and the empty-string Toast bug — turned out to describe related-but-distinct issues, not true duplicates). Read the actual code at every finding's location before rating severity — most consequentially, re-verified via `grep` that no FK besides `assignments.content_id` references `content_catalog.id` (disproving one Edge Case Hunter finding outright), and cross-checked the "repository get-then-delete hazard" and "no confirmation" findings directly against `skills/service.py::delete_skill_service` and the story's own AC2 text respectively, confirming both were either already-shipped precedent or explicit spec decisions, not new risks. Routed the result into 0 decision-needed, 2 patch, 6 defer, 15 dismiss.
- **Step 04 (Present and Act):** Findings written to the story file's new "Review Findings" subsection; 6 deferred items also logged to `deferred-work.md`. User chose "apply every patch."

**Patches Applied (both TDD — implemented, then re-verified GREEN):**
1. `CurrentlyApprovedContent.tsx`'s Toast fallback used `skillName ?? 'this skill'`, which does not catch an empty string (only `null`/`undefined`) — a future caller passing `skillName=""` would render a Toast with a trailing blank instead of the fallback text. Fixed: `skillName || 'this skill'`. 1 new test added covering the empty-string case.
2. `test_reject_content_succeeds_when_referenced_by_an_assignment_and_nulls_content_id`'s manual `Assignment` cleanup only ran after its own `content_id is None` assertion — if that assertion ever failed, the `Assignment` row would never be deleted, and the outer `finally`'s `_delete_skill_by_name` would then hit `assignments_skill_id_fkey`'s FK (no cascade), masking the real failure behind an unrelated `IntegrityError` and risking an orphaned row in the shared dev database. Fixed: `Assignment` cleanup restructured into its own unconditional inner `try/finally`, independent of the assertion's outcome.

**Output:** Story status → `done`; full regression re-verified — backend 621 passed / 2 skipped / same pre-existing-failure category; frontend 307/307 (1 net new); `tsc --noEmit` unchanged at 31 pre-existing errors.

**Documentation Generated:**
- Code review findings + resolutions written directly into the story file's Review Findings subsection (2 patches, 6 deferrals, 15 dismissals each with a one-line reason)
- 6 deferred items appended to `deferred-work.md` under a new "Deferred from: code review of 6-9-..." heading
- Sprint status synced (`6-9-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`)

---

## Files Created/Updated

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/010_assignments_content_id_set_null_on_delete.py` | Gives `assignments.content_id`'s FK `ON DELETE SET NULL` — the fix for the real, pre-existing gap this story discovered |

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/content/repository.py` | Adds `delete_content` (Core-level hard delete, no ORM-object load) |
| `backend/app/content/service.py` | Adds `_not_found_content`; adds `reject_content` (require_hr_admin → fetch-and-check-origin → delete → commit) |
| `backend/app/content/admin_content_router.py` | Adds `DELETE /{content_id}/reject`, `204 No Content`, thin — delegates to `content_service.reject_content` |
| `backend/tests/test_content_repository.py` | 2 new tests: `delete_content` removes an existing row; a nonexistent id is a silent no-op |
| `backend/tests/test_content_service.py` | 5 new tests: happy path, nonexistent 404, `origin="BATCH"` 404 (not deleted), EMPLOYEE 403, succeeds regardless of `ever_assigned` |
| `backend/tests/test_admin_content_router.py` | 6 new tests: happy path 204, EMPLOYEE 403, unauthenticated 401, nonexistent 404, `origin="BATCH"` 404, and the dedicated AC6 test (real `Assignment` row survives the reject as a clean 204 with `content_id` nulled); 1 restructured by the code-review patch |

### Frontend — New Files

| File | Purpose |
|------|---------|
| `frontend/src/features/admin/CurrentlyApprovedContent.tsx` | The "Currently Approved" card — green-tinted, source/title/days-to-complete, View/Reject, no confirmation, Toast on success, retryable inline error on failure |
| `frontend/src/tests/CurrentlyApprovedContent.test.tsx` | 7 tests (6 initial + 1 code-review patch): renders with/without duration, View opens the preview modal, Reject success (with/without `skillName`, including the empty-string case), Reject failure stays retryable |
| `frontend/src/pages/dev/CurrentlyApprovedContentDemo.tsx` | Dev-only demo page — text/select inputs for `contentId`/`title`/`source`/`url`/`duration_hours`/`skillName`, renders the component once a Content ID is entered |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/api/adminContentApi.ts` | Adds `rejectContent(contentId)` — thin typed `DELETE` client |
| `frontend/src/App.tsx` | Adds the new `/dev/currently-approved-content-demo` route, `RequireAuth`-wrapped like every other `/dev/*` route |

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/6-9-reject-the-currently-approved-content-link.md` | Story file — ACs (including the new AC6), Scope Notes, Dev Notes, Review Findings, Dev Agent Record |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `6-9-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | 6 deferred findings logged under a new heading |
| `documentation/ImplementationStepsForStory6-9.md` | This file |

### Not Changed (by design)

- The Skills Card Grid, Content Lookup Panel shell, Edit-mode Save-name wiring, Search-tab/Approve wiring — all Story 6.10's job, still `backlog`
- The real "give me a Skill's current admin-approved Content" read endpoint — `CurrentlyApprovedContent.tsx` is deliberately props-driven, not self-fetching; that composition is Story 6.10's job (extending `skills.service.list_all_skills()`)
- Any other content_catalog write path (`attach_content`, `manual_seed_content`, `ingest_content_for_skill`) — untouched

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skills:** `/bmad-agent-dev` → `/bmad-create-story`
- Discovered no story file existed yet for `6-9-...` (`backlog`) — created it directly
- Read the architecture spine's Consistency Conventions table, which explicitly names `/api/admin/content/{id}/reject [FR-23]` as the route to build — no guessing required on the URL shape
- **Found a real, undocumented system gap before writing any code** — `assignments.content_id`'s FK had no `ON DELETE` action, confirmed live via a `pg_constraint` query — and scoped its fix (migration 010) directly into the story as a new AC6, rather than discovering it mid-implementation or leaving it for a later review to catch
- Resolved 12 real design decisions during story-writing, documented as 12 numbered Scope Notes, including the deliberate reading of the epics AC's "given Skill" phrasing against the endpoint's actual skill-less signature

### Phase 2: Implementation
**(direct, same session, TDD red-green-refactor per task, both backend and frontend)**
- Migration 010 verified against the live constraint name via `pg_constraint` before writing it, then applied and re-verified live via `psql` (`confdeltype` changed `'a'` → `'n'`)
- 13 new backend tests (repository, service, router) + 6 new frontend tests
- RED confirmed (missing-symbol `ImportError`) before every backend implementation step
- Full regression pass — backend 621 passed / 2 skipped / 1 of 3 documented pre-existing failures manifested (test-order-dependent, not new); frontend 306/306; `tsc --noEmit` unchanged (31 pre-existing errors)
- Live end-to-end verification via `curl` against rebuilt Docker containers (happy path, 404, 403) **plus a dedicated live proof of AC6** — a real `Assignment` row inserted via `psql`, rejected via the API, re-queried to confirm the FK's `SET NULL` action fired correctly instead of raising an `IntegrityError`
- Story marked `review`

### Phase 3: Code Review
**Skill:** `/bmad-code-review`
- 3 parallel adversarial layers, all background subagents (two in isolated worktrees), single pass
- **Findings:** 24 raw → 23 after dedup → 0 decision-needed, 2 patch, 6 defer, 15 dismiss
- **Most findings were correctly dismissed as explicit spec decisions or already-shipped precedent, not new defects** — hard delete/no audit trail (PRD FR-23's own `[ASSUMPTION]`), no confirmation (AC2), no `skill_id` scoping (the endpoint's own literal signature), the fetch-then-Core-delete "hazard" (copied directly from Story 6.3's `delete_skill_service`), and a claimed-but-disproven "other FK" gap (verified via `grep` — none exists)
- **Two genuinely real, small correctness fixes applied:** a Toast-fallback `??`/`||` bug, and a test-cleanup ordering hazard that could mask a real assertion failure behind an unrelated FK error
- **Action:** user chose "apply every patch" — both patches applied with 2 new/updated tests, full regression re-verified
- Output: 621 passed backend (unchanged net count, same test file, restructured not added) / 307 passed frontend (up from 306); story marked `done`

---

## Test Coverage

### New/Extended Test Files (20 tests total from this story, post-review)

**Backend (13 new):**
- `test_content_repository.py` — 2 new: `delete_content` removes an existing row, nonexistent id is a silent no-op
- `test_content_service.py` — 5 new: happy path deletes the row, nonexistent 404, `origin="BATCH"` 404 (row untouched), EMPLOYEE 403 (row untouched), succeeds regardless of the Skill's `ever_assigned`
- `test_admin_content_router.py` — 6 new: happy path 204 (+ re-attempt 404), EMPLOYEE 403, unauthenticated 401, nonexistent 404, `origin="BATCH"` 404, and the dedicated AC6 test (real `Assignment` survives the reject with `content_id` nulled, not a 500)

**Frontend (7 new/updated):**
- `CurrentlyApprovedContent.test.tsx` — 6 initial (renders with/without duration estimate, View opens the preview modal, Reject success with/without `skillName` shows the right Toast and removes the card, Reject failure shows an inline retryable error) + 1 code-review-patch test (empty-string `skillName` falls back correctly)

### Regression Verification
- Full backend suite run after implementation and again after the code review's patch (621 passed both times, 2 skipped, same pre-existing-failure category since Story 6.4 — only 1 of the 3 historically-documented failures manifested in these particular full-suite runs, the other 2 independently confirmed passing both in-run and in isolation, consistent with this codebase's already-documented test-order-dependent flakiness, not a regression)
- Full frontend suite run after implementation (306 passed) and again after the patch (307 passed), zero failures at either stage
- `tsc --noEmit` explicitly checked before and after every change set — 31 pre-existing errors, unchanged by this story's changes at every stage, confirmed via a targeted grep that none of the 31 reference any file this story touched
- Live-verified end-to-end via `curl` against a rebuilt/redeployed Docker backend container: reject happy path (204, `psql`-confirmed hard delete), 404 nonexistent, 404 non-admin-sourced, 403 EMPLOYEE (row left untouched), and **AC6's own dedicated live proof** — a real `Assignment.content_id` reference surviving the reject as a clean 204 with the FK correctly nulled, confirmed via direct `psql` re-query
- Interactive real-browser verification of the Reject-click → Toast flow was not performed — honestly noted as not performed (no Playwright/browser-automation tool available this session) rather than overclaimed, covered instead by `CurrentlyApprovedContent.test.tsx`'s automated assertions

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AD-1: single-owner module, cross-module calls via Service API only** | The new route lives in the same `content/admin_content_router.py` file Story 6.8 already established (own prefix, per the Consistency Conventions table) but delegates all logic to `content/service.py::reject_content`, which never touches the `skills` table directly | `content/admin_content_router.py`, `content/service.py` |
| **AD-6: HR_ADMIN-only via service-layer gate** | `reject_content` calls `require_hr_admin(current_user)` first, before the fetch — same ordering as `attach_content`/`delete_skill_service` | `content/service.py` |
| **AD-11 point 5: FR-17/18/19/23 are Skill-agnostic w.r.t. `ever_assigned`** | `reject_content` never reads or checks the Skill row's lock flag at all — explicitly tested (`test_reject_content_succeeds_regardless_of_skill_ever_assigned`) | `content/service.py` |
| **FR-23: hard removal, no confirmation, not gated by assignment status** | `repository.delete_content`'s Core-level `DELETE`, the router's immediate `204` with no confirmation step in the frontend, and the `ever_assigned`-agnostic service logic together implement the full consequence list | `content/repository.py`, `content/admin_content_router.py`, `CurrentlyApprovedContent.tsx` |
| **System-integrity requirement beyond the epics text: a rejected row must not corrupt or crash an Assignment that referenced it** | Migration 010's `ON DELETE SET NULL` on `assignments.content_id`'s FK — found by reading the schema directly, not stated in any FR/AC, but necessary for AC1's own `204` promise to hold in every reachable state | `backend/alembic/versions/010_assignments_content_id_set_null_on_delete.py` |

---

## Key Technical Achievements

✅ **Found and fixed a real, undocumented system-integrity gap during story creation, before any implementation code existed** — `assignments.content_id`'s FK had no `ON DELETE` action, which would have made this story's own `204` promise false for the exact "Skill actively assigned to an Employee" case PRD FR-23 itself calls out as the most important one to support
✅ **Resolved a genuine spec-text ambiguity by reading the actual endpoint contract, not by inventing a parameter that doesn't exist** — the epics AC's "does not belong to the given Skill" phrasing implies a `skill_id` the endpoint's own literal signature (and the architecture spine's own route naming) never carries; documented the resolution directly in Scope Note 2 rather than silently adding an unrequested parameter
✅ **Reused established patterns instead of inventing new ones at every layer** — `delete_content` mirrors `skills/repository.py::delete_skill`'s exact Core-delete reasoning; `reject_content` mirrors `skills/service.py::delete_skill_service`'s exact fetch-then-delete shape; the migration mirrors migration 007's exact drop/recreate-named-constraint structure; the frontend component mirrors `ManualContentEntryForm.tsx`'s exact Toast/error-state conventions
✅ **Code review correctly separated real defects from explicit spec decisions** — 15 of 23 findings were dismissed as matching either this story's own explicit AC/Scope-Note text or precedent already shipped and reviewed in Stories 6.3/6.7/6.8, rather than being treated as blanket "issues" to chase; one claimed finding (another FK lacking `SET NULL`) was directly disproven via `grep` rather than accepted on faith
✅ **The two patches that were applied were genuinely new, narrow, and unambiguous** — a `??`/`||` fallback bug and a test-cleanup ordering hazard, both fixed with a one-line change plus a small test addition, no scope creep
✅ **Zero regressions across both full-suite runs, on both stacks, at every stage** — backend 606 → 621 passed (13 new tests + 2 previously-flaky tests passing in this run), frontend 300 → 307 passed, `tsc --noEmit` unchanged at 31 pre-existing errors throughout
✅ **Honest gap disclosure instead of a false completeness claim** — explicitly recorded that the Reject-click → Toast flow was verified via automated component tests, not an interactive browser session, matching the same honest-disclosure pattern established in Stories 6.7/6.8

---

## Deferred Items (Not Story 6-9 Scope)

Logged in `_bmad-output/implementation-artifacts/deferred-work.md` under "Deferred from: code review of 6-9-reject-the-currently-approved-content-link (2026-09-10)":

1. **Migration 010's `ON DELETE SET NULL` isn't directly exercised against dashboard/Content Discovery rendering** — the resulting `content_id = NULL` state itself is already covered by pre-existing tests reached a different way (a never-matched assignment); coverage-enhancement suggestion, not a new defect.
2. **`origin == "ADMIN_LOOKUP"` is a bare string literal with no shared constant/enum** — pre-existing pattern from Story 6.8's `attach_content`, not introduced newly-different here.
3. **Generic frontend error handling across all failure modes (403/404/500)** — a 404 from a since-rejected-by-another-admin race shows a permanently-retryable error instead of self-clearing. Matches `ManualContentEntryForm.tsx`'s identical established pattern, low likelihood given this pilot's small HR Admin pool.
4. **No idempotency/rowcount check on `reject_content`** — two concurrent rejects can give the "losing" request a 204 instead of a 404, though the end state (row deleted) is still correct. Matches Story 6.8's already-accepted tolerance for the identical attach-duplicate race.
5. **No service-layer logging on `reject_content`** — matches `attach_content`'s identical no-logging precedent.
6. **No test exercises the adjacent reject-then-reattach workflow** — coverage-enhancement suggestion, not a defect.

---

## Conclusion

Story 6-9 is **✅ DONE** after a story-creation-then-implement cycle (API + a new standalone frontend component pulled forward from Story 6.10, per explicit user instruction) followed by one full adversarial code review pass:

- All acceptance criteria satisfied, including a new AC6 this story itself discovered and added — confirmed independently by a clean Acceptance Auditor pass
- A real, previously-undocumented system-integrity gap (`assignments.content_id`'s missing `ON DELETE` action) found and fixed during story creation, before implementation began, then explicitly live-verified end-to-end
- A deliberate, documented scope choice versus the epics' own Story 6.10-only UI assignment, distinguished from Story 6.8's simpler "wire an existing button" precedent since no such button existed yet
- 2 patches applied from this story's own code review, both small and unambiguous; 15 other raised findings correctly dismissed as explicit spec decisions or already-shipped precedent rather than chased as blanket "issues"
- Zero regressions across every full-suite run, on both the backend and frontend stacks
- 6 items deferred with clear "how to apply" notes, none blocking
- Live-verified via `curl` against rebuilt Docker containers, including a direct `psql`-backed proof of the migration's `ON DELETE SET NULL` behavior against a real `Assignment` row
- One honestly-disclosed verification gap (interactive browser check of the Reject → Toast flow) rather than an overclaimed "done"
- Not yet committed to git in this session

**Ready for:** Story 6.10 (Skills Tab Frontend — Card Grid, Content Lookup, API Keys, Watch Modal), the last remaining story in Epic 6, still `backlog`.
