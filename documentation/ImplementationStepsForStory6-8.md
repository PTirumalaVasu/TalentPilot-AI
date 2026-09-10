# Implementation Steps for Story 6-8: Review, Approve & Estimate Days-to-Complete (FR-18, FR-19)

**Story Key:** 6-8-review-approve-and-estimate-days-to-complete
**Epic:** 6 (Admin-Assisted Content Sourcing)
**Status:** ✅ DONE
**Completed Date:** 2026-09-10

---

## Overview

Story 6.8 gives an HR Admin the actual write/approve action every reviewed candidate from Stories 6.6 (live search) and 6.7 (manual entry) has been waiting on: `POST /api/admin/content/attach`. It adds two new columns to `content_catalog` (`attached_by`, `origin`) via migration 009, extends the `source` enum to include `UDEMY`, and writes a real `content_catalog` row — `origin: "ADMIN_LOOKUP"`, `attached_by: <admin id>`, embedding computed from the title, `type` always hardcoded `"VIDEO"` — returning the full `ContentResponse` at `201`.

Per explicit user instruction ("start development api and ui for the story 6-8 ... the ux design if required"), scope was deliberately narrower than the epics' own full Story 6.10 UI assignment: only the manual-entry `[Approve]` button that Story 6.7 had already built — visibly present but hard-disabled, `title="Available once Story 6.8 ships"` — was wired live. The days-to-complete estimate (FR-19) needed zero new work: Story 6.7 had already built and displayed `estimateDaysToComplete` ahead of this story's endpoint existing. The Skills Card Grid, Content Lookup Panel shell, and Search-tab Approve wiring stay Story 6.10's job.

The work happened in three passes in the same overall session: (1) story creation, grounded in a direct read of `epics.md`'s Story 6.8 AC, the PRD's FR-18/FR-19 text, the UX spec's Content Lookup Panel section, the architecture spine's Consistency Conventions table (which literally names `/api/admin/content/attach`), and the live code Story 6.7 left behind; (2) full TDD implementation, task by task; (3) an adversarial code review pass that found and fixed a genuinely severe bug — the new endpoint wrote duration data in a shape the dashboard's own Status/percent derivation couldn't read, which would have permanently stuck every Assignment on admin-attached content at "In Progress, 0%."

---

## Agents Invoked

No dedicated research subagent was used during story creation — the live codebase (`content/schemas.py`, `content/service.py`, `content/repository.py`, `skills/router.py`, `assignments/models.py`, migrations 007/008, `admin_api_keys_router.py`, the UX spec, the PRD, and the architecture spine) was read directly, since Story 6.6/6.7 had already established the exact composition this story needed to mirror.

### 1. **Blind Hunter (Code Review Agent)**

**Purpose:** Adversarial general review — bugs, logic errors, contradictions with the code's own claims, reliability/security concerns.

**When Invoked:** Step 02 of `/bmad-code-review`
**Model Capability:** Sonnet 5 (session model)
**Input:** Full diff (uncommitted changes against baseline `a07c8690`, matching current `HEAD`) embedded directly in the prompt, ~1,027 lines across 13 files (production code; sibling test-file paths named for the agent to read directly if needed), instructed to invoke the `bmad-review-adversarial-general` skill against it

**Key Findings Identified (11 items):**
- **Duration data written in a shape the progress system can't read** — `content_metadata = {"duration_hours": ...}` vs. `ProgressRepository.get_video_duration`'s `content_metadata.get("duration")` read, permanently breaking dashboard completion tracking for admin-attached content
- **The same metadata fork breaks the batch job's de-dup key** — a YOUTUBE-sourced attach has no `video_id`, so the nightly ingestion job can't recognize it and would re-ingest the same video as a duplicate row
- No duplicate-attach protection anywhere (no unique constraint, no idempotency check)
- The "review" step isn't enforced server-side — any HR_ADMIN can POST straight to `/attach`, bypassing search/manual-review entirely
- Title length mismatch: `ContentLookupCandidate.title` has no `max_length` but `AttachContentRequest.title` caps at 255, producing a confusing generic 422 for an edge-case long title
- Migration 009's downgrade can't remove the `'UDEMY'` enum value (Postgres has no `ALTER TYPE ... DROP VALUE`), leaving a landmine if a downgrade ever runs after a UDEMY row was written
- `sprint-status.yaml`'s new changelog entries looked like literal placeholder ellipses
- `skillName` prop added with no live caller in this diff — "dead-on-arrival scope creep"
- No DB-level guard backs the client-side "already approved" state (double-click race)
- Redundant double `Depends(get_current_user)` in the new router (copied from `admin_api_keys_router.py` without questioning it)
- New write path never exercised through the service's own read APIs (`get_content`/`list_content_for_skill`) in tests

**Output:** 11 findings; after triage — including verifying one claim directly against the actual file rather than the diff excerpt sent to this agent — 2 became real patches (merged with Edge Case Hunter's independent findings on the same two issues), 1 became a deferred item, 1 was confirmed a false positive caused by this reviewer's own diff truncation, the rest were dismissed as matching existing accepted precedent or explicit out-of-scope text

---

### 2. **Edge Case Hunter (Code Review Agent)**

**Purpose:** Boundary conditions, unhandled branches, race windows.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with Blind Hunter)
**Model Capability:** Sonnet 5 (session model)
**Input:** Same diff, embedded in the prompt, targeting the `bmad-review-edge-case-hunter` skill

**Key Findings Identified (structured JSON, location/trigger/guard/consequence per item, 10 items):**
- `content_metadata`'s `"duration_hours"` key vs. the `"duration"` key the read path expects — independently confirmed the same core issue Blind Hunter raised, reproduced by reading `progress/repository.py`, `assignments/service.py`, and `dashboard/service.py` directly
- YOUTUBE-sourced attaches store no `video_id`, breaking future batch de-dup — same finding, independently raised
- No `thumbnail_url` carried into `content_metadata` for YOUTUBE/UDEMY-sourced attaches
- No duplicate/idempotency check before `create_content`
- Frontend `handleApprove` has no synchronous guard beyond the `disabled` prop, which updates only after render (double-click race)
- Migration downgrade can't remove the `'UDEMY'` enum value — same finding as Blind Hunter
- `duration_hours` requires `gt=0`, rejecting a legitimately-0-duration candidate
- `type` unconditionally hardcoded `"VIDEO"` regardless of the candidate's actual nature
- `handleReview` resets `candidate`/`approved`/`approveError` but not `toastMessage` — a stale approval toast can linger into a new review cycle
- No cross-check that the declared `source` matches the URL's domain

**Output:** 10 structured findings; the duration-metadata and video_id findings (independently confirmed against real call sites in `progress/repository.py` and `content/service.py::ingest_content_for_skill`) were the two genuinely new, high-value findings that became this review's headline patches; the stale-toast finding became the third patch

---

### 3. **Acceptance Auditor (Code Review Agent)**

**Purpose:** Verify the diff against Story 6.8's literal Given/When/Then acceptance criteria and its 12 numbered Scope Notes, and spot-check every cited precedent claim against the actual current code.

**When Invoked:** Step 02 of `/bmad-code-review` (parallel with the other two layers, background)
**Model Capability:** Sonnet 5 (session model)
**Input:** Story spec file (read directly, full) + the same diff, plus direct reads of `ManualContentEntryForm.tsx`, `ContentPreviewModal.tsx`, `content/schemas.py`, `content/service.py`, `content/repository.py`, `assignments/models.py`, migration 009, `admin_content_router.py`, `admin_api_keys_router.py`, `auth/service.py`, and every referenced test file

**Key Findings Identified:**
- **None requiring remediation.** Explicitly confirmed migration 009's additive shape and one-way `ADD VALUE` characteristic; the full `attach_content` composition (`require_hr_admin` → `get_skill_by_id`/`_not_found_skill()` → embed → write → `201`); the deliberate absence of `description`/`type` fields on the request schema; the router's double-`Depends` pattern matching existing precedent exactly; the 403-before-404 ordering matching `submit_manual_content`'s existing precedent; the frontend Approve wiring's exact request body, Toast text (with and without `skillName`), and error-state behavior; and that every Task 2/3/4/6 test list in the story file was actually implemented, not just declared complete
- One neutral observation noted (403-before-404 ordering), explicitly confirmed as pre-existing codebase behavior, not a deviation

**Output:** A fully clean pass — zero findings

---

## Skills Invoked

### 1. **`/bmad-agent-dev` (Amelia persona)**

**Purpose:** The user's entry point — "start development api and ui for the story 6-8-review-approve-and-estimate-days-to-complete the ux design if required."

**When Invoked:** Session start
**Outcome:** Loaded the `agent` block, recognized no story file existed yet for `6-8-...` (sprint-status showed `backlog`), and dispatched into `/bmad-create-story` before implementation.

---

### 2. **`/bmad-create-story` → `/bmad-dev-story` (story creation + implementation)**

**Purpose:** Ground the story in the real spec/architecture/UX/code, create the story file, then implement it in the same pass.

**When Invoked:** Immediately after Amelia activation
**Workflow Steps Executed:**
1. Pulled the full literal AC text for Story 6.8 from `epics.md` (lines 2331-2365) and FR-16 through FR-23's full text/consequences from the PRD; read the architecture spine's AD-1/AD-6/AD-8 and its Consistency Conventions table (which explicitly names `/api/admin/content/attach` as the route to build); read the full UX spec (`04.1-skills-content-sourcing.md`) for the Content Lookup Panel's Approve/days-to-complete object IDs and page-state copy
2. Read the actual current code directly: `content/schemas.py`, `content/service.py` (`submit_manual_content`'s exact shape to mirror, `_build_embedding_text`, `_not_found_skill`), `content/repository.py` (`create_content`'s arbitrary-dict acceptance, confirming no repository change was needed), `assignments/models.py` (`ContentCatalog`'s current columns and native-enum `source` type), migrations 007/008 (the only prior migration to touch `content_catalog`, and the org-credential-table precedent), `admin_api_keys_router.py` (the own-file/own-prefix router pattern to mirror), and Story 6.7's frontend pieces (`ManualContentEntryForm.tsx`'s disabled-Approve stub, `adminContentApi.ts`, `duration.ts`'s already-built `estimateDaysToComplete`, `toast.tsx`'s existing primitive)
3. Resolved 12 real design decisions during story-writing, written directly into 12 numbered Scope Notes: (a) API + a narrow frontend slice pulled forward from Story 6.10, by explicit user instruction — only the manual-entry Approve path, not the full Skills tab; (b) days-to-complete needed zero new work, already built by Story 6.7; (c) `content_source_enum` is a native Postgres enum, not a CHECK constraint — extending it means `ALTER TYPE ... ADD VALUE`, safe inside Alembic's default transactional DDL since the new value is never used in the same transaction; (d) `attached_by`/`origin` are both self-backfilling via their own column defaults, no explicit `UPDATE` needed; (e) a new `content/admin_content_router.py` file, not an existing router — different URL prefix from both `skills/router.py` and `content/router.py`; (f) no `description` field on the request — no upstream candidate shape carries one; (g) `type` never client-supplied, always hardcoded `"VIDEO"`; (h) `ContentResponse` deliberately NOT extended with `attached_by`/`origin` — nothing consumes them via the API yet; (i) `manual_seed_content`'s CLI path silently inherits `origin='BATCH'` too — a known, accepted, out-of-scope quirk; (j) the UX spec's panel-close/page-toast Approve-success behavior adapted to a standalone component with no panel or Skills Card Grid yet — an optional `skillName` prop with a generic fallback, reusing the existing `Toast` primitive; (k) Approve-error state matches the UX spec's "Couldn't approve this — Try again" text exactly; (l) no UX addendum needed, the existing object IDs already cover this
4. Generated the story file with 12 Scope Notes, then implemented it directly in the same session, task by task, TDD red-green-refactor: migration 009 (applied live against the dev Postgres container, verified via `psql`) → `assignments/models.py`'s `ContentCatalog` extension → `content/schemas.py`'s `AttachContentRequest` + `ContentResponse.source` extension → `content/service.py::attach_content` → `content/admin_content_router.py` + `main.py` mount → `adminContentApi.ts::attachContent` → `ManualContentEntryForm.tsx`'s Approve wiring
5. Confirmed RED (`ImportError`) before every backend implementation step; router-level tests were written immediately after the router/service pair already existed (the RED/GREEN discipline for the core logic was already satisfied at the schema/service layer) and passed 12/12 on first run; frontend RED (old hard-disabled-button assertions failing against the new interactive button) confirmed before implementing `handleApprove`
6. Full backend regression (603 passed, 2 skipped, same 3 pre-existing failures); full frontend regression (299/299); `tsc --noEmit` unchanged at 31 pre-existing errors; rebuilt and redeployed both Docker images; live-verified via `curl`: MANUAL + UDEMY happy paths (201), malformed-URL 422, nonexistent-skill 404, EMPLOYEE 403, plus a direct `psql` query confirming `origin`/`attached_by` landed correctly on both written rows
7. Noted honestly, rather than overclaiming: interactive real-browser verification of the Approve-click → Toast flow was not performed (no Playwright/browser-automation tool available this session) — covered instead by `ManualContentEntryForm.test.tsx`'s automated assertions of the same behavior

**Output File:** `_bmad-output/implementation-artifacts/6-8-review-approve-and-estimate-days-to-complete.md`
**Sprint Status:** `6-8-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` (created and implemented in the same pass)

---

### 3. **`/bmad-code-review` Skill**

**Purpose:** Adversarial review of the finished implementation against the story's own spec, structured triage, and patch application.

**When Invoked:** User request: "do the code review for story 6-8-review-approve-and-estimate-days-to-complete"
**Workflow Steps Executed:**

- **Step 01 (Gather Context):** Spec file resolved from the explicit story name in the user's request (Tier 1). `baseline_commit` (`a07c8690`) confirmed to match current `HEAD` exactly, so diff source = uncommitted changes. Combined `git diff HEAD` (tracked modifications) with `git diff --no-index /dev/null <path>` per untracked new file (migration 009, `admin_content_router.py`, `test_admin_content_router.py`) into one saved diff (~1,027 lines, 13 files), read directly and embedded in each review-agent prompt. Checkpoint presented and confirmed before launching review agents.
- **Step 02 (Review):** Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor as three parallel background subagents (`review_mode = "full"`, story file as spec). All three returned independently.
- **Step 03 (Triage):** Normalized 25 raw findings (11 Blind Hunter + 10 Edge Case Hunter + 4 Acceptance Auditor observations) down to 16 distinct findings after dedup. Read the actual code at every finding's location before rating severity — most consequentially, traced `ProgressRepository.get_video_duration`/`parse_duration_seconds` and every one of its callers (`assignments/service.py`, `dashboard/service.py`, `progress/router.py`, `progress/service.py`) to confirm the duration-metadata mismatch would genuinely stick every affected Assignment's dashboard Status at "In Progress, 0%" forever — and separately verified the "sprint-status.yaml placeholder ellipsis" claim was a false positive by directly checking the real file (2,152 characters of real text, not the truncated "..." this reviewer's own diff-construction had substituted when building the Blind Hunter prompt). Routed the result into 0 decision-needed, 3 patch, 4 defer, 9 dismiss.
- **Step 04 (Present and Act):** Findings written to the story file's new "Review Findings" subsection; 4 deferred items also logged to `deferred-work.md`. User chose "apply every patch."

**Patches Applied (all TDD — RED confirmed, then implemented, then GREEN):**
1. **The most serious finding:** `attach_content` wrote `content_metadata = {"duration_hours": duration_hours}`, but `ProgressRepository`'s dashboard-derivation read path expects `content_metadata.get("duration")` in seconds — a key AND unit mismatch. Fixed via a new `_build_attach_content_metadata` helper that additively stores both `duration_hours` (satisfies the epics AC's literal field name) and `duration` in whole seconds (satisfies the actual read contract this codebase's AD-3 single derivation authority relies on). 2 tests updated, 1 new.
2. **Same helper, second gap:** `source="YOUTUBE"` attaches had no `video_id`, so the batch ingestion job's de-dup check would silently re-ingest the same video as a duplicate row on its next run. Fixed via a new `_extract_youtube_video_id` helper — hostname-checked against `watch?v=`/`youtu.be/` URLs, not substring-matched, deliberately mirroring the exact lesson from Story 6.7's own review patch to `ContentPreviewModal.tsx`. 3 new tests (standard URL, short URL, unrecognized-URL graceful fallback) plus 1 new router-level test.
3. `ManualContentEntryForm.tsx`'s `handleReview` reset `candidate`/`approved`/`approveError` on a new review but not `toastMessage`, so a prior "✓ Content approved..." toast could linger visually into a new review cycle. Fixed with one added `setToastMessage(null)` in the same reset block. 1 new test.

**Output:** Story status → `done`; full regression re-verified — backend 606 passed (3 net new) / 2 skipped / same 3 pre-existing failures; frontend 300/300 (1 net new); `tsc --noEmit` unchanged at 31 pre-existing errors. Docker backend and frontend images rebuilt and redeployed a second time with the patches applied; a real `youtube.com/watch?v=` URL attached and confirmed via direct `psql` query to carry `duration_hours`, `duration` (seconds), and `video_id` together in `metadata`.

**Documentation Generated:**
- Code review findings + resolutions written directly into the story file's Review Findings subsection (3 patches, 4 deferrals, 9 dismissals each with a one-line reason)
- 4 deferred items appended to `deferred-work.md` under a new "Deferred from: code review of 6-8-..." heading
- Sprint status synced (`6-8-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`)

---

## Files Created/Updated

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/009_add_content_attach_metadata.py` | Adds `content_catalog.attached_by`/`origin`; extends `content_source_enum` with `'UDEMY'` |
| `backend/app/content/admin_content_router.py` | `POST /attach`, mounted at `/api/admin/content` — thin, delegates to `content/service.py::attach_content` |
| `backend/tests/test_admin_content_router.py` | 13 HTTP-level tests (12 initial + 1 code-review patch) |

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/assignments/models.py` | `ContentCatalog` gains `attached_by`, `origin`; `source` Enum tuple extended with `"UDEMY"` |
| `backend/app/content/schemas.py` | Adds `AttachContentRequest`; extends `ContentResponse.source`'s `Literal` to include `"UDEMY"` |
| `backend/app/content/service.py` | Adds `attach_content`; code-review patches add `_extract_youtube_video_id`, `_build_attach_content_metadata` |
| `backend/app/main.py` | Mounts the new `admin_content_router` at `/api/admin/content` |
| `backend/tests/test_content_schemas.py` | 14 new tests: valid sources ×3, optional duration, invalid source rejection, blank-title rejection, malformed-URL rejection ×5 parametrized, non-positive-duration rejection ×3 parametrized, unknown-field rejection; 1 existing test parametrized for `UDEMY` |
| `backend/tests/test_content_service.py` | 8 new tests (5 initial + 3 code-review patches): happy path per source, without-duration, nonexistent-skill 404, EMPLOYEE 403; YouTube `video_id` extraction ×3 (standard URL, short URL, unrecognized-URL fallback) |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/lib/api/adminContentApi.ts` | Adds `attachContent(body)` + `ContentResponse` type — thin typed POST client |
| `frontend/src/features/admin/ManualContentEntryForm.tsx` | Wires `[Approve]` to `attachContent`; adds optional `skillName` prop; Toast on success, inline retryable error on failure; code-review patch resets `toastMessage` on a new review |
| `frontend/src/tests/ManualContentEntryForm.test.tsx` | 1 obsolete test ("Approve is disabled") replaced with 3 new tests (Approve success + Toast, generic-fallback Toast, Approve failure); 1 new code-review-patch test (stale Toast cleared on new review) |

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/6-8-review-approve-and-estimate-days-to-complete.md` | Story file — ACs, Scope Notes, Dev Notes, Review Findings, Dev Agent Record |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `6-8-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | 4 deferred findings logged under a new heading |
| `documentation/ImplementationStepsForStory6-8.md` | This file |

### Not Changed (by design)

- The Skills Card Grid, Content Lookup Panel shell, New Skill Panel, Delete confirmation, API Keys panel integration — all Story 6.10's job
- Story 6.6's search-result cards' own `[Approve]` wiring — only the manual-entry card is wired here; a future Story 6.10 task wires the same `attachContent` call into the Search tab
- Story 6.9's `DELETE /api/admin/content/{content_id}/reject` — not built; this story's `origin: "ADMIN_LOOKUP"` write is the exact signal Story 6.9's dev agent will filter on
- Employee-facing Content Discovery's duration display — a known, documented, deliberately out-of-scope gap (see Deferred Items below)

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skills:** `/bmad-agent-dev` → `/bmad-create-story`
- Discovered no story file existed yet for `6-8-...` (`backlog`) — created it directly
- Read the architecture spine's Consistency Conventions table, which explicitly names `/api/admin/content/attach` as the route to build — no guessing required on the URL shape
- Resolved 12 real design decisions during story-writing, documented as 12 numbered Scope Notes, including the deliberate scope narrowing versus the epics' own Story 6.10-only UI assignment (per explicit user instruction) and the discovery that FR-19's days-to-complete estimate needed zero new work

### Phase 2: Implementation
**(direct, same session, TDD red-green-refactor per task, both backend and frontend)**
- Migration 009 applied and live-verified against the running dev Postgres container via `psql` before moving to the next task
- 35 new backend tests (schemas, service, router) + 3 new/replaced frontend tests
- RED confirmed (`ImportError` / failing old assertions against new interactive behavior) before every implementation step
- Full regression pass — backend 603 passed / 2 skipped / same 3 pre-existing failures; frontend 299/299; `tsc --noEmit` unchanged (31 pre-existing errors)
- Live end-to-end verification via `curl` against rebuilt Docker containers (MANUAL + UDEMY happy paths, 422, 404, 403) plus a direct `psql` confirmation of `origin`/`attached_by`
- Story marked `review`

### Phase 3: Code Review
**Skill:** `/bmad-code-review`
- 3 parallel adversarial layers, all background subagents, single pass
- **Findings:** 25 raw → 16 after dedup → 0 decision-needed, 3 patch, 4 defer, 9 dismiss
- **One review-subagent claim flipped to a confirmed false positive by reading the real file, not the diff excerpt sent to that subagent:** the "placeholder ellipsis" claim about `sprint-status.yaml`'s changelog — an artifact of this reviewer's own diff truncation, not the story's code
- **Most serious finding:** `attach_content` wrote duration data under a key/unit shape the dashboard's own Status/percent derivation (`ProgressRepository`, AD-3's single derivation authority) can't read — every Assignment on admin-attached Content would have been permanently stuck "In Progress" at 0%, silently defeating this story's own stated purpose
- **Second finding, same root cause:** YOUTUBE-sourced attaches had no `video_id`, which would have caused the batch ingestion job to silently duplicate the same video on its next run
- **Action:** user chose "apply every patch" — all 3 patches applied with 8 new/updated tests, re-verified live via `curl` against a rebuilt Docker container (a real `youtube.com/watch?v=` URL, confirmed via direct `psql` query)
- Output: 606 passed backend (up from 603 before review) / 300 passed frontend (up from 299); story marked `done`

---

## Test Coverage

### New/Extended Test Files (61 tests total from this story, post-review)

**Backend (46 new):**
- `test_content_schemas.py` — 14 new: valid sources ×3, optional duration, invalid-source rejection, blank-title rejection, malformed-URL rejection (5 parametrized cases), non-positive-duration rejection (3 parametrized cases), unknown-field rejection; 1 existing test parametrized for `UDEMY`
- `test_content_service.py` — 8 new: happy path per source with/without duration, nonexistent-skill 404, EMPLOYEE 403, YouTube `video_id` extraction (standard URL, short URL, unrecognized-URL fallback)
- `test_admin_content_router.py` — 13 new: happy path per source ×3, duration-omitted-omits-metadata, EMPLOYEE 403, unauthenticated 401, nonexistent-skill 404, malformed-URL 422, blank-title 422, invalid-source 422, non-positive-duration 422, unknown-field 422, YouTube-URL-includes-video_id (code-review patch)

**Frontend (4 new/updated):**
- `ManualContentEntryForm.test.tsx` — 1 obsolete test replaced (Approve was hard-disabled), 3 new (Approve success + Toast with `skillName`, generic-fallback Toast, Approve failure + retryable), 1 new code-review-patch test (stale Toast cleared on new review)

### Regression Verification
- Full backend suite run after implementation (603 passed) and again after the code review's patches (606 passed) — same 3 pre-existing, unrelated failures at every stage (`test_find_existing_assignment_returns_empty_when_no_match`, `test_assignment_with_no_qualifying_content_has_null_content`, `test_content_match_returns_null_when_no_content_matches_the_skill`, documented since Story 6.4)
- Full frontend suite run after implementation (299 passed) and again after patches (300 passed), zero failures at either stage
- `tsc --noEmit` explicitly checked before and after every change set — 31 pre-existing errors, unchanged by this story's changes at every stage
- Live-verified end-to-end via `curl` against a rebuilt/redeployed Docker backend container, both before and after the review's patches — MANUAL + UDEMY happy paths (201), malformed-URL 422, nonexistent-skill 404, EMPLOYEE 403, and (post-patch) direct `psql` confirmation of the full `metadata` shape on a real attached YouTube video
- Interactive real-browser verification of the Approve-click → Toast flow was not performed — honestly noted as not performed (no Playwright/browser-automation tool available this session) rather than overclaimed, covered instead by `ManualContentEntryForm.test.tsx`'s automated assertions

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AD-1: single-owner module, cross-module calls via Service API only** | The new route lives in its own `content/admin_content_router.py` file (own prefix, per the Consistency Conventions table) but delegates all logic to `content/service.py::attach_content`, reusing `skills_service.get_skill_by_id` for its 404 check | `content/admin_content_router.py`, `content/service.py` |
| **AD-6: HR_ADMIN-only via service-layer gate** | `attach_content` calls `require_hr_admin(current_user)` first, before the 404 check — same ordering as `submit_manual_content`/`search_content_for_skill` | `content/service.py` |
| **AD-3: `progress/` is the single derivation authority for readiness** | The review's headline patch exists specifically to satisfy this: `content_metadata.duration` (seconds) is the exact shape `ProgressRepository.parse_duration_seconds` requires, added alongside the epics-literal `duration_hours` rather than instead of it | `content/service.py` |
| **FR-18: attached link visible to Employees the same way as batch-matched Content** | `attach_content` writes to the same `content_catalog` table via the same `repository.create_content` function every other ingestion path uses — no separate table or shape | `content/service.py`, `content/repository.py` |
| **FR-18: each attached Content item records which HR Admin attached it and when** | `attached_by`/`ingested_at` columns, set from `current_user.user_id` and the table's existing `server_default=func.now()` | `assignments/models.py`, migration 009 |
| **FR-19: days-to-complete, client-side, never persisted** | Unchanged from Story 6.7 — `estimateDaysToComplete` lives entirely on the frontend; the backend only ever stores `duration_hours`/`duration` | `frontend/src/lib/utils/duration.ts` (untouched by this story) |

---

## Key Technical Achievements

✅ **Deliberately narrowed scope versus the epics' own assignment, with the reasoning written down, not silently** — the epics text puts all UI wiring in Story 6.10; this story's Scope Note 1 documents exactly why the manual-entry Approve path was pulled forward instead (explicit user instruction), while the rest of Story 6.10's surface stays untouched and named
✅ **Reused an existing composition instead of inventing a new one** — `attach_content` mirrors `submit_manual_content`'s exact `require_hr_admin` → 404-check → build/write shape; `repository.create_content`'s existing arbitrary-dict acceptance needed zero changes
✅ **Code review caught a genuinely severe, easy-to-miss bug through independent confirmation** — both Blind Hunter and Edge Case Hunter independently raised the `content_metadata` key/unit mismatch, and tracing the actual read path (`ProgressRepository` → its four real callers) confirmed the consequence was not cosmetic but a permanent dashboard-Status break for every affected Assignment
✅ **A review-subagent finding was caught as a false positive by checking the real file instead of trusting the claim** — the "placeholder ellipsis" finding was traced to this reviewer's own diff-truncation when building the Blind Hunter prompt, verified wrong by reading the actual 2,152-character line
✅ **Fixed the core bug without violating the literal spec text** — rather than treating "store `duration_hours`" (epics AC) and "the dashboard needs `duration` in seconds" (real system contract) as a forced tradeoff, the fix stores both additively, satisfying both
✅ **Honest gap disclosure instead of a false completeness claim** — explicitly recorded that the Approve-click → Toast flow was verified via automated component tests, not an interactive browser session, and flagged (in the story's own Dev Notes, before review even started) that Employee-facing Content Discovery still can't display a days-to-complete estimate for admin-attached content, since that display path reads a different metadata key than this story's literal AC specifies
✅ **Zero regressions across both full-suite runs, on both stacks, at every stage** — backend 603 → 606 passed, frontend 299 → 300 passed, `tsc --noEmit` unchanged at 31 pre-existing errors throughout

---

## Deferred Items (Not Story 6-8 Scope)

Logged in `_bmad-output/implementation-artifacts/deferred-work.md` under "Deferred from: code review of 6-8-review-approve-and-estimate-days-to-complete (2026-09-10)":

1. **No duplicate-attach protection** — no unique constraint or idempotency check on `attach_content`; consistent with FR-18's own explicit "more than one item may be approved for a Skill" tolerance, and the client-side `approving`/`approved` state already covers the common double-click case (same precedent as Story 6.7's Review-link button).
2. **Title length mismatch** — `AttachContentRequest.title` caps at 255 chars but the upstream candidate schemas don't, so an unusually long title fails Approve with a generic 422. Pre-existing column-width characteristic, low probability.
3. **No `thumbnail_url` carried into `content_metadata`** — a YouTube/Udemy candidate's thumbnail is lost once approved. `AssignmentCard.tsx` already degrades gracefully (conditional render), so this is visual polish, not breakage.
4. **No test round-trips a written row through `content_service.get_content`/`list_content_for_skill`** — existing tests fetch via `repository.get_content_by_id` directly. Test-coverage enhancement suggestion, not a defect.

Also flagged directly in the story file's own Dev Notes (not a review finding — a scope decision made during story creation, confirmed still accurate after the review's fix): **admin-attached `content_metadata.duration_hours`/`duration` still won't surface a days-to-complete estimate on the Employee-facing Content Discovery page**, because that page's display logic reads a metadata shape from the batch-ingestion path that this story's literal epics AC text doesn't reconcile. Left for a future story, not silently expanded into this one's scope.

---

## Conclusion

Story 6-8 is **✅ DONE** after a story-creation-then-implement cycle (API + a narrow frontend slice pulled forward from Story 6.10, per explicit user instruction) followed by one full adversarial code review pass:

- All acceptance criteria satisfied, confirmed independently by a clean Acceptance Auditor pass that also verified every cited precedent claim against the live code
- A deliberate, documented scope narrowing versus the epics' own Story 6.10-only UI assignment
- 3 patches applied from this story's own code review, the most serious closing a real, severe dashboard-completion-tracking break for every Assignment on admin-attached Content — caught by two independent review layers and fixed without violating the literal spec text
- One review-subagent claim correctly identified and dismissed as a false positive after reading the real file, not the diff excerpt sent to that subagent
- Zero regressions across every full-suite run, on both the backend and frontend stacks
- 4 items deferred with clear "how to apply" notes, none blocking
- Live-verified via `curl` against rebuilt Docker containers, both before and after the review's patches, including a direct `psql` confirmation of the fixed metadata shape
- One honestly-disclosed verification gap (interactive browser check of the Approve → Toast flow) rather than an overclaimed "done"
- Not yet committed to git in this session

**Ready for:** Story 6.9 (Reject the Currently Approved Content Link, FR-23) or Story 6.10 (Skills Tab Frontend — Card Grid, Content Lookup, API Keys, Watch Modal), both still `backlog` in Epic 6.
